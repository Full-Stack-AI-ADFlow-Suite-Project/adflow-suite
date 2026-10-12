"""Implementazione finta dell'adattatore email per sviluppo e test."""

from .base import Email, EmailAdapter, ErroreInvio


class EmailFinto(EmailAdapter):
    """Adattatore email simulato, senza rete.

    Ogni chiamata a ``invia()`` registra l'email in ``inviate`` per i test che
    controllano che cosa è partito. Per comandare un errore si imposta
    ``fallimenti``: i primi ``fallimenti`` invii sollevano ``ErroreInvio``,
    poi l'invio torna a riuscire.
    """

    def __init__(self, fallimenti: int = 0) -> None:
        self.inviate: list[Email] = []
        self.fallimenti = fallimenti
        self.tentativi = 0

    def invia(self, email: Email) -> None:
        self.tentativi += 1
        if self.fallimenti > 0:
            self.fallimenti -= 1
            raise ErroreInvio("Errore di invio simulato")
        self.inviate.append(email)
