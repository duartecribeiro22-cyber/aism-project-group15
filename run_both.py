"""Corre o Supervisor v1 e o v2 em sequência e guarda results/results_v1.csv e results/results_v2.csv.

Uso (Linux/macOS):  python3 run_both.py
Uso (Windows):      python run_both.py
Requer GEMINI_API_KEY definida (ou no ficheiro .env). Para repetir as chamadas do zero,
apaga antes a pasta cache/.
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
(BASE / "results").mkdir(exist_ok=True)

for version in ("v1", "v2"):
    print(f"\n===== Supervisor {version} =====", flush=True)
    env = dict(os.environ, SUPERVISOR=version)
    r = subprocess.run([sys.executable, str(BASE / "triage.py")], cwd=BASE, env=env)
    if r.returncode != 0:
        sys.exit(f"triage.py falhou no {version} (código {r.returncode}). Vê a mensagem acima.")
    shutil.copy(BASE / "results.csv", BASE / "results" / f"results_{version}.csv")
    print(f"Guardado em results/results_{version}.csv")
