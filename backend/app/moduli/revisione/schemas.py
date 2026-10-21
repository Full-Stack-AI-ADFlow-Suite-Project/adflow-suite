"""Schemi delle risposte di ``GET /campagne/{id}/post`` (plan §3, spec §2.3)
e dei corpi delle richieste degli interventi sul post (T2b-42)."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class PostModifica(BaseModel):
    """Corpo di ``POST /post/{id}/modifica`` (R-30): testo e hashtag nuovi."""

    testo: str
    hashtag: list[str] = []


class PostControllato(BaseModel):
    """Corpo di ``POST /post/{id}/controllato``: la spunta «va bene» (R-30)."""

    valore: bool


class PostRigenera(BaseModel):
    """Corpo di ``POST /post/{id}/rigenera`` (R-03, R-31).

    ``totale`` riscrive da zero; ``da_proposta`` parte dal testo scritto
    dall'operatore, obbligatorio in quel caso (422).
    """

    modalita: Literal["totale", "da_proposta"]
    testo_proposto: str | None = None
    nota: str | None = None


class PostRiprogramma(BaseModel):
    """Corpo di ``POST /post/{id}/riprogramma`` (R-34): la nuova data e ora."""

    data_ora: datetime


class PostSposta(BaseModel):
    """Corpo di ``POST /post/{id}/sposta`` (R-36): la nuova data e ora."""

    model_config = ConfigDict(extra="forbid")

    data_ora: datetime


class PostAnnulla(BaseModel):
    """Corpo di ``POST /post/{id}/annulla`` (R-36): la nota è obbligatoria."""

    model_config = ConfigDict(extra="forbid")

    nota: str = Field(min_length=1)


class PostCambiaFoto(BaseModel):
    """Corpo di ``POST /post/{id}/cambia-foto`` (R-36): la foto scelta."""

    model_config = ConfigDict(extra="forbid")

    foto_id: int


class FotoPossibile(BaseModel):
    """Una foto con cui si può cambiare quella del post (R-36)."""

    foto_id: int
    punteggio: float | None
    # Falso: arrivata con una richiesta all'artigiano, senza analisi (R-46).
    analizzata: bool


class CampagnaSchema(BaseModel):
    """La campagna come la legge l'operatore in Vedi campagna."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    profilo_id: int
    titolo: str
    inizio: date
    fine: date
    descrizione: str | None
    stato: str
    canali: list[str] | None
    canali_tolti: list[str] | None
    frequenza: str | None
    obiettivo: str | None
    inviata_il: datetime | None
    chiusa_il: datetime | None


class PianoSchema(BaseModel):
    """Il piano corrente: strategia, esito del controllo e debolezza (R-20)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    numero: int
    strategia: str
    esito_controllo: dict[str, Any] | list[Any] | None
    debole: bool
    creata_il: datetime


class FotoLegataSchema(BaseModel):
    """Una foto legata a una versione, nella sua posizione."""

    foto_id: int
    posizione: int


class VersionePostSchema(BaseModel):
    """Una versione del post con autore, foto e risultati del validatore."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    numero: int
    testo: str
    hashtag: list[str]
    autore_id: int | None
    tipo_intervento: str
    testo_proposto: str | None
    nota: str | None
    provider_ai: str | None
    modello_ai: str | None
    versione_prompt: str | None
    errori_validazione: dict[str, Any] | list[Any] | None
    creata_il: datetime
    foto: list[FotoLegataSchema]


class PostSchema(BaseModel):
    """Un post con tipo di riempitivo, versione corrente e storico."""

    post_id: int
    canale: str
    formato: str
    riempitivo: str | None
    data_ora: datetime
    stato: str
    da_rivedere: bool
    controllato_da: int | None
    controllato_il: datetime | None
    intervento_in_corso: str | None
    intervento_dal: datetime | None
    versione_corrente: VersionePostSchema | None
    versioni: list[VersionePostSchema]
    # Gli interventi che l'operatore può fare adesso (R-16): valori di INTERVENTI.
    interventi: list[str] = []


class GruppoSchema(BaseModel):
    """Il gruppo di un'uscita o delle foto non usate."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    origine: str
    descrizione: str | None
    da_usare_il: date | None


class UscitaSchema(BaseModel):
    """Un'uscita con il suo gruppo e i post dei canali."""

    id: int
    numero: int
    tema: str
    gruppo: GruppoSchema | None
    post: list[PostSchema]


class FotoNonUsataSchema(BaseModel):
    """Una foto che il piano non usa, con il motivo dell'analisi."""

    foto_id: int
    motivo: str | None


class GruppoFotoNonUsateSchema(BaseModel):
    """Le foto non usate di un gruppo; ``gruppo_id`` nullo per le cartoline."""

    gruppo_id: int | None
    descrizione: str | None
    foto: list[FotoNonUsataSchema]


class ErroreSchema(BaseModel):
    """L'ultimo errore della generazione (R-35)."""

    model_config = ConfigDict(from_attributes=True)

    tipo: str
    messaggio: str
    tappa: str
    canale: str | None
    creata_il: datetime


class VediCampagnaSchema(BaseModel):
    """Risposta completa di Vedi campagna in ogni stato dopo l'invio."""

    campagna: CampagnaSchema
    piano: PianoSchema | None
    uscite: list[UscitaSchema]
    foto_non_usate: list[GruppoFotoNonUsateSchema]
    ultimo_errore: ErroreSchema | None
    # Totale in dollari delle chiamate all'AI della campagna (R-44)
    costo_ai: Decimal


class ConteggiPost(BaseModel):
    """Conteggi dei post di una campagna in «Campagne da approvare» (plan §3)."""

    totale: int
    da_approvare: int
    da_rivedere: int
    riempitivi: dict[str, int] = {}


class CampagnaDaApprovare(BaseModel):
    """Una riga di ``GET /da-approvare`` (R-38): conteggi, entro quando, ultima nota."""

    id: int
    profilo_id: int
    titolo: str
    inizio: date
    fine: date
    stato: str
    canali: list[str] | None = None
    bottega: str | None = None
    citta: str | None = None
    conteggi: ConteggiPost | None = None
    entro_quando: datetime | None = None
    ultima_nota: str | None = None
    # Richiesta all'artigiano (R-46): "aperta", "inviata" o None.
    richiesta: str | None = None


class ArtigianoElenco(BaseModel):
    """Una riga di ``GET /artigiani``: la bottega con la sua situazione."""

    id: int
    email: str
    nome: str
    attivo: bool
    profilo_id: int | None = None
    # ``bottega`` nullo: l'artigiano non ha ancora compilato il profilo.
    bottega: str | None = None
    citta: str | None = None
    tipo_prodotto: str | None = None
    canali_collegati: list[str] = []
    n_da_approvare: int = 0
    n_in_corso: int = 0
    # ``entro_quando`` più vicino tra le campagne da approvare (R-38).
    prossima_scadenza: datetime | None = None
    prossima_campagna_id: int | None = None


class UtenteArtigiano(BaseModel):
    """L'account di accesso dell'artigiano, nella sua scheda."""

    id: int
    email: str
    nome: str
    attivo: bool


class ProfiloArtigiano(BaseModel):
    """Il profilo della bottega in sola lettura, nella scheda artigiano."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    referente: str
    citta: str
    tipo_prodotto: str
    clienti_ideali: str
    obiettivo: str
    canali: list[str]
    anni_attivita: int | None = None
    sito: str | None = None
    storia: str | None = None
    origine: str | None = None
    valori: list[str] | None = None
    gamma: str | None = None
    fascia_prezzo: str | None = None
    stagionalita: str | None = None
    zona: str | None = None
    tono: list[str] | None = None
    cortesia: str | None = None
    vincoli: str | None = None
    frequenza: str | None = None
    orari: dict[str, Any] | list[Any] | None = None
    social_esistenti: dict[str, Any] | None = None
    foto_policy: dict[str, Any] | None = None
    eventi_ricorrenti: list[dict[str, Any]] | None = None
    chiusure: str | None = None
    aggiornato_il: datetime


class CampagnaSezione(BaseModel):
    """Una campagna nelle sezioni «in corso» e «chiuse» della scheda."""

    id: int
    titolo: str
    stato: str
    inizio: date
    fine: date
    canali: list[str] | None = None
    inviata_il: datetime | None = None
    chiusa_il: datetime | None = None
    n_post: int = 0
    n_pubblicati: int = 0
    n_falliti: int = 0
    n_foto: int = 0


class SchedaArtigiano(BaseModel):
    """Risposta di ``GET /artigiani/{id}``: il dettaglio per sezioni (plan §3).

    ``da_approvare`` porta le stesse righe di ``GET /da-approvare``; ``chiuse``
    sono le ultime tre, con il totale in ``totale_chiuse``.
    """

    artigiano: UtenteArtigiano
    profilo: ProfiloArtigiano | None
    canali_collegati: list[str] = []
    bozza: CampagnaSezione | None = None
    da_approvare: list[CampagnaDaApprovare] = []
    in_corso: list[CampagnaSezione] = []
    chiuse: list[CampagnaSezione] = []
    totale_chiuse: int = 0


class CampagnaNota(BaseModel):
    """Corpo di ``POST /campagne/{id}/nota``: la nota interna (R-32)."""

    model_config = ConfigDict(extra="forbid")

    nota: str = Field(min_length=1)


class CampagnaRespingi(BaseModel):
    """Corpo di ``POST /campagne/{id}/respingi`` (R-18, CA-24, CA-25)."""

    model_config = ConfigDict(extra="forbid")

    motivo: Literal["foto", "altro"]
    nota: str = Field(min_length=1)
    foto_segnate: list[int] = []


class CampagnaTogliCanale(BaseModel):
    """Corpo di ``POST /campagne/{id}/togli-canale`` (CA-53)."""

    model_config = ConfigDict(extra="forbid")

    canale: str
    nota: str = Field(min_length=1)


class CampagnaSospendi(BaseModel):
    """Corpo facoltativo di ``POST /campagne/{id}/sospendi``: la nota (R-33)."""

    model_config = ConfigDict(extra="forbid")

    nota: str | None = None


class CampagnaRiattiva(BaseModel):
    """Corpo di ``POST /campagne/{id}/riattiva`` (plan §3, R-33).

    ``pubblica_ora``: gli id dei post approvati in arretrato che escono
    subito; gli altri arretrati diventano ``annullato``.
    """

    model_config = ConfigDict(extra="forbid")

    pubblica_ora: list[int] = []
