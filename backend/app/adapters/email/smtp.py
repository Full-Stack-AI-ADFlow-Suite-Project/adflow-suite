"""Implementazione SMTP dell'adattatore email: in sviluppo spedisce al catcher
locale (Mailpit), in produzione al server configurato (plan §1)."""

import smtplib
from email.message import EmailMessage
from email.utils import formataddr

from app.core.config import leggi_impostazioni

from .base import Email, EmailAdapter, ErroreInvio


class EmailSmtp(EmailAdapter):
    """Invia via SMTP verso ``SMTP_HOST``/``SMTP_PORT`` (Mailpit in locale).

    Mittente e firma sono quelli del consorzio in configurazione. Nessun dato
    del messaggio finisce nei log: l'errore risale come ``ErroreInvio`` e chi
    chiama decide come registrarlo.
    """

    def __init__(self, host: str | None = None, porta: int | None = None) -> None:
        impostazioni = leggi_impostazioni()
        self._host = host if host is not None else impostazioni.smtp_host
        self._porta = porta if porta is not None else impostazioni.smtp_port
        self._mittente = impostazioni.consorzio_email or "adflow@localhost"
        self._nome_mittente = impostazioni.consorzio_nome or "AdFlow"

    def invia(self, email: Email) -> None:
        messaggio = EmailMessage()
        messaggio["From"] = formataddr((self._nome_mittente, self._mittente))
        messaggio["To"] = email.destinatario
        messaggio["Subject"] = email.oggetto
        messaggio.set_content(email.corpo)
        for allegato in email.allegati:
            tipo, _, sottotipo = allegato.mime.partition("/")
            messaggio.add_attachment(
                allegato.contenuto,
                maintype=tipo or "application",
                subtype=sottotipo or "octet-stream",
                filename=allegato.nome,
            )
        try:
            with smtplib.SMTP(self._host, self._porta, timeout=10) as smtp:
                smtp.send_message(messaggio)
        except (OSError, smtplib.SMTPException) as errore:
            # Il messaggio dell'eccezione può contenere dati del destinatario:
            # non lo facciamo propagare, il chiamante logga solo il tipo.
            raise ErroreInvio(type(errore).__name__) from None
