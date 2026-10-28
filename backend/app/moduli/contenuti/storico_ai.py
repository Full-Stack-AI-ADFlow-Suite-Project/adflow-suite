"""Storico dell'AI: elenco, dettaglio e numeri delle chiamate (spec R-50, ADR-119).

Legge ``chiamata_ai`` e ``valutazione_ai``; i dati degli altri moduli vengono
dalle loro funzioni di plan §6: ``campagne.campagna()`` (titolo),
``artigiani.profilo()`` (bottega), ``accesso.utente()`` (chi ha votato).
Senza commit.
"""

from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import Select, and_, case, func, select
from sqlalchemy.orm import Session, aliased

from app.adapters.ai import TIPI_USO
from app.core.errori import NonTrovato
from app.core.orologio import ROMA
from app.moduli.accesso import service as accesso
from app.moduli.artigiani import service as artigiani
from app.moduli.campagne import service as campagne

from .domain import (
    ANNULLATO,
    APPROVATO,
    FALLITO,
    PUBBLICATO,
)
from .models import ChiamataAI, Post, ValutazioneAI, VersionePost
from .schemas import (
    ChiamataAIDettaglio,
    ChiamataAIRiga,
    NumeriAI,
    NumeriVersione,
    PaginaChiamateAI,
    ValutazioneAISchema,
)
from .immagini_ai import IMMAGINE_NON_CREATA

PER_PAGINA = 50
NON_TROVATA = "Chiamata non trovata."

STATI_APPROVATI = (APPROVATO, PUBBLICATO, FALLITO, ANNULLATO)
# Una versione del testo (o dell'immagine) scritta dall'AI, non dall'operatore.
INTERVENTI_DELL_AI = (
    "generazione",
    "rigenera_totale",
    "rigenera_da_proposta",
    "rigenera_immagine",
)
RIGENERAZIONI_TESTO = ("rigenera_totale", "rigenera_da_proposta")


def _filtri(
    campagna_id: int | None,
    tipo: str | None,
    modello: str | None,
    versione_prompt: str | None,
    esito: str | None,
    dal: date | None,
    al: date | None,
) -> list[Any]:
    """Le condizioni su ``chiamata_ai``; ``dal`` e ``al`` sono giorni di Roma, compresi."""
    condizioni: list[Any] = []
    if campagna_id is not None:
        condizioni.append(ChiamataAI.campagna_id == campagna_id)
    if tipo:
        condizioni.append(ChiamataAI.tipo == tipo)
    if modello:
        condizioni.append(ChiamataAI.modello_ai == modello)
    if versione_prompt:
        condizioni.append(ChiamataAI.versione_prompt == versione_prompt)
    if esito:
        condizioni.append(ChiamataAI.esito == esito)
    if dal is not None:
        condizioni.append(ChiamataAI.creata_il >= datetime.combine(dal, time(), ROMA))
    if al is not None:
        fine = datetime.combine(al + timedelta(days=1), time(), ROMA)
        condizioni.append(ChiamataAI.creata_il < fine)
    return condizioni


def _voto(valore: Any) -> float | None:
    return None if valore is None else round(float(valore), 2)


class _Anagrafica:
    """Titolo della campagna e nome della bottega, letti una volta per campagna."""

    def __init__(self, db: Session) -> None:
        self._db = db
        self._per_campagna: dict[int, tuple[str, str | None]] = {}

    def di(self, campagna_id: int) -> tuple[str, str | None]:
        if campagna_id not in self._per_campagna:
            campagna = campagne.campagna(self._db, campagna_id)
            profilo = artigiani.profilo(self._db, campagna.profilo_id)
            self._per_campagna[campagna_id] = (
                campagna.titolo,
                profilo.nome if profilo is not None else None,
            )
        return self._per_campagna[campagna_id]


def _riga(chiamata: ChiamataAI, voto: Any, anagrafica: _Anagrafica) -> dict[str, Any]:
    titolo, bottega = anagrafica.di(chiamata.campagna_id)
    return dict(
        id=chiamata.id,
        creata_il=chiamata.creata_il,
        campagna_id=chiamata.campagna_id,
        campagna_titolo=titolo,
        bottega=bottega,
        post_id=chiamata.post_id,
        foto_id=chiamata.foto_id,
        tipo=chiamata.tipo,
        modello_ai=chiamata.modello_ai,
        versione_prompt=chiamata.versione_prompt,
        esito=chiamata.esito,
        durata_ms=chiamata.durata_ms,
        costo_usd=chiamata.costo_usd,
        token_ingresso=chiamata.token_ingresso,
        token_uscita=chiamata.token_uscita,
        voto_medio=_voto(voto),
    )


def _voti_medi() -> Select:
    return (
        select(
            ValutazioneAI.chiamata_ai_id.label("chiamata_id"),
            func.avg(ValutazioneAI.voto).label("voto"),
        )
        .group_by(ValutazioneAI.chiamata_ai_id)
        .subquery()
    )


def elenco(
    db: Session,
    *,
    campagna_id: int | None = None,
    tipo: str | None = None,
    modello: str | None = None,
    versione_prompt: str | None = None,
    esito: str | None = None,
    dal: date | None = None,
    al: date | None = None,
    pagina: int = 1,
) -> PaginaChiamateAI:
    """Una pagina di chiamate, dalla più recente, con i filtri dati (R-50)."""
    condizioni = _filtri(campagna_id, tipo, modello, versione_prompt, esito, dal, al)
    totale = db.scalar(select(func.count()).select_from(ChiamataAI).where(*condizioni))
    voti = _voti_medi()
    righe = db.execute(
        select(ChiamataAI, voti.c.voto)
        .outerjoin(voti, voti.c.chiamata_id == ChiamataAI.id)
        .where(*condizioni)
        .order_by(ChiamataAI.creata_il.desc(), ChiamataAI.id.desc())
        .limit(PER_PAGINA)
        .offset((pagina - 1) * PER_PAGINA)
    ).all()
    anagrafica = _Anagrafica(db)
    return PaginaChiamateAI(
        voci=[
            ChiamataAIRiga(**_riga(chiamata, voto, anagrafica))
            for chiamata, voto in righe
        ],
        totale=totale or 0,
        pagina=pagina,
        per_pagina=PER_PAGINA,
    )


def valutazioni(db: Session, chiamata_id: int) -> list[ValutazioneAISchema]:
    """I voti dati a una chiamata, dal più vecchio, con il nome di chi li ha dati."""
    nomi: dict[int, str] = {}
    risultato = []
    for voto in db.scalars(
        select(ValutazioneAI)
        .where(ValutazioneAI.chiamata_ai_id == chiamata_id)
        .order_by(ValutazioneAI.creata_il, ValutazioneAI.id)
    ):
        if voto.utente_id not in nomi:
            nomi[voto.utente_id] = accesso.utente(db, voto.utente_id).nome
        risultato.append(
            ValutazioneAISchema(
                id=voto.id,
                utente_nome=nomi[voto.utente_id],
                voto=voto.voto,
                nota=voto.nota,
                creata_il=voto.creata_il,
            )
        )
    return risultato


def chiamata(db: Session, chiamata_id: int) -> ChiamataAI:
    """La chiamata con quell'id; ``NonTrovato`` (404) se non c'è."""
    record = db.get(ChiamataAI, chiamata_id)
    if record is None:
        raise NonTrovato(NON_TROVATA)
    return record


def dettaglio(db: Session, chiamata_id: int) -> ChiamataAIDettaglio:
    """Richiesta, risposta, errore e valutazioni di una chiamata (R-50)."""
    record = chiamata(db, chiamata_id)
    voto = db.scalar(
        select(func.avg(ValutazioneAI.voto)).where(
            ValutazioneAI.chiamata_ai_id == record.id
        )
    )
    return ChiamataAIDettaglio(
        **_riga(record, voto, _Anagrafica(db)),
        richiesta=record.richiesta,
        risposta=record.risposta,
        errore=record.errore,
        tentativo=record.tentativo,
        valutazioni=valutazioni(db, record.id),
    )


def numeri(
    db: Session,
    *,
    campagna_id: int | None = None,
    tipo: str | None = None,
    modello: str | None = None,
    versione_prompt: str | None = None,
    esito: str | None = None,
    dal: date | None = None,
    al: date | None = None,
) -> NumeriAI:
    """I numeri delle chiamate filtrate e dei testi delle loro campagne (R-50).

    Le chiamate si contano con i filtri. I testi e le immagini si contano sui
    post delle campagne che hanno almeno una di quelle chiamate: sono i post a
    dire quanti testi l'operatore ha tenuto, cambiato o rifatto. Medie e p95
    usano le sole ``durata_ms`` non nulle.
    """
    condizioni = _filtri(campagna_id, tipo, modello, versione_prompt, esito, dal, al)
    errata = case((ChiamataAI.esito != "ok", 1), else_=0)

    chiamate, costo, media, p95, errori = db.execute(
        select(
            func.count(),
            func.coalesce(func.sum(ChiamataAI.costo_usd), 0),
            func.avg(ChiamataAI.durata_ms),
            func.percentile_disc(0.95).within_group(ChiamataAI.durata_ms),
            func.coalesce(func.sum(errata), 0),
        ).where(*condizioni)
    ).one()
    voto_medio = db.scalar(
        select(func.avg(ValutazioneAI.voto))
        .join(ChiamataAI, ChiamataAI.id == ValutazioneAI.chiamata_ai_id)
        .where(*condizioni)
    )
    immagini_create = db.scalar(
        select(func.coalesce(func.sum(ChiamataAI.n_immagini), 0)).where(
            *condizioni, ChiamataAI.tipo == "immagine", ChiamataAI.esito == "ok"
        )
    )

    voti_della_chiamata = _voti_medi()
    per_versione = []
    for tipo_riga, versione, quante, sbagliate, durata, spesa, voto in db.execute(
        select(
            ChiamataAI.tipo,
            ChiamataAI.versione_prompt,
            func.count(),
            func.coalesce(func.sum(errata), 0),
            func.avg(ChiamataAI.durata_ms),
            func.coalesce(func.sum(ChiamataAI.costo_usd), 0),
            func.avg(voti_della_chiamata.c.voto),
        )
        .outerjoin(
            voti_della_chiamata, voti_della_chiamata.c.chiamata_id == ChiamataAI.id
        )
        .where(*condizioni)
        .group_by(ChiamataAI.tipo, ChiamataAI.versione_prompt)
    ):
        per_versione.append(
            NumeriVersione(
                tipo=tipo_riga,
                versione_prompt=versione,
                chiamate=quante,
                tasso_errore=sbagliate / quante,
                durata_media_ms=None if durata is None else round(durata),
                costo_usd=Decimal(spesa),
                voto_medio=_voto(voto),
            )
        )
    ordine = {nome: posto for posto, nome in enumerate(TIPI_USO)}
    per_versione.sort(
        key=lambda riga: (
            ordine.get(riga.tipo, len(ordine)),
            riga.versione_prompt or "",
        )
    )

    campagne_filtrate = select(ChiamataAI.campagna_id).where(*condizioni).distinct()
    post_delle_campagne = Post.campagna_id.in_(campagne_filtrate)
    precedente = aliased(VersionePost)
    ultima = (
        select(func.max(precedente.numero))
        .where(precedente.post_id == Post.id)
        .scalar_subquery()
    )
    testi_approvati, come_ai = db.execute(
        select(
            func.count(),
            func.coalesce(
                func.sum(
                    case((VersionePost.tipo_intervento.in_(INTERVENTI_DELL_AI), 1))
                ),
                0,
            ),
        )
        .select_from(Post)
        .join(
            VersionePost,
            and_(VersionePost.post_id == Post.id, VersionePost.numero == ultima),
        )
        .where(post_delle_campagne, Post.stato.in_(STATI_APPROVATI))
    ).one()

    per_tipo = dict(
        db.execute(
            select(VersionePost.tipo_intervento, func.count())
            .join(Post, Post.id == VersionePost.post_id)
            .where(post_delle_campagne)
            .group_by(VersionePost.tipo_intervento)
        ).all()
    )
    non_create = db.scalar(
        select(func.count(func.distinct(VersionePost.post_id)))
        .join(Post, Post.id == VersionePost.post_id)
        .where(
            post_delle_campagne,
            VersionePost.errori_validazione.contains([{"regola": IMMAGINE_NON_CREATA}]),
        )
    )

    return NumeriAI(
        chiamate=chiamate,
        costo_usd=Decimal(costo),
        durata_media_ms=None if media is None else round(media),
        durata_p95_ms=None if p95 is None else round(p95),
        tasso_errore=errori / chiamate if chiamate else 0.0,
        voto_medio=_voto(voto_medio),
        testi_approvati=testi_approvati,
        testi_approvati_come_ai=come_ai,
        modifiche_a_mano=per_tipo.get("modifica_operatore", 0),
        rigenerazioni_testo=sum(per_tipo.get(t, 0) for t in RIGENERAZIONI_TESTO),
        immagini_create=immagini_create or 0,
        immagini_non_create=non_create or 0,
        immagini_rigenerate=per_tipo.get("rigenera_immagine", 0),
        per_versione=per_versione,
    )
