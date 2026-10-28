"""Risposta pubblica del calendario: contenuti approvati, senza note interne."""
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


class FotoCalendario(BaseModel):
    id: int
    url: str
    mime: str
    larghezza: int
    altezza: int
    origine: str


class PostCalendario(BaseModel):
    id: int
    data_ora: datetime
    ora: str
    canale: str
    stato: str
    testo: str
    hashtag: list[str]
    foto: list[FotoCalendario]


class GiornoCalendario(BaseModel):
    data: date
    post: list[PostCalendario]


class PostSettimana(PostCalendario):
    """Un post del calendario settimanale (spec R-48)."""

    campagna_id: int
    campagna_titolo: str
    bottega: str | None


class GiornoSettimana(BaseModel):
    data: date
    post: list[PostSettimana]


class CalendarioSettimana(BaseModel):
    dal: date  # lunedì
    al: date  # domenica
    giorni: list[GiornoSettimana]  # sempre 7, anche vuoti


class CanaleToltoCalendario(BaseModel):
    canale: str
    nota: str | None


class CalendarioCampagna(BaseModel):
    campagna_id: int
    strategia: str | None
    giorni: list[GiornoCalendario]
    canali_tolti: list[CanaleToltoCalendario]
    n_post_scaduti: int


class ChiamateAIDiUnTipo(BaseModel):
    """Le chiamate all'AI di un tipo (analisi, piano, testo, immagine) e ciò che sono costate."""

    tipo: str
    chiamate: int
    modelli: list[str]
    token_ingresso: int
    token_uscita: int
    immagini: int
    costo_usd: Decimal


class PostSegnalato(BaseModel):
    """Un post la cui versione corrente ha blocchi o avvisi del validatore."""

    post_id: int
    canale: str
    data_ora: datetime
    con_blocco: bool
    segnalazioni: list[str]


class RiepilogoAI(BaseModel):
    """Che cosa ha fatto e speso l'AI per una campagna (spec R-44, prova di T3-32)."""

    campagna_id: int
    per_tipo: list[ChiamateAIDiUnTipo]
    costo_totale_usd: Decimal
    n_post: int
    riscritture_piano: int
    riscritture_testi: int
    post_segnalati: list[PostSegnalato]


# --- Storico dell'AI (spec R-50) --------------------------------------------


class ChiamataAIRiga(BaseModel):
    id: int
    creata_il: datetime
    campagna_id: int
    campagna_titolo: str
    bottega: str | None
    post_id: int | None
    foto_id: int | None
    tipo: str  # analisi · piano · testo · immagine
    modello_ai: str
    versione_prompt: str | None
    esito: str  # ESITI_CHIAMATA_AI
    durata_ms: int | None
    costo_usd: Decimal
    token_ingresso: int | None
    token_uscita: int | None
    voto_medio: float | None


class ValutazioneAISchema(BaseModel):
    id: int
    utente_nome: str
    voto: int
    nota: str | None
    creata_il: datetime


class ChiamataAIDettaglio(ChiamataAIRiga):
    richiesta: dict | None
    risposta: str | None
    errore: str | None
    tentativo: int | None
    valutazioni: list[ValutazioneAISchema]


class PaginaChiamateAI(BaseModel):
    voci: list[ChiamataAIRiga]  # dalla più recente
    totale: int
    pagina: int
    per_pagina: int  # 50


class NumeriVersione(BaseModel):
    tipo: str
    versione_prompt: str | None
    chiamate: int
    tasso_errore: float  # 0–1
    durata_media_ms: int | None
    costo_usd: Decimal
    voto_medio: float | None


class NumeriAI(BaseModel):
    chiamate: int
    costo_usd: Decimal
    durata_media_ms: int | None
    durata_p95_ms: int | None
    tasso_errore: float
    voto_medio: float | None
    testi_approvati: int  # post approvati, pubblicati, falliti o annullati
    testi_approvati_come_ai: int  # di questi, con la versione corrente scritta dall'AI
    modifiche_a_mano: int  # versioni modifica_operatore
    rigenerazioni_testo: int  # versioni rigenera_totale e rigenera_da_proposta
    immagini_create: int
    immagini_non_create: int  # post con il blocco immagine_non_creata
    immagini_rigenerate: int  # versioni rigenera_immagine
    per_versione: list[NumeriVersione]
