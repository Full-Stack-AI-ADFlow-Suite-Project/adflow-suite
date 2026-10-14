# Congelato per l'MVP, ADR-114: non estendere.
"""Interfaccia dell'adattatore email (plan §5)."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class Allegato:
    """Un file allegato all'email (es. la miniatura di una foto da rifare).

    Attributes:
        nome: nome del file come appare al destinatario.
        contenuto: byte del file.
        mime: tipo MIME del file (es. ``image/jpeg``).
    """

    nome: str
    contenuto: bytes
    mime: str


@dataclass
class Email:
    """Un'email pronta per l'invio.

    Attributes:
        destinatario: indirizzo email del destinatario.
        oggetto: riga dell'oggetto.
        corpo: testo del messaggio.
        allegati: allegati, vuoti se non ce ne sono.
    """

    destinatario: str
    oggetto: str
    corpo: str
    allegati: list[Allegato] = field(default_factory=list)


class EmailAdapter(ABC):
    """Contratto dell'invio email.

    Ogni trasporto ha la sua implementazione; in sviluppo si spedisce verso un
    catcher locale (Mailpit) con ``EmailSmtp``, nei test si usa ``EmailFinto``.
    """

    @abstractmethod
    def invia(self, email: Email) -> None:
        """Invia l'email.

        Args:
            email: il messaggio completo di destinatario, oggetto, corpo e
                allegati.

        Raises:
            ErroreInvio: il trasporto non è riuscito: il chiamante decide se
                riprovare.
        """
        raise NotImplementedError


class ErroreInvio(Exception):
    """Il trasporto email non è riuscito: il messaggio non entra nei log."""
