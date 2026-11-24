"""Support Inbox Triage Desk — Router -> Especialista -> Supervisor.

Funciona em Linux, macOS e Windows. A chave da API NUNCA vai no código:

    Linux / macOS (bash, zsh):   export GEMINI_API_KEY="api_key"
    Windows (PowerShell):        $env:GEMINI_API_KEY = "api_key"

Uso:
    python3 triage.py                       # corre as 24 mensagens e mede a accuracy do router
    python3 triage.py --one "texto" --email ana.silva@example.pt

Variáveis opcionais:
    MODEL      = nome do modelo Gemini (por defeito gemini-3.5-flash-lite)
    SUPERVISOR = v2 (por defeito) ou v1, para reproduzir as duas configurações do relatório
"""
import argparse
import csv
import hashlib
import json
import os
import sys
import time
from pathlib import Path

from data import CUSTOMERS, FAQ, MESSAGES

# Todos os ficheiros gerados ficam ao lado do script, seja qual for a pasta de onde se corre.
BASE = Path(__file__).resolve().parent


def _load_dotenv(path: Path) -> None:
    """Lê um .env simples (CHAVE=valor). As variáveis já definidas no terminal têm prioridade."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_load_dotenv(BASE / ".env")

try:  # acentos corretos no terminal do Windows
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

MODEL = os.environ.get("MODEL", "gemini-3.5-flash-lite")
CACHE_DIR = BASE / "cache"
LOG_FILE = BASE / "logs" / "messages.jsonl"
RESULTS_FILE = BASE / "results.csv"
CACHE_DIR.mkdir(exist_ok=True)
LOG_FILE.parent.mkdir(exist_ok=True)


# ----------------------------------------------------------------- LLM + log
def _gemini(system: str, user: str) -> str:
    import requests
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        sys.exit("Falta a variável GEMINI_API_KEY (ver instruções no topo de triage.py ou README.md).")
    body = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": user}]}],
        "generationConfig": {"maxOutputTokens": 2048, "responseMimeType": "application/json"},
    }
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
    headers = {"x-goog-api-key": key}
    for attempt in range(8):
        r = requests.post(url, json=body, headers=headers, timeout=60)
        if r.status_code in (429, 500, 502, 503, 504):  # limite da quota ou servidor sobrecarregado
            wait = 15 * (attempt + 1)
            print(f"  [Gemini {r.status_code}] temporário, a esperar {wait}s...", file=sys.stderr)
            time.sleep(wait)
            continue
        if not r.ok:
            raise RuntimeError(f"Gemini {r.status_code}: {r.text[:300]}")
        break
    else:
        raise RuntimeError("Gemini: erro temporário persistente (429/503). Volta a correr daqui a uns "
                           "minutos: a cache guarda o progresso.")
    try:
        return r.json()["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        return ""  # resposta bloqueada ou vazia: o resto do pipeline trata como falha


def call_llm(agent: str, system: str, user: str) -> str:
    """Chama o Gemini com cache em disco e regista a mensagem no log."""
    key = hashlib.sha256(f"gemini|{MODEL}|{system}|{user}".encode()).hexdigest()
    cache_file = CACHE_DIR / f"{key}.txt"
    cached = cache_file.exists()
    if cached:
        out = cache_file.read_text(encoding="utf-8")
    else:
        out = _gemini(system, user)
        if out:  # nunca guardar respostas vazias na cache
            cache_file.write_text(out, encoding="utf-8")
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"t": time.strftime("%H:%M:%S"), "agent": agent,
                            "cached": cached, "input": user, "output": out},
                           ensure_ascii=False) + "\n")
    return out


def parse_json(text: str):
    """Extrai o primeiro objeto JSON do texto; devolve None se falhar."""
    try:
        return json.loads(text[text.index("{"): text.rindex("}") + 1])
    except (ValueError, json.JSONDecodeError):
        return None


# -------------------------------------------------------------------- Agentes
ROUTER_SYS = """You are the ROUTER of a customer support desk. Your ONLY job is to decide who handles a message.
Output ONLY a JSON object: {"label": "billing" | "technical" | "complaint", "urgency": 1|2|3, "reason": "<max 15 words>"}
- billing: charges, invoices, prices, payments.
- technical: the product does not work or the customer asks how to do something.
- complaint: the main point is dissatisfaction, anger, bad treatment, or a threat to leave/report.
When a message mixes topics, choose the customer's MAIN request.
Urgency: 1 = routine, 2 = needs attention soon, 3 = angry, legal threat, money at risk or business stopped.
You are FORBIDDEN from writing any reply to the customer. No text outside the JSON."""

BILLING_SYS = """You are the BILLING SPECIALIST. You draft a reply to the customer in European Portuguese.
You receive the customer's message and their account record (the ONLY source of truth).
Rules: cite real numbers (invoice ids, dates, amounts) from the record. If the record does not show
what the customer claims, say so honestly. Never invent invoices or amounts. Do not promise refunds;
say the case will be reviewed. Output ONLY JSON: {"reply": "<draft>", "covered": true|false}
Use covered=false if the record does not allow you to answer."""

TECH_SYS = """You are the TECHNICAL SPECIALIST. You draft a step-by-step reply in European Portuguese.
Your ONLY source is the FAQ provided. Never invent steps that are not in the FAQ.
If the problem is not covered by the FAQ, say so explicitly in the reply and set covered=false.
Output ONLY JSON: {"reply": "<draft>", "covered": true|false}"""

COMPLAINT_SYS = """You are the COMPLAINT HANDLER. You draft an empathetic apology and a proposed remedy
in European Portuguese. Rules: NEVER admit legal fault or liability ("the error was ours", "we violated...").
NEVER promise a refund amount or a compensation value. Propose a next step (a call, a review by a
senior colleague, a deadline to reply). Output ONLY JSON: {"reply": "<draft>", "covered": true}"""

# Supervisor v1: versão inicial (gerou results/results_v1.csv).
SUPERVISOR_V1 = """You are the SUPERVISOR. You read the customer's original message and a draft reply and decide
send or escalate to a human. Escalate if: the specialist flagged "not covered"; urgency is 3; the draft
promises a refund amount, admits legal fault, invents facts, or does not answer what the customer asked.
Otherwise send. Output ONLY JSON: {"decision": "send" | "escalate", "reason": "<max 20 words>"}"""

# Supervisor v2: acrescenta as duas últimas regras (mensagens com dois problemas e rascunhos
# que só encaminham o caso). Gerou results/results_v2.csv.
SUPERVISOR_V2 = """You are the SUPERVISOR. You read the customer's original message and a draft reply and decide
send or escalate to a human. Escalate if: the specialist flagged "not covered"; urgency is 3; the draft
promises a refund amount, admits legal fault, invents facts, or does not answer what the customer asked;
the customer's message has two distinct problems and the draft does not resolve both;
the draft's only answer is to forward the case to another team.
Otherwise send. Output ONLY JSON: {"decision": "send" | "escalate", "reason": "<max 20 words>"}"""

SUPERVISOR_SYS = SUPERVISOR_V1 if os.environ.get("SUPERVISOR", "v2").lower() == "v1" else SUPERVISOR_V2


def router(text: str) -> dict:
    out = call_llm("router", ROUTER_SYS, f"Customer message:\n{text}")
    data = parse_json(out)
    if not data or data.get("label") not in ("billing", "technical", "complaint"):
        return {"label": "unknown", "urgency": 3, "reason": "router output invalid"}
    try:
        data["urgency"] = int(data.get("urgency", 2))
    except (TypeError, ValueError):
        data["urgency"] = 3  # na dúvida, urgência máxima: o caso vai para um humano
    return data


def billing_specialist(text: str, email: str) -> dict:
    account = CUSTOMERS.get(email)  # "ferramenta": consulta à base de dados fictícia
    record = json.dumps(account, ensure_ascii=False, indent=1) if account else "NO ACCOUNT FOUND"
    out = call_llm("billing", BILLING_SYS, f"Message:\n{text}\n\nAccount record:\n{record}")
    return parse_json(out) or {"reply": out, "covered": False}


def technical_specialist(text: str, email: str) -> dict:
    out = call_llm("technical", TECH_SYS, f"Message:\n{text}\n\n{FAQ}")
    return parse_json(out) or {"reply": out, "covered": False}


def complaint_handler(text: str, email: str) -> dict:
    out = call_llm("complaint", COMPLAINT_SYS, f"Message:\n{text}")
    return parse_json(out) or {"reply": out, "covered": False}


SPECIALISTS = {"billing": billing_specialist, "technical": technical_specialist,
               "complaint": complaint_handler}


def supervisor(text: str, route: dict, draft: dict) -> dict:
    user = (f"Original message:\n{text}\n\nUrgency: {route['urgency']}\n"
            f"Specialist covered: {draft.get('covered')}\nDraft reply:\n{draft.get('reply')}")
    data = parse_json(call_llm("supervisor", SUPERVISOR_SYS, user)) or {
        "decision": "escalate", "reason": "supervisor output invalid"}
    if data.get("decision") not in ("send", "escalate"):
        data["decision"] = "escalate"  # resposta inesperada: não enviar sem humano
    # Regras duras em Python: o modelo nunca consegue "deixar passar" estes casos.
    if route["urgency"] >= 3 or draft.get("covered") is False:
        data["decision"] = "escalate"
        data["reason"] = "hard rule: urgency 3 or not covered | " + str(data.get("reason", ""))
    return data


def process(text: str, email: str) -> dict:
    route = router(text)
    if route["label"] == "unknown":
        return {"route": route, "draft": {"reply": "", "covered": False},
                "verdict": {"decision": "escalate", "reason": route["reason"]}}
    draft = SPECIALISTS[route["label"]](text, email)
    verdict = supervisor(text, route, draft)
    return {"route": route, "draft": draft, "verdict": verdict}


# ------------------------------------------------------------------- Avaliação
def evaluate():
    rows, ok, ok_amb, n_amb, ok_urg, ok_clear, n_clear = [], 0, 0, 0, 0, 0, 0
    for mid, email, text, exp_label, exp_urg, amb in MESSAGES:
        res = process(text, email)
        got = res["route"]["label"]
        hit = got == exp_label
        ok += hit
        ok_urg += res["route"]["urgency"] == exp_urg
        if amb:
            n_amb += 1
            ok_amb += hit
        else:
            n_clear += 1
            ok_clear += hit
        rows.append({"id": mid, "ambiguous": amb, "expected": exp_label, "got": got,
                     "urgency_exp": exp_urg, "urgency_got": res["route"]["urgency"],
                     "decision": res["verdict"]["decision"],
                     "reason": res["verdict"]["reason"],
                     "draft": res["draft"].get("reply", "")})
        flag = "OK " if hit else "ERR"
        print(f"[{flag}] #{mid:02d} {'(amb) ' if amb else '      '}"
              f"esperado={exp_label:<9} obtido={got:<9} "
              f"urg {exp_urg}->{res['route']['urgency']}  => {res['verdict']['decision']}")
    with open(RESULTS_FILE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    n = len(MESSAGES)
    print(f"\nAccuracy do router:      {ok}/{n} = {ok / n:.0%}")
    print(f"  mensagens claras:      {ok_clear}/{n_clear}")
    print(f"  mensagens ambíguas:    {ok_amb}/{n_amb}")
    print(f"Urgência exata:          {ok_urg}/{n}")
    sent = sum(r["decision"] == "send" for r in rows)
    print(f"Enviadas / escaladas:    {sent} / {n - sent}")
    print(f"Detalhe em {RESULTS_FILE.name}; mensagens entre agentes em logs/{LOG_FILE.name}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--one", help="processar uma só mensagem")
    ap.add_argument("--email", default="ana.silva@example.pt")
    args = ap.parse_args()
    try:
        if args.one:
            print(json.dumps(process(args.one, args.email), ensure_ascii=False, indent=2))
        else:
            evaluate()
    except RuntimeError as e:
        sys.exit(f"Erro: {e}")