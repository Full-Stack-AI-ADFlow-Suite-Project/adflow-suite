"""Profilo minimo con dati fittizi e account social collegati, senza commit."""
from datetime import date
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.moduli.artigiani.models import (
    AccountSocial,
    AnagraficaArtigiano,
    ProfiloBottega,
)
from tests.moduli.accesso.fabbrica import utente


def anagrafica(
    db: Session, *, utente_id: int | None = None, **campi
) -> AnagraficaArtigiano:
    if utente_id is None:
        utente_id = utente(db, "artigiano").id
    numero = db.scalar(select(func.count()).select_from(AnagraficaArtigiano)) + 1
    dati = dict(
        utente_id=utente_id,
        codice=f"ART-{numero:04d}",
        codice_consorzio="CONS-001",
        nome_bottega="Bottega di prova",
        referente="Referente",
        citta="Roma",
        stato_iscrizione="attiva",
        iscritto_il=date(2030, 1, 5),
    )
    dati.update(campi)
    record = AnagraficaArtigiano(**dati)
    db.add(record)
    db.flush()
    return record


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
        profilo = _nuovo_profilo(db, canali=[piattaforma])
        record = db.scalar(
            select(AccountSocial).where(
                AccountSocial.profilo_id == profilo.id,
                AccountSocial.piattaforma == piattaforma,
            )
        )
        record.stato = stato
        for campo, valore in campi.items():
            setattr(record, campo, valore)
        db.flush()
        return record
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
