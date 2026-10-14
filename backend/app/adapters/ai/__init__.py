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
    ImmagineAI,
    PianoAI,
    PostAI,
    PostScritto,
    TIPI_USO,
    UsoAI,
)
from .finto import AIFinto
from .immagini import prompt_immagine

_istanza_ai: Optional[AIAdapter] = None


def ottieni_ai() -> AIAdapter:
    """Restituisce il provider AI scelto con ``AI_PROVIDER``.

    ``finto`` per sviluppo e test, ``litellm`` per il provider vero: senza i
    modelli in ``.env`` solleva un ``ErroreAI`` di tipo ``configurazione``.
    Nei test si sostituisce con ``usa_ai()`` o ``imposta_ai()``.
    """
    global _istanza_ai
    if _istanza_ai is None:
        if leggi_impostazioni().ai_provider == "litellm":
            # LiteLLM è pesante da importare: solo se serve davvero.
            from .litellm import AILiteLLM

            _istanza_ai = AILiteLLM()
        else:
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
    "TIPI_USO",
    "AIAdapter",
    "AIFinto",
    "CampagnaAI",
    "ErroreAI",
    "FotoAI",
    "GruppoAI",
    "ImmagineAI",
    "PianoAI",
    "PostAI",
    "PostScritto",
    "UsoAI",
    "prompt_immagine",
    "ottieni_ai",
    "imposta_ai",
    "usa_ai",
]
