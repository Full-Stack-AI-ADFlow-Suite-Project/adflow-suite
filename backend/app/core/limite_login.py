"""Prenotazioni atomiche PostgreSQL, indipendenti dal rollback del login."""
from datetime import datetime, timedelta
from hashlib import sha256
import hmac
from math import ceil

from sqlalchemy import Engine, text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import leggi_impostazioni
from app.core.db import motore
from app.core.errori import ErroreDominio


class TroppiTentativi(ErroreDominio):
    status_code = 429

    def __init__(
        self,
        riprova_dopo: int,
        messaggio: str = "Troppi tentativi di accesso. Riprova più tardi.",
    ):
        super().__init__(messaggio)
        self.riprova_dopo = riprova_dopo


class LimiteNonDisponibile(ErroreDominio):
    status_code = 503


def prenota(
    tipo: str,
    identificatore: str,
    ora: datetime,
    *,
    engine: Engine | None = None,
    limite: int | None = None,
    finestra_secondi: int | None = None,
    messaggio: str | None = None,
) -> None:
    """Conta un tentativo; oltre il limite solleva ``TroppiTentativi``.

    Senza parametri legge i limiti del login. ``limite``, ``finestra_secondi`` e
    ``messaggio`` servono agli altri usi (azioni AI) e non cambiano il login.
    """
    impostazioni = leggi_impostazioni()
    if limite is None:
        limite = impostazioni.login_limite_tentativi
    if finestra_secondi is None:
        finestra_secondi = impostazioni.login_finestra_secondi
    chiave = hmac.new(
        impostazioni.login_limite_segreto.encode(),
        (tipo + "\x00" + identificatore).encode("utf-8"),
        sha256,
    ).hexdigest()
    try:
        # La transazione viene confermata prima di un eventuale 401/429.
        # ON CONFLICT serializza anche richieste di processi diversi.
        with (engine or motore()).begin() as connessione:
            connessione.execute(
                text(
                    """
                DELETE FROM limite_login WHERE scade_il <= :ora AND chiave IN (
                    SELECT chiave FROM limite_login WHERE scade_il <= :ora
                    ORDER BY scade_il LIMIT 100
                )
            """
                ),
                {"ora": ora},
            )
            tentativi, scade_il = connessione.execute(
                text(
                    """
                INSERT INTO limite_login (chiave, tentativi, scade_il)
                VALUES (:chiave, 1, :scade)
                ON CONFLICT (chiave) DO UPDATE SET
                    tentativi = CASE WHEN limite_login.scade_il <= :ora THEN 1
                        ELSE LEAST(limite_login.tentativi + 1, :massimo) END,
                    scade_il = CASE WHEN limite_login.scade_il <= :ora THEN :scade
                        ELSE limite_login.scade_il END
                RETURNING tentativi, scade_il
            """
                ),
                {
                    "chiave": chiave,
                    "ora": ora,
                    "scade": ora + timedelta(seconds=finestra_secondi),
                    "massimo": limite + 1,
                },
            ).one()
    except SQLAlchemyError:
        raise LimiteNonDisponibile("Accesso temporaneamente non disponibile.") from None
    if tentativi > limite:
        riprova_dopo = max(1, ceil((scade_il - ora).total_seconds()))
        if messaggio is None:
            raise TroppiTentativi(riprova_dopo)
        raise TroppiTentativi(riprova_dopo, messaggio)


def prenota_azione_ai(utente_id: int, ora: datetime) -> None:
    """Limite per utente sulle azioni che fanno spendere l'AI (RL-018).

    Rigenera testo, Rigenera immagine e invio della campagna: ``azioni_ai_limite``
    richieste ogni ``azioni_ai_finestra_secondi``. Stessa tabella del login, con
    un tipo suo, così i due conteggi non si toccano.
    """
    impostazioni = leggi_impostazioni()
    prenota(
        "azione_ai",
        str(utente_id),
        ora,
        limite=impostazioni.azioni_ai_limite,
        finestra_secondi=impostazioni.azioni_ai_finestra_secondi,
        messaggio="Troppe richieste. Riprova tra poco.",
    )
