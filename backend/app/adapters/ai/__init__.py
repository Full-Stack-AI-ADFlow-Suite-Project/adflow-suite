"""Adattatore AI: analisi delle foto, piano e testi dei post (plan §5)."""

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Optional

from app.core.config import leggi_impostazioni

from .base import (
    TIPI_ERRORE,
    AIAdapter,
    CampagnaAI,
    ErroreAI,
    FotoAI,
    GruppoAI,
    PianoAI,
    PostAI,
    PostScritto,
)
from .finto import AIFinto

_istanza_ai: Optional[AIAdapter] = None


def ottieni_ai() -> AIAdapter:
    """Restituisce il provider AI scelto con ``AI_PROVIDER``.

    Per ora esiste solo ``AIFinto``: con un altro provider solleva un
    ``ErroreAI`` di tipo ``configurazione``, come farà una chiave sbagliata.
    Nei test si sostituisce con ``usa_ai()`` o ``imposta_ai()``.
    """
    global _istanza_ai
    if _istanza_ai is None:
        provider = leggi_impostazioni().ai_provider
        if provider != "finto":
            raise ErroreAI(
                "configurazione",
                f"Il provider AI «{provider}» non è ancora disponibile: "
                f"imposta AI_PROVIDER=finto.",
            )
        _istanza_ai = AIFinto()
    return _istanza_ai


def imposta_ai(adattatore: Optional[AIAdapter]) -> None:
    """Imposta o resetta il provider AI globale."""
    global _istanza_ai
    _istanza_ai = adattatore


@contextmanager
def usa_ai(adattatore: AIAdapter) -> Iterator[AIAdapter]:
    """Usa un provider dentro il blocco with, poi ripristina il precedente."""
    global _istanza_ai
    precedente = _istanza_ai
    _istanza_ai = adattatore
    try:
        yield adattatore
    finally:
        _istanza_ai = precedente


__all__ = [
    "TIPI_ERRORE",
    "AIAdapter",
    "AIFinto",
    "CampagnaAI",
    "ErroreAI",
    "FotoAI",
    "GruppoAI",
    "PianoAI",
    "PostAI",
    "PostScritto",
    "ottieni_ai",
    "imposta_ai",
    "usa_ai",
]
