"""Difetti trovati dalla linea di base della simulazione di accettazione (T4-101).

Ogni test di questo file descrive un difetto reale trovato dalla corsia 10
(ADR-120): finché il difetto resta, il test fallisce e `xfail(strict=True)`
lo dichiara previsto, così la suite resta verde e il difetto resta documentato;
il giorno in cui qualcuno corregge il difetto, il test passa e pytest lo
segnala come XPASS strict, obbligando a togliere il marcatore e il rilievo
nel registro (`docs/accettazione/rilievi.md`).
"""

import subprocess
import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[2]


@pytest.mark.skipif(
    not (BACKEND / ".env").exists(),
    reason="serve backend/.env: in locale c'è sempre (lo crea allinea.py), in CI no",
)
@pytest.mark.xfail(
    strict=True,
    reason="RL-009: litellm, appena importato, chiama load_dotenv() e riversa "
    "backend/.env in os.environ: tutte le variabili del file, segreti compresi, "
    "finiscono nell'ambiente del processo",
)
def test_importare_litellm_non_esporta_il_file_env_nell_ambiente() -> None:
    """Riproroduzione del difetto visto in T4-101.

    Sotto `pytest --cov` la suite perdeva `test_instagram_meta_in_produzione_
    richiede_url_foto_https` (tests/test_sast_security.py): l'import di litellm
    esportava `FOTO_URL_PUBBLICO` di backend/.env nell'ambiente e il validatore
    di produzione, che doveva rifiutare l'assenza dell'URL HTTPS, lo trovava
    invece valido. Il difetto è la esportazione stessa: qui la si riproduce in
    un processo separato avviato senza `__main__.__file__` (come `python -c`),
    il caso in cui python-dotenv risolve il .env dalla directory di lavoro.
    """
    esito = subprocess.run(
        [
            sys.executable,
            "-c",
            "import os, litellm; print('FOTO_URL_PUBBLICO' in os.environ)",
        ],
        cwd=BACKEND,
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert esito.returncode == 0, esito.stderr
    riga_finale = esito.stdout.strip().splitlines()[-1] if esito.stdout.strip() else ""
    assert riga_finale == "False", (
        "litellm ha esportato backend/.env nell'ambiente del processo "
        f"(stdout: {riga_finale!r})"
    )
