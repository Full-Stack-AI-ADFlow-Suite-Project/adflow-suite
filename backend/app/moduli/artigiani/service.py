"""Logica del modulo artigiani: l'unica parte che gli altri moduli possono importare."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from .models import AccountSocial, ProfiloBottega
from .domain import CANALI, POST_A_SETTIMANA
from .schemas import CanaleCollegato, NuovoArtigiano, ArtigianoCreato, SchedaArtigiano
from app.core.errori import NonTrovato
from app.moduli.accesso import service as accesso
from .profilo_schemas import ProfiloPubblico, ProfiloScrittura


def stato_canali(db: Session, utente_id: int) -> list[CanaleCollegato]:
    """Stato di ogni canale MVP del solo utente autenticato (T1-14, R-22)."""
    profilo = profilo_di(db, utente_id)
    collegati = set(canali_collegati(db, profilo.id)) if profilo else set()
    return [
        CanaleCollegato(canale=canale, collegato=canale in collegati)
        for canale in CANALI
    ]


def profilo_di(
    db: Session,
    utente_id: int,
) -> ProfiloBottega | None:
    """Restituisce il profilo della bottega dell'utente, o None se assente.

    Usata da ``campagne`` (verifica prima dell'invio) e da ``revisione``
    (visualizzazione dati artigiano). Restituire ``None`` — e non sollevare
    ``NonTrovato`` — permette al chiamante di distinguere tra utente senza
    profilo (onboarding in corso) e utente inesistente (errore diverso).

    Args:
        db: sessione del database (aperta e chiusa dal chiamante).
        utente_id: chiave primaria dell'utente di cui si cerca il profilo.

    Returns:
        Il record ``ProfiloBottega`` se esiste, altrimenti ``None``.
    """
    return db.scalar(
        select(ProfiloBottega).where(ProfiloBottega.utente_id == utente_id)
    )


def profilo(db: Session, profilo_id: int) -> ProfiloBottega | None:
    """Profilo della bottega con l'id indicato, o None se non esiste (plan §6).

    Usata da ``campagne`` per i dati della bottega di una campagna quando chi
    guarda non è il proprietario. Il record si legge, non si modifica.
    """
    return db.get(ProfiloBottega, profilo_id)


def post_a_settimana(frequenza: str | None) -> int:
    """Post alla settimana per canale di una frequenza (plan §2, spec R-05).

    Senza frequenza, o con un valore fuori da ``domain.FREQUENZE``, vale
    ``decidete_voi``.
    """
    return POST_A_SETTIMANA.get(frequenza or "", POST_A_SETTIMANA["decidete_voi"])


def canali_collegati(db: Session, profilo_id: int) -> list[str]:
    """Canali con account nello stato collegato, in ordine di piattaforma (R-22)."""
    return list(
        db.scalars(
            select(AccountSocial.piattaforma)
            .where(
                AccountSocial.profilo_id == profilo_id,
                AccountSocial.stato == "collegato",
            )
            .order_by(AccountSocial.piattaforma)
        )
    )


def leggi_profilo_personale(db: Session, utente_id: int) -> ProfiloBottega:
    """Profilo dell'artigiano autenticato; non accetta un proprietario dal client."""
    from app.core.errori import NonTrovato

    record = profilo_di(db, utente_id)
    if record is None:
        raise NonTrovato("Profilo della bottega non trovato.")
    return record


def salva_profilo_personale(
    db: Session, utente_id: int, dati: "ProfiloScrittura", ora: "datetime"
) -> ProfiloBottega:
    """Sostituisce i dati del profilo, preservando account e snapshot.

    L'upsert PostgreSQL evita due profili anche con prime scritture concorrenti.
    Il commit resta alla sessione del router.
    """
    primo_profilo = profilo_di(db, utente_id) is None
    valori = dati.model_dump()
    valori["aggiornato_il"] = ora
    inserimento = insert(ProfiloBottega).values(utente_id=utente_id, **valori)
    comando = inserimento.on_conflict_do_update(
        index_elements=[ProfiloBottega.utente_id], set_=valori
    ).returning(ProfiloBottega)
    record = db.scalars(comando, execution_options={"populate_existing": True}).one()
    if primo_profilo:
        # Gli account hanno una FK al profilo: si preparano atomicamente al
        # primo salvataggio, senza inventare prima un profilo di comunicazione.
        for piattaforma in CANALI:
            db.execute(
                insert(AccountSocial)
                .values(
                    profilo_id=record.id,
                    piattaforma=piattaforma,
                    id_pagina=f"{piattaforma}-pagina-seed-finta",
                    stato="collegato",
                )
                .on_conflict_do_nothing(constraint="uq_account_social_piattaforma")
            )
    return record


def scheda_artigiano(db: Session, utente_id: int) -> SchedaArtigiano:
    """Account, canali e profilo di un artigiano, per l'operatore (spec R-38, CA-93).

    L'id di un operatore o di un utente che non esiste è lo stesso 404: la
    pagina non rivela chi ha un account.
    """
    try:
        record = accesso.utente(db, utente_id)
    except NonTrovato:
        record = None
    if record is None or record.ruolo != "artigiano":
        raise NonTrovato("Artigiano non trovato.")
    bottega = profilo_di(db, record.id)
    return SchedaArtigiano(
        id=record.id,
        nome=record.nome,
        email=record.email,
        attivo=record.attivo,
        profilo=ProfiloPubblico.model_validate(bottega) if bottega else None,
        canali_collegati=canali_collegati(db, bottega.id) if bottega else [],
    )


def crea_artigiano(db: Session, dati: NuovoArtigiano) -> ArtigianoCreato:
    """Creazione da parte del consorzio: non salva né ripropone la password in chiaro."""
    record, password = accesso.crea_artigiano(db, dati.email, dati.nome)
    return ArtigianoCreato(
        id=record.id,
        email=record.email,
        nome=record.nome,
        password_provvisoria=password,
    )
