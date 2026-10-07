"""Modulo dell'adattatore archivio per la gestione delle foto (Corsia 2)."""

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Optional

from .base import (
    DIMENSIONE_MAX_BYTE,
    ESTENSIONI_AMMESSE,
    ArchivioAdapter,
)
from .disco import ArchivioDisco
from .finto import ArchivioFinto

_istanza_archivio: Optional[ArchivioAdapter] = None


def ottieni_archivio() -> ArchivioAdapter:
    """Restituisce l'adattatore archivio attualmente configurato.

    Di default restituisce un'istanza di ArchivioDisco.
    Nei test o durante lo sviluppo può essere sostituito tramite `usa_archivio()`
    o `imposta_archivio()`.
    """
    global _istanza_archivio
    if _istanza_archivio is None:
        _istanza_archivio = ArchivioDisco()
    return _istanza_archivio


def imposta_archivio(adattatore: Optional[ArchivioAdapter]) -> None:
    """Imposta o resetta l'adattatore archivio globale."""
    global _istanza_archivio
    _istanza_archivio = adattatore


@contextmanager
def usa_archivio(adattatore: ArchivioAdapter) -> Iterator[ArchivioAdapter]:
    """Context manager per impostare temporaneamente un adattatore con ripristino garantito.

    Previene test non deterministici (flaky) ripristinando sempre l'adattatore
    precedente al termine del blocco with, anche in caso di eccezione.
    """
    global _istanza_archivio
    precedente = _istanza_archivio
    _istanza_archivio = adattatore
    try:
        yield adattatore
    finally:
        _istanza_archivio = precedente


__all__ = [
    "DIMENSIONE_MAX_BYTE",
    "ESTENSIONI_AMMESSE",
    "ArchivioAdapter",
    "ArchivioDisco",
    "ArchivioFinto",
    "ottieni_archivio",
    "imposta_archivio",
    "usa_archivio",
]
