"""Adattatore email: invio delle notifiche (plan §5)."""

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Optional

from .base import Allegato, Email, EmailAdapter, ErroreInvio
from .finto import EmailFinto
from .smtp import EmailSmtp

_istanza_email: Optional[EmailAdapter] = None


def ottieni_email() -> EmailAdapter:
    """Restituisce l'adattatore email configurato.

    Di default è ``EmailSmtp`` verso il catcher locale (Mailpit) o il server
    SMTP configurato; nei test si sostituisce con ``usa_email()`` o
    ``imposta_email()``.
    """
    global _istanza_email
    if _istanza_email is None:
        _istanza_email = EmailSmtp()
    return _istanza_email


def imposta_email(adattatore: Optional[EmailAdapter]) -> None:
    """Imposta o resetta l'adattatore email globale."""
    global _istanza_email
    _istanza_email = adattatore


@contextmanager
def usa_email(adattatore: EmailAdapter) -> Iterator[EmailAdapter]:
    """Usa un adattatore dentro il blocco with, poi ripristina il precedente."""
    global _istanza_email
    precedente = _istanza_email
    _istanza_email = adattatore
    try:
        yield adattatore
    finally:
        _istanza_email = precedente


__all__ = [
    "Allegato",
    "Email",
    "EmailAdapter",
    "EmailFinto",
    "EmailSmtp",
    "ErroreInvio",
    "imposta_email",
    "ottieni_email",
    "usa_email",
]
