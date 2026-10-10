"""Logica e regole di modifica della bozza di campagna (T2a-21)."""

from datetime import datetime, timedelta

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.config import leggi_impostazioni
from app.core.errori import DatiNonValidi, NonTrovato, StatoNonValido
from app.core.orologio import ROMA
from app.moduli.artigiani import service as artigiani_service
from app.moduli.campagne.domain import BOZZA, STATI_CHIUSI
from app.moduli.campagne.models import Campagna, GruppoFoto
from app.moduli.campagne.schemas import CampagnaModifica


def modifica_bozza(
    db: Session,
    utente_id: int,
    campagna_id: int,
    dati: CampagnaModifica,
    ora: datetime,
) -> Campagna:
    """Modifica una campagna nello stato bozza per l'artigiano autenticato.

    Verifica le regole di pianificazione R-08, i vincoli temporali e di unicità R-12,
    la presenza dei canali collegati R-22 e il vincolo sulle date dei gruppi R-13
    (CA-08, CA-09, CA-10, CA-48, fuori dalla bozza -> 409).
    """
    profilo = artigiani_service.profilo_di(db, utente_id)
    if profilo is None:
        raise NonTrovato("Campagna non trovata.")

    # Concorrenza atomica: lock di transazione sull'artigiano per serializzare richieste concorrenti (Regola 4)
    db.execute(text("SELECT pg_advisory_xact_lock(:chiave)"), {"chiave": profilo.id})

    campagna = db.get(Campagna, campagna_id)
    if campagna is None or campagna.profilo_id != profilo.id:
        raise NonTrovato("Campagna non trovata.")

    # Solo in bozza (T2a-21, 409 fuori dalla bozza)
    if campagna.stato != BOZZA:
        raise StatoNonValido(
            "La campagna può essere modificata solo quando è in bozza."
        )

    # Calcolo valori effettivi
    nuovo_titolo = (
        dati.titolo
        if "titolo" in dati.model_fields_set and dati.titolo is not None
        else campagna.titolo
    )
    nuova_descrizione = (
        dati.descrizione
        if "descrizione" in dati.model_fields_set
        else campagna.descrizione
    )
    nuovo_inizio = (
        dati.inizio
        if "inizio" in dati.model_fields_set and dati.inizio is not None
        else campagna.inizio
    )
    nuovo_fine = (
        dati.fine
        if "fine" in dati.model_fields_set and dati.fine is not None
        else campagna.fine
    )
    nuovi_canali = (
        dati.canali
        if "canali" in dati.model_fields_set and dati.canali is not None
        else list(campagna.canali or [])
    )

    # R-22, CA-48: solo canali con account collegato
    if not nuovi_canali:
        raise DatiNonValidi("Selezionare almeno un canale.")

    collegati = set(artigiani_service.canali_collegati(db, profilo.id))
    non_collegati = [c for c in nuovi_canali if c not in collegati]
    if non_collegati:
        raise DatiNonValidi(
            f"I seguenti canali non sono collegati: {', '.join(non_collegati)}."
        )

    # R-08, CA-09: inizio >= oggi + anticipo minimo
    oggi = ora.astimezone(ROMA).date() if ora.tzinfo else ora.date()
    impostazioni = leggi_impostazioni()
    anticipo_minimo = timedelta(days=impostazioni.anticipo_minimo_giorni)

    if nuovo_inizio < oggi + anticipo_minimo:
        raise DatiNonValidi(
            "La data di inizio deve essere ad almeno "
            f"{impostazioni.anticipo_minimo_giorni} giorni da oggi."
        )

    # R-08, CA-10: fine > inizio e durata tra 7 e 92 giorni
    if nuovo_fine <= nuovo_inizio:
        raise DatiNonValidi(
            "La data di fine deve essere successiva alla data di inizio."
        )

    durata = (nuovo_fine - nuovo_inizio).days + 1
    if durata < 7:
        raise DatiNonValidi("La durata della campagna deve essere di almeno 7 giorni.")
    if durata > 92:
        raise DatiNonValidi("La durata della campagna non può superare 92 giorni.")

    # R-12, CA-12: campagne non chiuse non sovrapposte (esclusa la campagna corrente)
    campagna_sovrapposta = db.scalar(
        select(Campagna.id).where(
            Campagna.profilo_id == profilo.id,
            Campagna.stato.not_in(STATI_CHIUSI),
            Campagna.id != campagna.id,
            Campagna.inizio <= nuovo_fine,
            Campagna.fine >= nuovo_inizio,
        )
    )
    if campagna_sovrapposta is not None:
        raise StatoNonValido("Il periodo si sovrappone a una campagna già esistente.")

    # R-13, T2a-21: se la data di un gruppo esce dal nuovo periodo -> 422
    gruppi = list(
        db.scalars(select(GruppoFoto).where(GruppoFoto.campagna_id == campagna.id))
    )
    for g in gruppi:
        if g.da_usare_il is not None:
            if g.da_usare_il < nuovo_inizio or g.da_usare_il > nuovo_fine:
                raise DatiNonValidi(
                    f"La data di utilizzo del gruppo ({g.da_usare_il}) esce dal nuovo periodo della campagna."
                )

    # Aggiornamento dati campagna
    campagna.titolo = nuovo_titolo
    campagna.inizio = nuovo_inizio
    campagna.fine = nuovo_fine
    campagna.descrizione = nuova_descrizione
    campagna.canali = list(nuovi_canali)

    db.flush()
    return campagna
