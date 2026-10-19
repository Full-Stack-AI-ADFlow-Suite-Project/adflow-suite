"""Schemi Pydantic per il modulo campagne (richieste e risposte API)."""

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


def testo_valido(testo: str, *, campo_postgres: bool = True) -> bool:
    """Verifica che il testo sia UTF-8 valido e senza byte NUL per PostgreSQL."""
    if campo_postgres and "\x00" in testo:
        return False
    try:
        testo.encode("utf-8")
    except UnicodeEncodeError:
        return False
    return True


class CampagnaCrea(BaseModel):
    """Payload per la creazione di una nuova bozza di campagna (POST /campagne)."""

    titolo: str = Field(min_length=1, max_length=200)
    inizio: date
    fine: date
    descrizione: str | None = Field(default=None, max_length=2000)
    canali: list[str] = Field(min_length=1)

    @field_validator("titolo")
    @classmethod
    def valida_titolo(cls, valore: str) -> str:
        pulito = valore.strip()
        if not pulito:
            raise ValueError("Il titolo non può essere vuoto.")
        if not testo_valido(pulito):
            raise ValueError("Il titolo contiene caratteri non validi.")
        return pulito

    @field_validator("descrizione")
    @classmethod
    def valida_descrizione(cls, valore: str | None) -> str | None:
        if valore is None:
            return None
        pulito = valore.strip()
        if not pulito:
            return None
        if not testo_valido(pulito):
            raise ValueError("La descrizione contiene caratteri non validi.")
        return pulito

    @field_validator("canali")
    @classmethod
    def valida_canali(cls, canali: list[str]) -> list[str]:
        if not canali:
            raise ValueError("Selezionare almeno un canale.")
        # Quali canali esistono lo sa artigiani: il service ammette solo quelli collegati
        visti = []
        for c in canali:
            c_norm = c.strip().lower()
            if c_norm not in visti:
                visti.append(c_norm)
        return visti


class CampagnaModifica(BaseModel):
    """Payload per la modifica di una bozza di campagna (PATCH /campagne/{id}).

    Tutti i campi sono opzionali. I campi non specificati mantengono il valore corrente.
    """

    titolo: str | None = Field(default=None, min_length=1, max_length=200)
    inizio: date | None = None
    fine: date | None = None
    descrizione: str | None = Field(default=None, max_length=2000)
    canali: list[str] | None = None

    @field_validator("titolo")
    @classmethod
    def valida_titolo(cls, valore: str | None) -> str | None:
        if valore is None:
            return None
        pulito = valore.strip()
        if not pulito:
            raise ValueError("Il titolo non può essere vuoto.")
        if not testo_valido(pulito):
            raise ValueError("Il titolo contiene caratteri non validi.")
        return pulito

    @field_validator("descrizione")
    @classmethod
    def valida_descrizione(cls, valore: str | None) -> str | None:
        if valore is None:
            return None
        pulito = valore.strip()
        if not pulito:
            return None
        if not testo_valido(pulito):
            raise ValueError("La descrizione contiene caratteri non validi.")
        return pulito

    @field_validator("canali")
    @classmethod
    def valida_canali(cls, canali: list[str] | None) -> list[str] | None:
        if canali is None:
            return None
        if not canali:
            raise ValueError("Selezionare almeno un canale.")
        visti = []
        for c in canali:
            c_norm = c.strip().lower()
            if c_norm not in visti:
                visti.append(c_norm)
        if not visti:
            raise ValueError("Selezionare almeno un canale.")
        return visti


class CampagnaInvia(BaseModel):
    """Payload per l'invio della campagna (POST /campagne/{id}/invia)."""

    dichiarazione: bool = False


class FotoSintetica(BaseModel):
    """Rappresentazione essenziale di una foto nel dettaglio della campagna."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    gruppo_id: int | None = None
    file: str
    mime: str
    larghezza: int
    altezza: int
    origine: str = "caricata"


class GruppoSintetico(BaseModel):
    """Rappresentazione sintetica di un gruppo di foto nel dettaglio della campagna."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    origine: str
    descrizione: str | None = None
    da_usare_il: date | None = None
    n_immagini: int | None = None
    foto: list[FotoSintetica] = []


class DecisioneSintetica(BaseModel):
    """Decisione dell'operatore sulla campagna (consultabile da operatore/admin)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    esito: str
    canale: str | None = None
    post_id: int | None = None
    motivo: str | None = None
    nota: str | None = None


class EsitoRespinta(BaseModel):
    """Ciò che l'artigiano legge di una campagna respinta (spec §4, R-18)."""

    motivo: str
    nota: str | None = None
    foto_segnate: list[int] = []


class RichiestaCrea(BaseModel):
    """Corpo di ``POST /campagne/{id}/richiesta`` (R-46): la domanda e le foto da sostituire."""

    model_config = ConfigDict(extra="forbid")

    domanda: str
    foto: list[int] = []


class RichiestaInvia(BaseModel):
    """Corpo facoltativo di ``POST /campagne/{id}/richiesta/invia`` (R-46)."""

    model_config = ConfigDict(extra="forbid")

    risposta: str | None = None


class FotoDaSostituire(BaseModel):
    """Una foto segnata da sostituire e, se l'artigiano l'ha caricata, la sua nuova."""

    foto_id: int
    gruppo_id: int | None
    nuova_foto_id: int | None = None


class RichiestaArtigiano(BaseModel):
    """La richiesta del consorzio all'artigiano, ricavata dalle decisioni (R-46)."""

    stato: Literal["aperta", "inviata", "decaduta"]
    domanda: str
    creata_il: datetime
    foto: list[FotoDaSostituire]
    risposta: str | None = None
    inviata_il: datetime | None = None


class CampagnaDettaglio(BaseModel):
    """Dettaglio completo di una campagna (GET /campagne/{id})."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    profilo_id: int
    titolo: str
    inizio: date
    fine: date
    descrizione: str | None = None
    stato: str
    canali: list[str] | None = None
    canali_tolti: list[str] | None = None
    frequenza: str | None = None
    obiettivo: str | None = None
    inviata_il: datetime | None = None
    chiusa_il: datetime | None = None
    gruppi: list[GruppoSintetico] = []
    post_chiesti_per_canale: dict[str, int] = {}
    avvisi: list[str] = []
    profilo_snapshot: dict[str, Any] | list[Any] | None = None
    decisioni: list[DecisioneSintetica] = []
    esito_respinta: EsitoRespinta | None = None
    richiesta: RichiestaArtigiano | None = None


class CampagnaElencoItem(BaseModel):
    """Elemento sintetico per la lista delle campagne (GET /campagne)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    profilo_id: int
    titolo: str
    inizio: date
    fine: date
    stato: str
    canali: list[str] | None = None
    bottega: str | None = None
    citta: str | None = None
    # Stato della richiesta del consorzio, solo nell'elenco dell'artigiano (R-46).
    richiesta: str | None = None


class GruppoArchivioCrea(BaseModel):
    """Payload per la creazione di un gruppo nell'archivio della bottega (POST /archivio/gruppi)."""

    descrizione: str = Field(min_length=1, max_length=2000)

    @field_validator("descrizione")
    @classmethod
    def valida_descrizione(cls, valore: str) -> str:
        pulito = valore.strip()
        if not pulito:
            raise ValueError("La descrizione non può essere vuota.")
        if not testo_valido(pulito):
            raise ValueError("La descrizione contiene caratteri non validi.")
        return pulito


class GruppoCrea(BaseModel):
    """Payload per la creazione di un gruppo di foto (POST /campagne/{id}/gruppi)."""

    origine: str = Field(default="caricate")
    descrizione: str | None = Field(default=None, max_length=2000)
    da_usare_il: date | None = None
    n_immagini: int | None = None

    @field_validator("origine")
    @classmethod
    def valida_origine(cls, v: str) -> str:
        v_norm = v.strip().lower()
        if v_norm not in ("caricate", "create_ai"):
            raise ValueError(
                "Origine del gruppo non valida (ammesse: 'caricate', 'create_ai')."
            )
        return v_norm

    @field_validator("descrizione")
    @classmethod
    def valida_descrizione(cls, v: str | None) -> str | None:
        if v is None:
            return None
        pulito = v.strip()
        if not pulito:
            raise ValueError("La descrizione del gruppo non può essere vuota.")
        if not testo_valido(pulito):
            raise ValueError("La descrizione del gruppo contiene caratteri non validi.")
        return pulito

    @field_validator("n_immagini")
    @classmethod
    def valida_n_immagini(cls, v: int | None) -> int | None:
        if v is not None and (v < 1 or v > 20):
            raise ValueError("n_immagini deve essere compreso tra 1 e 20.")
        return v


class GruppoAggiorna(BaseModel):
    """Payload per l'aggiornamento di un gruppo di foto (PUT /campagne/{id}/gruppi/{gruppo_id})."""

    descrizione: str | None = Field(default=None, max_length=2000)
    da_usare_il: date | None = None
    n_immagini: int | None = None

    @field_validator("descrizione")
    @classmethod
    def valida_descrizione(cls, v: str | None) -> str | None:
        if v is None:
            return None
        pulito = v.strip()
        if not pulito:
            raise ValueError("La descrizione del gruppo non può essere vuota.")
        if not testo_valido(pulito):
            raise ValueError("La descrizione del gruppo contiene caratteri non validi.")
        return pulito

    @field_validator("n_immagini")
    @classmethod
    def valida_n_immagini(cls, v: int | None) -> int | None:
        if v is not None and (v < 1 or v > 20):
            raise ValueError("n_immagini deve essere compreso tra 1 e 20.")
        return v


class GruppoDettaglio(BaseModel):
    """Rappresentazione di un gruppo di foto nel dettaglio o come risultato di creazione."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    profilo_id: int
    campagna_id: int | None = None
    origine: str
    descrizione: str | None = None
    da_usare_il: date | None = None
    n_immagini: int | None = None
    foto: list[FotoSintetica] = []


class FotoDettaglio(BaseModel):
    """Rappresentazione completa di una foto appena caricata o consultata."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    profilo_id: int
    campagna_id: int | None = None
    gruppo_id: int | None = None
    origine: str
    file: str
    mime: str
    larghezza: int
    altezza: int
    n_utilizzi: int = 0
