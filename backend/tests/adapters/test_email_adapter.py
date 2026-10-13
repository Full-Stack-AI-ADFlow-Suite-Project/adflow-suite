"""Test dell'adattatore email: finto in memoria, SMTP verso il catcher."""

import smtplib

import pytest

from app.adapters.email import (
    Allegato,
    Email,
    EmailAdapter,
    EmailFinto,
    EmailSmtp,
    ErroreInvio,
    imposta_email,
    ottieni_email,
    usa_email,
)


def _email(allegati=None) -> Email:
    return Email(
        destinatario="artigiano@example.test",
        oggetto="Campagna respinta",
        corpo="Testo del messaggio",
        allegati=allegati or [],
    )


def test_ottieni_email_restituisce_smtp():
    imposta_email(None)
    assert isinstance(ottieni_email(), EmailSmtp)
    assert ottieni_email() is ottieni_email()
    imposta_email(None)


def test_usa_email_sostituisce_e_ripristina():
    finto = EmailFinto()
    with usa_email(finto):
        assert ottieni_email() is finto
    assert isinstance(ottieni_email(), EmailSmtp)
    imposta_email(None)


def test_finto_registra_le_email_inviate():
    finto = EmailFinto()
    email = _email(
        [Allegato(nome="foto.jpg", contenuto=b"\xff\xd8\xff", mime="image/jpeg")]
    )
    finto.invia(email)

    assert finto.inviate == [email]
    assert finto.tentativi == 1


def test_finto_fallisce_quante_volte_richiesto():
    finto = EmailFinto(fallimenti=2)
    for _ in range(2):
        with pytest.raises(ErroreInvio):
            finto.invia(_email())
    finto.invia(_email())

    assert finto.tentativi == 3
    assert len(finto.inviate) == 1


class _SmtpFinto:
    """SMTP finto per provare EmailSmtp senza rete."""

    inviati = []
    solleva = False

    def __init__(self, host, porta, timeout):
        self.host, self.porta, self.timeout = host, porta, timeout

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def send_message(self, messaggio):
        _SmtpFinto.inviati.append(messaggio)
        if _SmtpFinto.solleva:
            raise smtplib.SMTPException("connessione rifiutata")


def test_smtp_compone_e_manda_il_messaggio(monkeypatch):
    _SmtpFinto.inviati = []
    _SmtpFinto.solleva = False
    monkeypatch.setattr(smtplib, "SMTP", _SmtpFinto)

    EmailSmtp(host="mailpit.test", porta=1025).invia(
        _email(
            [Allegato(nome="foto.jpg", contenuto=b"\xff\xd8\xff", mime="image/jpeg")]
        )
    )

    (messaggio,) = _SmtpFinto.inviati
    assert messaggio["To"] == "artigiano@example.test"
    assert messaggio["Subject"] == "Campagna respinta"
    corpo = messaggio.get_body(preferencelist=("plain",))
    assert corpo is not None and "Testo del messaggio" in corpo.get_content()
    allegati = list(messaggio.iter_attachments())
    assert len(allegati) == 1
    assert allegati[0].get_filename() == "foto.jpg"


def test_smtp_avvolge_gli_errori_in_errore_invio(monkeypatch):
    _SmtpFinto.inviati = []
    _SmtpFinto.solleva = True
    monkeypatch.setattr(smtplib, "SMTP", _SmtpFinto)

    with pytest.raises(ErroreInvio):
        EmailSmtp(host="mailpit.test", porta=1025).invia(_email())


def test_email_adapter_e_astratto():
    with pytest.raises(TypeError):
        EmailAdapter()
