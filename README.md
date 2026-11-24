# Support Inbox Triage Desk (Projeto 4)

Sistema multi-agente: **Router → Especialista (Billing / Technical / Complaint) → Supervisor**.
Cada mensagem termina com uma etiqueta, um rascunho e uma decisão `send` ou `escalate`.
Usa a API do Google Gemini.

## Tema 4, desenvolvido por:
- Amilcio Monteiro - 240000005
- Duarte Ribeiro - 240000715
- João Neto - 230001032

## Arquitetura

| Agente | O que sabe / faz | Restrição |
|---|---|---|
| **Router** | Lê a mensagem e devolve `label` (billing, technical, complaint) e urgência 1 a 3 | Proibido de escrever respostas |
| **Billing** | Recebe o registo do cliente (faturas, valores, datas) e cita números reais | Não promete reembolsos; se o registo não confirma o pedido, diz-o |
| **Technical** | Só vê a FAQ de suporte | Não inventa passos; se não está na FAQ, marca `covered=false` |
| **Complaint** | Redige um pedido de desculpa e propõe um próximo passo | Nunca admite culpa legal nem promete valores |
| **Supervisor** | Lê a mensagem original e o rascunho e decide `send` ou `escalate` | Regras duras em Python: urgência 3 ou `covered=false` escalam sempre |

Só um especialista corre por mensagem. A decisão do Router escolhe qual.

## Requisitos
- Python 3.9 ou superior
- Uma chave gratuita da API do Gemini: https://aistudio.google.com/apikey

## Instalação e execução

### Linux e macOS (bash/zsh)
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export GEMINI_API_KEY="api_key"
python3 triage.py
```
Notas: no Ubuntu/Debian pode ser preciso `sudo apt install python3-venv`. O ambiente virtual
(`.venv`) evita o erro "externally-managed-environment" ao instalar pacotes.

### Windows (PowerShell)
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt

$env:GEMINI_API_KEY = "api_key"
python triage.py
```

### Alternativa em qualquer sistema: ficheiro `.env`
Cria um ficheiro `.env` na pasta do projeto com uma linha:
```
GEMINI_API_KEY=a_tua_chave
```
O script lê-o sozinho. As variáveis definidas no terminal têm prioridade sobre o `.env`.
**Não incluas o `.env` na entrega.** A chave nunca é escrita no código.

## Comandos úteis
```bash
python3 triage.py                                   # as 24 mensagens + accuracy (Supervisor v2)
SUPERVISOR=v1 python3 triage.py                     # mesma avaliação com o Supervisor v1
python3 triage.py --one "A app fecha sozinha" --email bruno.costa@example.pt
```
No PowerShell, o equivalente a `SUPERVISOR=v1` é `$env:SUPERVISOR = "v1"` antes de correr.

## Saída esperada
Uma linha por mensagem (etiqueta esperada e obtida, urgência e decisão final) e um resumo no fim.
Com o Supervisor v2, a corrida que fizemos terminou assim (excerto):

```
[OK ] #01       esperado=billing   obtido=billing   urg 2->2  => escalate
[OK ] #04       esperado=billing   obtido=billing   urg 1->1  => send
[OK ] #08       esperado=technical obtido=technical urg 3->3  => escalate
[ERR] #11 (amb) esperado=technical obtido=billing   urg 2->2  => escalate
...
Accuracy do router:      23/24 = 96%
  mensagens claras:      19/19
  mensagens ambíguas:    4/5
Urgência exata:          19/24
Enviadas / escaladas:    11 / 13
Detalhe em results.csv; mensagens entre agentes em logs/messages.jsonl
```
Como o modelo não é determinístico, uma corrida sem cache pode dar números ligeiramente diferentes.

## Variáveis opcionais
| Variável | Valor por defeito | Para quê |
|---|---|---|
| `MODEL` | `gemini-3.5-flash-lite` | Os modelos Gemini mudam; se der erro 404, vê o nome atual no AI Studio e define `MODEL` |
| `SUPERVISOR` | `v2` | `v1` para correr com o prompt inicial do Supervisor (sem as duas regras extra) |

## Estrutura do repositório
```
.
├── triage.py          # agentes, pipeline (process) e avaliação (evaluate)
├── data.py            # clientes fictícios, FAQ e as 24 mensagens com etiqueta/urgência esperadas
├── requirements.txt   # dependências (apenas requests)
├── README.md
├── .gitignore         # exclui .env, .venv/, cache/, logs/ e results.csv
└── results/
    ├── results_v1.csv # resultados com o Supervisor v1 (16 enviadas / 8 escaladas)
    └── results_v2.csv # resultados com o Supervisor v2 (11 enviadas / 13 escaladas)
```
Os dados são todos fictícios e foram criados por nós; estão em `data.py`.

## Ficheiros gerados (ao lado do script)
- `logs/messages.jsonl`: todas as mensagens passadas entre agentes (hand-off). Acumula todas as
  corridas; apaga a pasta `logs/` para um log limpo.
- `results.csv`: resultado por mensagem (etiqueta, urgência, decisão, rascunho).
- `cache/`: respostas guardadas; voltar a correr não gasta quota. Apaga a pasta para repetir
  as chamadas do zero.

## Avaliação
As 24 mensagens foram escritas e etiquetadas por nós, incluindo 5 ambíguas de propósito.
A amostra é pequena, por isso os números são indicativos.

| | Supervisor v1 | Supervisor v2 |
|---|---|---|
| Router: etiqueta correta | 23/24 (96%) | 23/24 (96%) |
| Mensagens claras / ambíguas | 19/19 · 4/5 | 19/19 · 4/5 |
| Urgência exata | 19/24 | 19/24 |
| Enviadas / escaladas | 16 / 8 | 11 / 13 |

As respostas do Router são iguais nas duas corridas porque vêm da cache, por isso não provam
consistência do modelo.

## Falhas conhecidas
1. **Mensagens com dois problemas (#11, #24).** O Router só dá uma etiqueta, e o especialista
   responde a metade. O Supervisor v1 deixava passar rascunhos que só prometiam "encaminhar
   para a equipa técnica", algo que o sistema não faz.
2. **Correção do Supervisor v2.** Acrescentámos duas regras ("dois problemas não resolvidos" e
   "só encaminha"). Apanhou o #11, mas o #24 continua a escapar, e criou falsos positivos
   (#2 e #21, em que o Supervisor viu um segundo problema que não existia). A precisão das
   escalações baixou.
3. **Inflação de urgência (#6, #9, #18).** Tom zangado leva o Router a dar urgência 3, e a regra
   dura escala mesmo com o rascunho correto.
4. **Fora da cobertura (#8 webhook, #17 SSO).** Comportamento correto: o Technical diz que não
   está na FAQ, não inventa passos, e o caso é escalado.

## Problemas comuns
- **429 / RESOURCE_EXHAUSTED**: limite do plano gratuito. O script espera e tenta de novo; se
  for o limite diário, volta a correr mais tarde (a cache guarda o progresso).
- **404 no modelo**: o modelo foi renomeado ou desligado; muda `MODEL`.
- **Falta a GEMINI_API_KEY**: define a variável no mesmo terminal onde corres o script.
- **400 / chave inválida**: confirma que a chave é a real e não o texto de exemplo.