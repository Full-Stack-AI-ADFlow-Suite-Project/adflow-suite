"""Endpoint del modulo revisione: chiamano service.py, senza logica di business."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.orologio import adesso
from app.moduli.accesso import service as accesso

from . import decisioni, interventi, letture, service, sospensione
from .schemas import (
    ArtigianoElenco,
    CampagnaDaApprovare,
    CampagnaNota,
    CampagnaRespingi,
    CampagnaRiattiva,
    CampagnaSospendi,
    CampagnaTogliCanale,
    FotoPossibile,
    PostAnnulla,
    PostCambiaFoto,
    PostControllato,
    PostModifica,
    PostRigenera,
    PostRiprogramma,
    PostSposta,
    SchedaArtigiano,
    VediCampagnaSchema,
)

router = APIRouter(tags=["revisione"])


@router.get("/da-approvare", response_model=list[CampagnaDaApprovare])
def campagne_da_approvare(
    db: Annotated[Session, Depends(get_db)],
    utente: Annotated[accesso.Utente, Depends(accesso.richiede_ruolo("operatore"))],
) -> list[CampagnaDaApprovare]:
    """Campagne da approvare di tutti gli artigiani, dalla più urgente (R-38, CA-69)."""
    return letture.da_approvare(db)


@router.get("/artigiani", response_model=list[ArtigianoElenco])
def elenco_artigiani(
    db: Annotated[Session, Depends(get_db)],
    utente: Annotated[accesso.Utente, Depends(accesso.richiede_ruolo("operatore"))],
) -> list[ArtigianoElenco]:
    """Tutti gli artigiani del consorzio, dalla scadenza più vicina."""
    return letture.elenco_artigiani(db)


@router.get("/artigiani/{utente_id}", response_model=SchedaArtigiano)
def scheda_artigiano(
    utente_id: int,
    db: Annotated[Session, Depends(get_db)],
    utente: Annotated[accesso.Utente, Depends(accesso.richiede_ruolo("operatore"))],
) -> SchedaArtigiano:
    """Scheda dell'artigiano: account, profilo e campagne per sezioni."""
    return letture.scheda_artigiano(db, utente_id)


@router.get("/campagne/{campagna_id}/post", response_model=VediCampagnaSchema)
def vedi_campagna(
    campagna_id: int,
    db: Annotated[Session, Depends(get_db)],
    utente: Annotated[accesso.Utente, Depends(accesso.richiede_ruolo("operatore"))],
    ora: Annotated[datetime, Depends(adesso)],
    stato: str | None = None,
) -> VediCampagnaSchema:
    """Vedi campagna in ogni stato dopo l'invio, per l'operatore (CA-60)."""
    return service.vedi_campagna(db, campagna_id, stato, ora)


@router.post("/campagne/{campagna_id}/approva")
def approva_campagna(
    campagna_id: int,
    db: Annotated[Session, Depends(get_db)],
    utente: Annotated[accesso.Utente, Depends(accesso.richiede_ruolo("operatore"))],
    ora: Annotated[datetime, Depends(adesso)],
) -> dict[str, str]:
    """Approva in blocco: post approvati, campagna attiva (R-14, CA-21/22)."""
    service.approva(db, campagna_id, utente, ora)
    return {"stato": "attiva"}


@router.post("/campagne/{campagna_id}/sospendi")
def sospendi_campagna(
    campagna_id: int,
    db: Annotated[Session, Depends(get_db)],
    utente: Annotated[accesso.Utente, Depends(accesso.richiede_ruolo("operatore"))],
    corpo: CampagnaSospendi | None = None,
) -> dict[str, str]:
    """Sospende la pubblicazione di una campagna attiva, con una nota facoltativa
    (R-33, CA-32)."""
    sospensione.sospendi(db, campagna_id, utente, corpo.nota if corpo else None)
    return {"stato": "sospesa"}


@router.post("/campagne/{campagna_id}/riattiva")
def riattiva_campagna(
    campagna_id: int,
    corpo: CampagnaRiattiva,
    db: Annotated[Session, Depends(get_db)],
    utente: Annotated[accesso.Utente, Depends(accesso.richiede_ruolo("operatore"))],
    ora: Annotated[datetime, Depends(adesso)],
) -> dict[str, str]:
    """Riattiva una sospesa: gli arretrati scelti escono subito, gli altri
    diventano ``annullato`` (R-33, CA-32)."""
    sospensione.riattiva(db, campagna_id, utente, corpo.pubblica_ora, ora)
    return {"stato": "attiva"}


@router.post("/campagne/{campagna_id}/annulla")
def annulla_campagna(
    campagna_id: int,
    db: Annotated[Session, Depends(get_db)],
    utente: Annotated[accesso.Utente, Depends(accesso.richiede_ruolo("operatore"))],
    ora: Annotated[datetime, Depends(adesso)],
) -> dict[str, str]:
    """Annulla una campagna attiva o sospesa: i post ``approvato`` diventano
    ``annullato`` (R-33, CA-32)."""
    sospensione.annulla(db, campagna_id, utente, ora)
    return {"stato": "annullata"}


# Congelato per l'MVP, ADR-114: non estendere.
@router.post("/campagne/{campagna_id}/nota")
def nota_interna(
    campagna_id: int,
    corpo: CampagnaNota,
    db: Annotated[Session, Depends(get_db)],
    utente: Annotated[accesso.Utente, Depends(accesso.richiede_ruolo("operatore"))],
) -> dict[str, str]:
    """Nota interna in ogni stato dopo l'invio: solo operatori (R-32, CA-23)."""
    decisioni.nota(db, campagna_id, utente, corpo.nota)
    return {"stato": "ok"}


@router.post("/campagne/{campagna_id}/respingi")
def respingi_campagna(
    campagna_id: int,
    corpo: CampagnaRespingi,
    db: Annotated[Session, Depends(get_db)],
    utente: Annotated[accesso.Utente, Depends(accesso.richiede_ruolo("operatore"))],
    ora: Annotated[datetime, Depends(adesso)],
) -> dict[str, str]:
    """Respinge la campagna: post scartati, decisione e notifica (R-18, CA-24/25)."""
    decisioni.respingi(
        db, campagna_id, utente, corpo.motivo, corpo.nota, corpo.foto_segnate, ora
    )
    return {"stato": "respinta"}


# Congelato per l'MVP, ADR-114: non estendere.
@router.post("/campagne/{campagna_id}/togli-canale")
def togli_canale_campagna(
    campagna_id: int,
    corpo: CampagnaTogliCanale,
    db: Annotated[Session, Depends(get_db)],
    utente: Annotated[accesso.Utente, Depends(accesso.richiede_ruolo("operatore"))],
    ora: Annotated[datetime, Depends(adesso)],
) -> dict[str, str]:
    """Toglie un canale: post scartati, decisione `canale_tolto` (CA-53)."""
    record = decisioni.togli_canale(
        db, campagna_id, utente, corpo.canale, corpo.nota, ora
    )
    return {"stato": record.stato}


@router.post("/post/{post_id}/modifica")
def modifica_post(
    post_id: int,
    corpo: PostModifica,
    db: Annotated[Session, Depends(get_db)],
    utente: Annotated[accesso.Utente, Depends(accesso.richiede_ruolo("operatore"))],
    ora: Annotated[datetime, Depends(adesso)],
) -> dict[str, str]:
    """Modifica a mano del testo: versione `modifica_operatore` (R-30, CA-64)."""
    interventi.modifica(db, post_id, utente, corpo.testo, corpo.hashtag, ora)
    return {"stato": "ok"}


# Congelato per l'MVP, ADR-114: non estendere.
@router.post("/post/{post_id}/controllato")
def controllato_post(
    post_id: int,
    corpo: PostControllato,
    db: Annotated[Session, Depends(get_db)],
    utente: Annotated[accesso.Utente, Depends(accesso.richiede_ruolo("operatore"))],
    ora: Annotated[datetime, Depends(adesso)],
) -> dict[str, str]:
    """Mette o toglie la spunta «va bene» sul post (R-30, CA-65)."""
    interventi.controllato(db, post_id, utente.id, corpo.valore, ora)
    return {"stato": "ok"}


@router.post("/post/{post_id}/rigenera")
def rigenera_post(
    post_id: int,
    corpo: PostRigenera,
    db: Annotated[Session, Depends(get_db)],
    utente: Annotated[accesso.Utente, Depends(accesso.richiede_ruolo("operatore"))],
    ora: Annotated[datetime, Depends(adesso)],
) -> dict[str, str]:
    """Accende l'intervento e accoda il job `rigenera_post` (R-03, R-31)."""
    interventi.rigenera(
        db, post_id, corpo.modalita, corpo.testo_proposto, corpo.nota, ora
    )
    return {"stato": "in_corso"}


@router.post("/post/{post_id}/riprogramma")
def riprogramma_post(
    post_id: int,
    corpo: PostRiprogramma,
    db: Annotated[Session, Depends(get_db)],
    utente: Annotated[accesso.Utente, Depends(accesso.richiede_ruolo("operatore"))],
    ora: Annotated[datetime, Depends(adesso)],
) -> dict[str, str]:
    """Un post fallito torna approvato con una nuova data (R-34, CA-67)."""
    interventi.riprogramma(db, post_id, utente.id, corpo.data_ora, ora)
    return {"stato": "approvato"}


# Corsia 6 (ADR-116): interventi dopo l'approvazione e sposta.
@router.post("/post/{post_id}/sposta")
def sposta_post(
    post_id: int,
    corpo: PostSposta,
    db: Annotated[Session, Depends(get_db)],
    utente: Annotated[accesso.Utente, Depends(accesso.richiede_ruolo("operatore"))],
    ora: Annotated[datetime, Depends(adesso)],
) -> dict[str, str]:
    """Sposta il post a un'altra data e ora, in revisione o dopo l'approvazione
    (R-16, R-36, CA-72)."""
    post = interventi.sposta(db, post_id, utente.id, corpo.data_ora, ora)
    return {"stato": post.stato}


@router.post("/post/{post_id}/annulla")
def annulla_post(
    post_id: int,
    corpo: PostAnnulla,
    db: Annotated[Session, Depends(get_db)],
    utente: Annotated[accesso.Utente, Depends(accesso.richiede_ruolo("operatore"))],
    ora: Annotated[datetime, Depends(adesso)],
) -> dict[str, str]:
    """Annulla un post approvato con la nota, senza sospendere la campagna
    (R-16, R-36, CA-85)."""
    interventi.annulla(db, post_id, utente.id, corpo.nota, ora)
    return {"stato": "annullato"}


@router.get("/post/{post_id}/foto-possibili", response_model=list[FotoPossibile])
def foto_possibili_post(
    post_id: int,
    db: Annotated[Session, Depends(get_db)],
    utente: Annotated[accesso.Utente, Depends(accesso.richiede_ruolo("operatore"))],
    ora: Annotated[datetime, Depends(adesso)],
) -> list[FotoPossibile]:
    """Le foto con cui si può cambiare quella del post (R-36, CA-71)."""
    return interventi.foto_possibili(db, post_id, ora)


@router.post("/post/{post_id}/cambia-foto")
def cambia_foto_post(
    post_id: int,
    corpo: PostCambiaFoto,
    db: Annotated[Session, Depends(get_db)],
    utente: Annotated[accesso.Utente, Depends(accesso.richiede_ruolo("operatore"))],
    ora: Annotated[datetime, Depends(adesso)],
) -> dict[str, str]:
    """Cambia la foto del post: versione `cambio_foto` (R-16, R-36, CA-71)."""
    interventi.cambia_foto(db, post_id, corpo.foto_id, utente, ora)
    return {"stato": "ok"}
