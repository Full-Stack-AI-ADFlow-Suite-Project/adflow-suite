"""Profilo minimo con dati fittizi, senza commit."""
from sqlalchemy.orm import Session
from app.moduli.artigiani.models import ProfiloBottega
from tests.moduli.accesso.fabbrica import utente


def profilo(db: Session, *, utente_id: int | None = None, **campi) -> ProfiloBottega:
    if utente_id is None:
        utente_id = utente(db).id
    dati = dict(
        utente_id=utente_id,
        nome="Bottega di prova",
        referente="Referente",
        citta="Roma",
        tipo_prodotto="ceramica_vetro",
        clienti_ideali="Clienti locali",
        obiettivo="notorieta",
        canali=["instagram"],
        frequenza="f1_2",
    )
    dati.update(campi)
    record = ProfiloBottega(**dati)
    db.add(record)
    db.flush()
    return record
