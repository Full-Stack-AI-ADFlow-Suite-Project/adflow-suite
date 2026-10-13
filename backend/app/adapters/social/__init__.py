"""Adattatore social: pubblicazione dei post sulle piattaforme (plan §5)."""

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Optional

from .base import TIPI_ERRORE, EsitoPubblicazione, SocialAdapter
from .finto import MARCA_ERRORE_DEFINITIVO, MARCA_ERRORE_TEMPORANEO, SocialFinto

_istanza_social: Optional[SocialAdapter] = None


def ottieni_social() -> SocialAdapter:
    """Restituisce l'adattatore social configurato.

    Per ora esiste solo ``SocialFinto``; l'implementazione Meta arriva con il
    collegamento degli account (sprint successivo). Nei test si sostituisce
    con ``usa_social()`` o ``imposta_social()``.
    """
    global _istanza_social
    if _istanza_social is None:
        _istanza_social = SocialFinto()
    return _istanza_social


def imposta_social(adattatore: Optional[SocialAdapter]) -> None:
    """Imposta o resetta l'adattatore social globale."""
    global _istanza_social
    _istanza_social = adattatore


@contextmanager
def usa_social(adattatore: SocialAdapter) -> Iterator[SocialAdapter]:
    """Usa un adattatore dentro il blocco with, poi ripristina il precedente."""
    global _istanza_social
    precedente = _istanza_social
    _istanza_social = adattatore
    try:
        yield adattatore
    finally:
        _istanza_social = precedente


__all__ = [
    "TIPI_ERRORE",
    "MARCA_ERRORE_DEFINITIVO",
    "MARCA_ERRORE_TEMPORANEO",
    "EsitoPubblicazione",
    "SocialAdapter",
    "SocialFinto",
    "ottieni_social",
    "imposta_social",
    "usa_social",
]
