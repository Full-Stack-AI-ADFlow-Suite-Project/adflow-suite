"""Scrittura JSONL sincronizzata tra processi per i log di valutazione."""

import logging
import hashlib
import os
from pathlib import Path


def id_test_redatto(test_id: str | None) -> str | None:
    """Mantiene la correlazione senza scrivere valori dei casi parametrizzati."""
    if not test_id:
        return None
    test_id = test_id.split(" (", 1)[0]
    nome, separatore, parametri = test_id.partition("[")
    if not separatore:
        return nome
    impronta = hashlib.sha256(parametri.encode("utf-8")).hexdigest()[:10]
    return f"{nome}[case:{impronta}]"


def scrivi_jsonl(percorso: Path, messaggio: str) -> None:
    """Aggiunge una riga completa anche quando più processi condividono il log."""
    percorso.parent.mkdir(parents=True, exist_ok=True)
    lock_path = Path(f"{percorso}.lock")
    with lock_path.open("a+b") as lock_file:
        lock_file.seek(0, os.SEEK_END)
        if lock_file.tell() == 0:
            lock_file.write(b"\0")
            lock_file.flush()
        lock_file.seek(0)
        _blocca(lock_file)
        try:
            contenuto = (messaggio.rstrip("\r\n") + "\n").encode("utf-8")
            with percorso.open("ab", buffering=0) as output:
                restante = memoryview(contenuto)
                while restante:
                    scritti = output.write(restante)
                    restante = restante[scritti:]
        finally:
            _sblocca(lock_file)


def _blocca(file) -> None:
    if os.name == "nt":
        import msvcrt

        msvcrt.locking(file.fileno(), msvcrt.LK_LOCK, 1)
    else:
        import fcntl

        fcntl.flock(file.fileno(), fcntl.LOCK_EX)


def _sblocca(file) -> None:
    if os.name == "nt":
        import msvcrt

        file.seek(0)
        msvcrt.locking(file.fileno(), msvcrt.LK_UNLCK, 1)
    else:
        import fcntl

        fcntl.flock(file.fileno(), fcntl.LOCK_UN)


class JSONLFileHandler(logging.Handler):
    """Handler logging con una scrittura completa protetta da lock tra processi."""

    def __init__(self, percorso: Path):
        super().__init__()
        self.percorso = percorso

    def emit(self, record: logging.LogRecord) -> None:
        try:
            scrivi_jsonl(self.percorso, self.format(record))
        except Exception:
            self.handleError(record)
