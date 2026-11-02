"""Email non consegnabile (T4-105, §7.4).

Atteso: il flusso principale non si blocca. La spedizione è un job separato
(`invia_notifica`): se il trasporto cade, la notifica resta con il suo esito e
la campagna ha già la sua transizione.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.adapters.email.base import ErroreInvio
from app.adapters.email import usa_email
from app.moduli.campagne.models import Campagna
from app.moduli.revisione import decisioni
from tests.moduli.artigiani.fabbrica import profilo
from tests.moduli.campagne.fabbrica import campagna_in_revisione
from tests.moduli.contenuti.fabbrica import post_da_approvare


class EmailRotta:
    """Un trasporto che rifiuta ogni invio."""

    def invia(self, email):
        raise ErroreInvio("relay irraggiungibile")

    def chiudi(self):
        pass


def test_email_rotta_non_blocca_la_respinta(db, utente_di_prova):
    """La respinta passa lo stesso; il job email non ferma la campagna."""
    artigiano = utente_di_prova("artigiano")
    operatore = utente_di_prova("operatore")
    bottega = profilo(db, utente_id=artigiano.id)
    campagna = campagna_in_revisione(db, profilo_id=bottega.id, canali=["instagram"])
    post_da_approvare(db, campagna_id=campagna.id)
    db.flush()

    with usa_email(EmailRotta()):
        decisioni.respingi(
            db,
            campagna.id,
            operatore,
            "foto",
            "Foto non della bottega",
            [],
            datetime.now(timezone.utc),
        )

    assert db.get(Campagna, campagna.id).stato == "respinta"
