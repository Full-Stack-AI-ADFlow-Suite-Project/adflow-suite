"""Profilo minimo con dati fittizi e account social collegati, senza commit."""
from sqlalchemy.orm import Session
from app.moduli.artigiani.models import AccountSocial, ProfiloBottega
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
    for canale in record.canali:
        account_social(db, record, piattaforma=canale)
    return record


_nuovo_profilo = profilo


def account_social(
    db: Session,
    profilo: ProfiloBottega | None = None,
    *,
    piattaforma: str = "facebook",
    stato: str = "collegato",
    **campi,
) -> AccountSocial:
    if profilo is None:
        profilo = _nuovo_profilo(db)
    dati = dict(
        profilo_id=profilo.id,
        piattaforma=piattaforma,
        id_pagina=f"{piattaforma}-pagina-di-prova",
        stato=stato,
    )
    dati.update(campi)
    record = AccountSocial(**dati)
    db.add(record)
    db.flush()
    return record
