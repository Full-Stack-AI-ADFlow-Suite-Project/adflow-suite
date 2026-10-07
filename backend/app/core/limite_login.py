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

    def __init__(self, riprova_dopo: int):
        super().__init__("Troppi tentativi di accesso. Riprova più tardi.")
        self.riprova_dopo = riprova_dopo


class LimiteNonDisponibile(ErroreDominio):
    status_code = 503


def prenota(
    tipo: str, identificatore: str, ora: datetime, *, engine: Engine | None = None
) -> None:
    impostazioni = leggi_impostazioni()
    chiave = hmac.new(
        impostazioni.login_limite_segreto.encode(),
        (tipo + "\x00" + identificatore).encode("utf-8"),
        sha256,
    ).hexdigest()
    limite = impostazioni.login_limite_tentativi
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
                    "scade": ora
                    + timedelta(seconds=impostazioni.login_finestra_secondi),
                    "massimo": limite + 1,
                },
            ).one()
    except SQLAlchemyError:
        raise LimiteNonDisponibile("Accesso temporaneamente non disponibile.") from None
    if tentativi > limite:
        raise TroppiTentativi(max(1, ceil((scade_il - ora).total_seconds())))
