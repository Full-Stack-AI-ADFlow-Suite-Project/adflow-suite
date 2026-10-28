"""Integrità dei log JSONL con writer in processi indipendenti."""

from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import subprocess
import sys


def _scrivi_da_processo(percorso: Path, processo: int) -> None:
    codice = """
import json, sys
from pathlib import Path
from app.core.log_jsonl import scrivi_jsonl
path = Path(sys.argv[1])
processo = int(sys.argv[2])
for numero in range(40):
    scrivi_jsonl(path, json.dumps({"processo": processo, "numero": numero}))
"""
    subprocess.run(
        [sys.executable, "-c", codice, str(percorso), str(processo)],
        check=True,
        env=os.environ.copy(),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def test_jsonl_rimane_integro_con_scritture_concorrenti(
    tmp_path: Path,
) -> None:
    percorso = tmp_path / "eventi.jsonl"
    processi = 4
    righe_per_processo = 40

    with ThreadPoolExecutor(max_workers=processi) as pool:
        list(
            pool.map(
                lambda numero: _scrivi_da_processo(percorso, numero),
                range(processi),
            )
        )

    righe = [
        json.loads(riga)
        for riga in percorso.read_text(encoding="utf-8").splitlines()
        if riga
    ]

    assert len(righe) == processi * righe_per_processo
    assert len({(riga["processo"], riga["numero"]) for riga in righe}) == len(righe)
