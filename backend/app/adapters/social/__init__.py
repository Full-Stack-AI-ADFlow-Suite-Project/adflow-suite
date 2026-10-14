"""Adattatore social: pubblicazione dei post sulle piattaforme (plan §5)."""

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Optional

from app.core.config import leggi_impostazioni

from .base import TIPI_ERRORE, EsitoPubblicazione, SocialAdapter
from .finto import MARCA_ERRORE_DEFINITIVO, MARCA_ERRORE_TEMPORANEO, SocialFinto
from .meta import SocialMeta

_istanza_social: Optional[SocialAdapter] = None


def ottieni_social() -> SocialAdapter:
    """Restituisce l'adattatore social configurato da ``SOCIAL_PROVIDER``.

    ``finto`` (default, sviluppo e test) crea ``SocialFinto``; ``meta`` crea
    ``SocialMeta``, che pubblica sulla Pagina di prova di ``.env`` (brief-meta).
    Nei test si sostituisce con ``usa_social()`` o ``imposta_social()``.
    """
    global _istanza_social
    if _istanza_social is None:
        impostazioni = leggi_impostazioni()
        if impostazioni.social_provider == "meta":
            _istanza_social = SocialMeta(
                pagina_id=impostazioni.meta_pagina_id,
                token=impostazioni.meta_token_pagina,
                instagram_id=impostazioni.meta_instagram_id,
                versione_graf=impostazioni.meta_graph_versione,
            )
        else:
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
    "SocialMeta",
    "ottieni_social",
    "imposta_social",
    "usa_social",
]
