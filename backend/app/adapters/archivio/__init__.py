"""Modulo dell'adattatore archivio per la gestione delle foto (Corsia 2)."""

from typing import Optional
from .base import ArchivioAdapter
from .disco import ArchivioDisco
from .finto import ArchivioFinto

_istanza_archivio: Optional[ArchivioAdapter] = None


def ottieni_archivio() -> ArchivioAdapter:
    """Restituisce l'adattatore archivio attualmente configurato.

    Di default restituisce un'istanza di ArchivioDisco.
    Nei test o durante lo sviluppo può essere sostituito tramite `imposta_archivio()`.
    """
    global _istanza_archivio
    if _istanza_archivio is None:
        _istanza_archivio = ArchivioDisco()
    return _istanza_archivio


def imposta_archivio(adattatore: Optional[ArchivioAdapter]) -> None:
    """Imposta o resetta l'adattatore archivio globale (per test e override di configurazione)."""
    global _istanza_archivio
    _istanza_archivio = adattatore


__all__ = [
    "ArchivioAdapter",
    "ArchivioDisco",
    "ArchivioFinto",
    "ottieni_archivio",
    "imposta_archivio",
]
