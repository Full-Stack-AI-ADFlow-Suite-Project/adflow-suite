"""Logica del modulo campagne: l'unica parte che gli altri moduli possono importare."""

from collections.abc import Callable
from copy import deepcopy
from datetime import date, datetime, timedelta
import json
import logging
from typing import Any

from sqlalchemy import event, func, select, text
from sqlalchemy.orm import Session, selectinload

from app.adapters.archivio import ottieni_archivio
from app.core import coda, orologio
from app.core.config import leggi_impostazioni
from app.core.errori import DatiNonValidi, NonPermesso, NonTrovato, StatoNonValido
from app.core.orologio import ROMA
from app.core.transizioni import verifica_transizione
from app.moduli.artigiani import service as artigiani_service

from .domain import (
    BOZZA,
    GENERAZIONE_FALLITA,
    INVIATA,
    ESITI_DECISIONE,
    ESITO_RESPINTA,
    MOTIVI_DECISIONE,
    ORIGINI_FOTO,
    ORIGINI_GRUPPO,
    STATI,
    STATI_CHIUSI,
    TRANSIZIONI,
)
from .immagini import MAX_FOTO_PER_GRUPPO, analizza_e_valida_immagine
from .models import Campagna, DecisioneCampagna, Foto, GruppoFoto
from .schemas import (
    CampagnaCrea,
    CampagnaDettaglio,
    CampagnaElencoItem,
    DecisioneSintetica,
    FotoSintetica,
    GruppoAggiorna,
    GruppoCrea,
    GruppoSintetico,
)

# R-25: massimo di post al mese per fascia di `foto_policy.quantita_mese`
LIMITI_POLICY_FOTO = {"meno_5": 4, "da5_a12": 12, "da12_a20": 20}
logger = logging.getLogger(__name__)


def campagna(
    db: Session,
    id: int,
) -> Campagna:
    """Restituisce la campagna con l'id indicato.

    Usata da ``contenuti``, ``revisione`` e ``pubblicazione``.
    Solleva ``NonTrovato`` invece di restituire ``None`` perché chi
    chiama questa funzione conosce già l'id e si aspetta che esista.

    Args:
        db: sessione del database (aperta e chiusa dal chiamante).
        id: chiave primaria della campagna.

    Returns:
        Il record ``Campagna`` corrispondente.

    Raises:
        NonTrovato: se non esiste nessuna campagna con quell'id.
    """
    trovata = db.get(Campagna, id)
    if trovata is None:
        raise NonTrovato("Campagna non trovata.")
    return trovata


def foto_della_campagna(
    db: Session,
    id: int,
) -> list[Foto]:
    """Restituisce tutte le foto associate alla campagna indicata.

    Usata da ``contenuti`` (analisi AI), ``revisione`` e ``pubblicazione``.
    Restituisce una lista vuota se la campagna non ha foto, senza sollevare
    eccezioni: la presenza di foto è verificata altrove (es. prima dell'invio).

    Args:
        db: sessione del database (aperta e chiusa dal chiamante).
        id: chiave primaria della campagna.

    Returns:
        Lista di record ``Foto``, vuota se la campagna non ne ha.
    """
    return list(
        db.scalars(select(Foto).where(Foto.campagna_id == id).order_by(Foto.id))
    )


def campagne_in_stato(
    db: Session,
    stati: list[str],
) -> list[Campagna]:
    """Restituisce tutte le campagne che si trovano in uno degli stati indicati.

    Usata da ``contenuti``, ``revisione`` e ``pubblicazione`` per ottenere
    le campagne su cui agire (es. tutte le ``in_revisione`` da mostrare
    all'operatore). Accetta una lista per permettere query multi-stato
    con una sola chiamata al database.

    Args:
        db: sessione del database (aperta e chiusa dal chiamante).
        stati: lista di stati validi (es. ``["in_revisione", "attiva"]``).
               Gli stati ammessi sono definiti in ``campagne/domain.py``.

    Returns:
        Lista di record ``Campagna``, vuota se nessuna corrisponde.
    """
    return list(
        db.scalars(
            select(Campagna).where(Campagna.stato.in_(stati)).order_by(Campagna.id)
        )
    )


def cambia_stato(
    db: Session,
    campagna: Campagna,
    nuovo: str,
    *,
    ora: datetime | None = None,
) -> None:
    """Aggiorna lo stato della campagna verificando che la transizione sia ammessa.

    È l'unico punto del sistema in cui lo stato di una campagna cambia
    (constitution §2.4 e §1.8). Internamente chiama ``verifica_transizione``
    con il dizionario delle transizioni di ``campagne/domain.py``.
    Nessun altro modulo deve modificare ``campagna.stato`` direttamente.

    Args:
        db: sessione del database (aperta e chiusa dal chiamante).
        campagna: il record ``Campagna`` da aggiornare (già caricato in sessione).
        nuovo: lo stato di destinazione (es. ``"inviata"``).
        ora: istante di chiusura iniettato; se assente usa ``core.orologio.adesso``.

    Raises:
        StatoNonValido: se la transizione da stato attuale a ``nuovo`` non è
            ammessa dal diagramma di ``campagne/domain.py``.
    """
    verifica_transizione(TRANSIZIONI, campagna.stato, nuovo)
    campagna.stato = nuovo
    if nuovo in STATI_CHIUSI:
        campagna.chiusa_il = ora if ora is not None else orologio.adesso()
    db.flush()


def registra_decisione(
    db: Session,
    campagna: Campagna,
    utente_id: int,
    esito: str,
    motivo: str | None,
    nota: str | None,
    foto_segnate: list[int],
    canale: str | None = None,
    post_id: int | None = None,
) -> None:
    """Scrive una riga nella tabella ``decisione_campagna``.

    Usata da ``revisione`` dopo ogni approvazione, nota o respinta.
    Le decisioni non si cancellano mai (constitution §1.2): questa funzione
    crea sempre un nuovo record, non aggiorna quelli esistenti.

    Args:
        db: sessione del database (aperta e chiusa dal chiamante).
        campagna: il record ``Campagna`` a cui appartiene la decisione.
        utente_id: id dell'operatore che ha preso la decisione.
        esito: uno degli esiti di ``domain.ESITI_DECISIONE``.
        motivo: obbligatorio se ``esito`` è ``"respinta"`` (``"foto"`` o
                ``"altro"``), ``None`` altrimenti.
        nota: testo libero dell'operatore; obbligatoria se ``esito`` è
              ``"respinta"``, facoltativa altrimenti.
        foto_segnate: lista di id delle foto segnalate come problematiche,
                      vuota se non applicabile.
        canale: canale tolto, facoltativo (decisione ``canale_tolto``).
        post_id: post riprogrammato, facoltativo (decisione ``riprogrammato``).

    Raises:
        DatiNonValidi: esito o motivo fuori dai valori di ``campagne/domain.py``,
            oppure ``respinta`` senza motivo o senza nota (R-18).
    """
    if esito not in ESITI_DECISIONE:
        raise DatiNonValidi("Esito della decisione non valido.")
    if motivo is not None and motivo not in MOTIVI_DECISIONE:
        raise DatiNonValidi("Motivo della decisione non valido.")
    if esito == ESITO_RESPINTA and (motivo is None or not (nota or "").strip()):
        raise DatiNonValidi("Per respingere servono il motivo e la nota.")
    db.add(
        DecisioneCampagna(
            campagna_id=campagna.id,
            utente_id=utente_id,
            esito=esito,
            motivo=motivo,
            nota=nota,
            foto_segnate=foto_segnate,
            canale=canale,
            post_id=post_id,
        )
    )
    db.flush()


def aggiorna_foto(
    db: Session,
    foto_id: int,
    analisi_ai: dict[str, Any] | None,
    n_utilizzi: int,
) -> None:
    """Aggiorna il risultato dell'analisi AI e il contatore utilizzi di una foto.

    Chiamata da ``contenuti`` durante il job ``genera_campagna``, dopo che
    l'adattatore AI ha analizzato l'immagine. La foto appartiene al modulo
    campagne, quindi solo questo service può modificarla.

    Args:
        db: sessione del database (aperta e chiusa dal chiamante).
        foto_id: chiave primaria della foto da aggiornare.
        analisi_ai: risultato strutturato dell'analisi AI (JSON, come la
                    colonna ``foto.analisi_ai``), o ``None`` se l'analisi
                    non ha prodotto risultati.
        n_utilizzi: numero totale di volte che la foto è stata usata
                    in versioni di post.

    Raises:
        NonTrovato: se non esiste nessuna foto con quell'id.
    """
    foto = db.get(Foto, foto_id)
    if foto is None:
        raise NonTrovato("Foto non trovata.")
    foto.analisi_ai = analisi_ai
    foto.n_utilizzi = n_utilizzi
    db.flush()


def gruppi_della_campagna(db: Session, id: int) -> list[GruppoFoto]:
    """Gruppi della campagna con le foto caricate, senza i gruppi di archivio."""
    return list(
        db.scalars(
            select(GruppoFoto)
            .where(GruppoFoto.campagna_id == id)
            .options(selectinload(GruppoFoto.foto))
            .order_by(GruppoFoto.id)
            .execution_options(populate_existing=True)
        )
    )


def aggiungi_foto(
    db: Session,
    campagna_id: int,
    origine: str,
    file: str,
    mime: str,
    larghezza: int,
    altezza: int,
) -> Foto:
    """Crea una foto senza gruppo per le cartoline, senza commit (plan §6)."""
    proprietaria = campagna(db, campagna_id)
    if origine not in ORIGINI_FOTO:
        raise DatiNonValidi("Origine della foto non valida.")
    record = Foto(
        profilo_id=proprietaria.profilo_id,
        campagna_id=campagna_id,
        gruppo_id=None,
        origine=origine,
        file=file,
        mime=mime,
        larghezza=larghezza,
        altezza=altezza,
    )
    db.add(record)
    db.flush()
    return record


def post_chiesti(post_a_settimana: int, inizio: date, fine: date) -> int:
    """Post chiesti su un canale: post/settimana × giorni ÷ 7, per difetto (R-05).

    Funzione pura, senza ``db`` (plan §6): la usano il dettaglio della campagna
    e ``contenuti`` per i limiti del piano, così la formula è scritta una volta.
    I giorni contano inizio e fine; un periodo rovesciato dà zero.
    """
    giorni = (fine - inizio).days + 1
    return max(0, post_a_settimana * giorni // 7)


def crea_bozza(
    db: Session,
    utente_id: int,
    dati: CampagnaCrea,
    ora: datetime,
) -> Campagna:
    """Crea una nuova campagna nello stato bozza per l'artigiano autenticato.

    Verifica le regole di pianificazione R-08, i vincoli di unicità R-12 e la presenza
    dei canali collegati R-22 (CA-09, CA-10, CA-11, CA-12, CA-48).
    """
    profilo = artigiani_service.profilo_di(db, utente_id)
    if profilo is None:
        raise DatiNonValidi("Profilo bottega non trovato.")

    # Concorrenza atomica: lock di transazione sull'artigiano per serializzare richieste concorrenti
    db.execute(text("SELECT pg_advisory_xact_lock(:chiave)"), {"chiave": profilo.id})

    # R-22, CA-48: solo canali con account collegato (quelli ammessi li conosce artigiani)
    canali_richiesti = dati.canali
    if not canali_richiesti:
        raise DatiNonValidi("Selezionare almeno un canale.")

    collegati = set(artigiani_service.canali_collegati(db, profilo.id))
    non_collegati = [c for c in canali_richiesti if c not in collegati]
    if non_collegati:
        raise DatiNonValidi(
            f"I seguenti canali non sono collegati: {', '.join(non_collegati)}."
        )

    oggi = ora.astimezone(ROMA).date() if ora.tzinfo else ora.date()
    impostazioni = leggi_impostazioni()
    anticipo_minimo = timedelta(days=impostazioni.anticipo_minimo_giorni)

    if dati.inizio < oggi + anticipo_minimo:
        raise DatiNonValidi(
            "La data di inizio deve essere ad almeno "
            f"{impostazioni.anticipo_minimo_giorni} giorni da oggi."
        )

    if dati.fine <= dati.inizio:
        raise DatiNonValidi(
            "La data di fine deve essere successiva alla data di inizio."
        )

    durata = (dati.fine - dati.inizio).days + 1
    if durata < 7:
        raise DatiNonValidi("La durata della campagna deve essere di almeno 7 giorni.")
    if durata > 92:
        raise DatiNonValidi("La durata della campagna non può superare 92 giorni.")

    # R-12, CA-11: una sola bozza per artigiano
    bozza_aperta = db.scalar(
        select(Campagna.id).where(
            Campagna.profilo_id == profilo.id,
            Campagna.stato == BOZZA,
        )
    )
    if bozza_aperta is not None:
        raise StatoNonValido("Esiste già una campagna in bozza per questo artigiano.")

    # R-12, CA-12: campagne non chiuse non sovrapposte
    campagna_sovrapposta = db.scalar(
        select(Campagna.id).where(
            Campagna.profilo_id == profilo.id,
            Campagna.stato.not_in(STATI_CHIUSI),
            Campagna.inizio <= dati.fine,
            Campagna.fine >= dati.inizio,
        )
    )
    if campagna_sovrapposta is not None:
        raise StatoNonValido("Il periodo si sovrappone a una campagna già esistente.")

    nuova = Campagna(
        profilo_id=profilo.id,
        titolo=dati.titolo,
        inizio=dati.inizio,
        fine=dati.fine,
        descrizione=dati.descrizione,
        canali=dati.canali,
        stato=BOZZA,
    )
    db.add(nuova)
    db.flush()
    return nuova


def elenca_campagne(
    db: Session,
    utente_id: int,
    ruolo: str,
    stati: list[str] | None = None,
) -> list[CampagnaElencoItem]:
    """Elenca le campagne accessibili all'utente autenticato.

    L'artigiano visualizza solo le proprie campagne.
    L'operatore e l'admin visualizzano tutte le campagne del consorzio con bottega e città.
    Supporta il filtro ripetibile per stati (CA-54).
    """
    if stati:
        for s in stati:
            if s not in STATI:
                raise DatiNonValidi(f"Stato della campagna non valido: {s}.")

    query = select(Campagna)

    if ruolo == "artigiano":
        profilo = artigiani_service.profilo_di(db, utente_id)
        if profilo is None:
            return []
        query = query.where(Campagna.profilo_id == profilo.id)
    elif ruolo not in ("operatore", "admin"):
        return []

    if stati:
        query = query.where(Campagna.stato.in_(stati))

    campagne = list(db.scalars(query.order_by(Campagna.id.desc())))
    if not campagne:
        return []

    if ruolo in ("operatore", "admin"):
        mappa_profili = {}
        for profilo_id in {c.profilo_id for c in campagne}:
            bottega = artigiani_service.profilo(db, profilo_id)
            if bottega is not None:
                mappa_profili[profilo_id] = (bottega.nome, bottega.citta)
        return [
            CampagnaElencoItem(
                id=c.id,
                profilo_id=c.profilo_id,
                titolo=c.titolo,
                inizio=c.inizio,
                fine=c.fine,
                stato=c.stato,
                canali=c.canali,
                bottega=mappa_profili.get(c.profilo_id, (None, None))[0],
                citta=mappa_profili.get(c.profilo_id, (None, None))[1],
            )
            for c in campagne
        ]

    return [
        CampagnaElencoItem(
            id=c.id,
            profilo_id=c.profilo_id,
            titolo=c.titolo,
            inizio=c.inizio,
            fine=c.fine,
            stato=c.stato,
            canali=c.canali,
            bottega=None,
            citta=None,
        )
        for c in campagne
    ]


def dettaglio_campagna(
    db: Session,
    utente_id: int,
    ruolo: str,
    campagna_id: int,
) -> CampagnaDettaglio:
    """Restituisce il dettaglio della campagna con gruppi, post chiesti e avvisi.

    Se l'utente è un artigiano e la campagna appartiene a un altro artigiano,
    solleva NonTrovato (404) per evitare fuga di informazioni (CA-04).
    Per operatori e admin include anche snapshot e decisioni pregresse.
    """
    rec = db.get(Campagna, campagna_id)
    if rec is None:
        raise NonTrovato("Campagna non trovata.")

    profilo = None
    if ruolo == "artigiano":
        profilo = artigiani_service.profilo_di(db, utente_id)
        if profilo is None or rec.profilo_id != profilo.id:
            raise NonTrovato("Campagna non trovata.")
    elif ruolo not in ("operatore", "admin"):
        raise NonPermesso("Non hai i permessi per visualizzare le campagne.")

    gruppi_db = gruppi_della_campagna(db, campagna_id)
    gruppi_out = [
        GruppoSintetico(
            id=g.id,
            origine=g.origine,
            descrizione=g.descrizione,
            da_usare_il=g.da_usare_il,
            n_immagini=g.n_immagini,
            foto=[
                FotoSintetica(
                    id=f.id,
                    gruppo_id=f.gruppo_id,
                    file=f.file,
                    mime=f.mime,
                    larghezza=f.larghezza,
                    altezza=f.altezza,
                    da_usare=f.da_usare,
                    origine=f.origine,
                )
                for f in g.foto
            ],
        )
        for g in gruppi_db
    ]

    # Calcolo post_chiesti_per_canale secondo spec R-05
    frequenza_val = rec.frequenza
    foto_policy_val = None

    if profilo is None:
        profilo = artigiani_service.profilo(db, rec.profilo_id)
    if profilo is not None:
        if not frequenza_val:
            frequenza_val = profilo.frequenza
        foto_policy_val = profilo.foto_policy

    post_sett = artigiani_service.post_a_settimana(frequenza_val)
    chiesti = post_chiesti(post_sett, rec.inizio, rec.fine)

    canali = rec.canali or []
    post_chiesti_per_canale = {canale: chiesti for canale in canali}

    # Calcolo avvisi informativi (spec R-25, CA-54)
    n_foto_caricate = sum(len(g.foto) for g in gruppi_db if g.origine == "caricate")
    avvisi: list[str] = []
    for _canale in canali:
        if chiesti > 0 and n_foto_caricate < chiesti:
            if "foto_poche" not in avvisi:
                avvisi.append("foto_poche")
        if chiesti > n_foto_caricate and (chiesti - n_foto_caricate) > (
            n_foto_caricate / 2
        ):
            if "riempitivi_molti" not in avvisi:
                avvisi.append("riempitivi_molti")

    if isinstance(foto_policy_val, str):
        try:
            foto_policy_val = json.loads(foto_policy_val)
        except json.JSONDecodeError:
            foto_policy_val = None

    if isinstance(foto_policy_val, dict):
        q_mese = foto_policy_val.get("quantita_mese")
        if q_mese in LIMITI_POLICY_FOTO:
            limite = LIMITI_POLICY_FOTO[q_mese]
            if (post_sett * 4) > limite:
                if "frequenza_alta" not in avvisi:
                    avvisi.append("frequenza_alta")

    snapshot = None
    decisioni = []
    if ruolo in ("operatore", "admin"):
        snapshot = rec.profilo_snapshot
        decisioni_db = list(
            db.scalars(
                select(DecisioneCampagna)
                .where(DecisioneCampagna.campagna_id == campagna_id)
                .order_by(DecisioneCampagna.id)
            )
        )
        decisioni = [DecisioneSintetica.model_validate(d) for d in decisioni_db]

    return CampagnaDettaglio(
        id=rec.id,
        profilo_id=rec.profilo_id,
        titolo=rec.titolo,
        inizio=rec.inizio,
        fine=rec.fine,
        descrizione=rec.descrizione,
        stato=rec.stato,
        canali=rec.canali,
        canali_tolti=rec.canali_tolti,
        frequenza=rec.frequenza,
        obiettivo=rec.obiettivo,
        inviata_il=rec.inviata_il,
        chiusa_il=rec.chiusa_il,
        gruppi=gruppi_out,
        post_chiesti_per_canale=post_chiesti_per_canale,
        avvisi=avvisi,
        profilo_snapshot=snapshot,
        decisioni=decisioni,
    )


def _al_termine_transazione(
    db: Session,
    *,
    su_commit: Callable[[], object] | None = None,
    su_rollback: Callable[[], object] | None = None,
) -> None:
    """Esegue un'azione sul file system solo all'esito reale della transazione.

    ``flush()`` non rende nulla definitivo: il commit avviene dopo la risposta
    (``get_db``). Le azioni irreversibili sul disco vanno quindi agganciate a
    commit o rollback. Ogni azione scatta al massimo una volta.
    """
    concluso = {"fatto": False}

    def gestore(azione: Callable[[], object] | None) -> Callable[[Session], None]:
        def esegui(_sessione: Session) -> None:
            if concluso["fatto"]:
                return
            concluso["fatto"] = True
            if azione is None:
                return
            try:
                azione()
            except OSError:
                logger.warning(
                    "Operazione sul file system non riuscita.", exc_info=True
                )

        return esegui

    event.listen(db, "after_commit", gestore(su_commit))
    event.listen(db, "after_rollback", gestore(su_rollback))


def crea_gruppo(
    db: Session,
    utente_id: int,
    ruolo: str,
    campagna_id: int,
    dati: GruppoCrea,
) -> GruppoFoto:
    """Crea un nuovo gruppo di foto per la campagna in bozza (CA-46, CA-47)."""
    if ruolo != "artigiano":
        raise NonPermesso("Solo un artigiano può creare gruppi.")

    rec = db.get(Campagna, campagna_id)
    if rec is None:
        raise NonTrovato("Campagna non trovata.")

    profilo = artigiani_service.profilo_di(db, utente_id)
    if profilo is None or rec.profilo_id != profilo.id:
        raise NonTrovato("Campagna non trovata.")

    if rec.stato != BOZZA:
        raise StatoNonValido(
            "I gruppi possono essere creati solo per campagne in bozza."
        )

    if dati.origine not in ORIGINI_GRUPPO:
        raise DatiNonValidi(f"Origine gruppo '{dati.origine}' non valida.")

    if dati.da_usare_il is not None:
        if dati.da_usare_il < rec.inizio or dati.da_usare_il > rec.fine:
            raise DatiNonValidi(
                "La data del gruppo deve rientrare nel periodo della campagna."
            )

    if dati.origine == "create_ai":
        if dati.n_immagini is None or dati.n_immagini < 1 or dati.n_immagini > 20:
            raise DatiNonValidi(
                "Il numero di immagini per un gruppo create_ai deve essere compreso tra 1 e 20."
            )
        n_immagini_val = dati.n_immagini
    else:
        n_immagini_val = None

    gruppo = GruppoFoto(
        profilo_id=profilo.id,
        campagna_id=rec.id,
        origine=dati.origine,
        descrizione=dati.descrizione,
        da_usare_il=dati.da_usare_il,
        n_immagini=n_immagini_val,
    )
    db.add(gruppo)
    db.flush()
    return gruppo


def aggiorna_gruppo(
    db: Session,
    utente_id: int,
    ruolo: str,
    campagna_id: int,
    gruppo_id: int,
    dati: GruppoAggiorna,
) -> GruppoFoto:
    """Aggiorna metadati e descrizione del gruppo (PUT /campagne/{id}/gruppi/{gruppo_id})."""
    if ruolo != "artigiano":
        raise NonPermesso("Solo l'artigiano proprietario può aggiornare il gruppo.")

    rec = db.get(Campagna, campagna_id)
    if rec is None:
        raise NonTrovato("Campagna non trovata.")

    profilo = artigiani_service.profilo_di(db, utente_id)
    if profilo is None or rec.profilo_id != profilo.id:
        raise NonTrovato("Campagna non trovata.")

    if rec.stato != BOZZA:
        raise StatoNonValido(
            "Il gruppo può essere modificato solo per campagne in bozza."
        )

    gruppo = db.get(GruppoFoto, gruppo_id)
    if gruppo is None or gruppo.campagna_id != rec.id:
        raise NonTrovato("Gruppo non trovato nella campagna.")

    if dati.da_usare_il is not None:
        if dati.da_usare_il < rec.inizio or dati.da_usare_il > rec.fine:
            raise DatiNonValidi(
                "La data del gruppo deve rientrare nel periodo della campagna."
            )
        gruppo.da_usare_il = dati.da_usare_il

    if dati.descrizione is not None:
        gruppo.descrizione = dati.descrizione

    if dati.n_immagini is not None:
        if gruppo.origine == "create_ai":
            if dati.n_immagini < 1 or dati.n_immagini > 20:
                raise DatiNonValidi(
                    "Il numero di immagini deve essere compreso tra 1 e 20."
                )
            gruppo.n_immagini = dati.n_immagini

    db.flush()
    return gruppo


def elimina_gruppo(
    db: Session,
    utente_id: int,
    ruolo: str,
    campagna_id: int,
    gruppo_id: int,
) -> None:
    """Elimina tutte le foto appartenenti a un gruppo e il gruppo stesso."""
    if ruolo != "artigiano":
        raise NonPermesso("Solo l'artigiano proprietario può eliminare i gruppi.")

    rec = db.get(Campagna, campagna_id)
    if rec is None:
        raise NonTrovato("Campagna non trovata.")

    profilo = artigiani_service.profilo_di(db, utente_id)
    if profilo is None or rec.profilo_id != profilo.id:
        raise NonTrovato("Campagna non trovata.")

    if rec.stato != BOZZA:
        raise StatoNonValido(
            "I gruppi possono essere eliminati solo per campagne in bozza."
        )

    gruppo = db.get(GruppoFoto, gruppo_id)
    if gruppo is None or gruppo.campagna_id != rec.id:
        raise NonTrovato("Gruppo non trovato nella campagna.")

    foto_gruppo = list(
        db.scalars(
            select(Foto).where(
                Foto.campagna_id == campagna_id,
                Foto.gruppo_id == gruppo_id,
            )
        )
    )
    nomi_file = [f.file for f in foto_gruppo]
    for f in foto_gruppo:
        db.delete(f)
    db.delete(gruppo)
    db.flush()

    archivio = ottieni_archivio()

    def rimuovi_tutti() -> None:
        for n in nomi_file:
            try:
                archivio.elimina(n)
            except OSError:
                logger.warning(
                    "Operazione sul file system non riuscita per %s.",
                    n,
                    exc_info=True,
                )

    _al_termine_transazione(db, su_commit=rimuovi_tutti)


def carica_foto(
    db: Session,
    utente_id: int,
    ruolo: str,
    campagna_id: int,
    contenuto: bytes,
    gruppo_id: int,
) -> Foto:
    """Valida, archivia e registra una foto caricata dall'artigiano per la campagna in bozza.

    Verifiche di sicurezza e conformità:
    - Solo l'artigiano proprietario della bottega può caricare foto (CA-04).
    - La campagna deve essere nello stato 'bozza' (altrimenti StatoNonValido 409).
    - Ispezione binaria e limiti dimensionali (R-13, CA-13): lato corto >= 1080 px,
      max 8192x8192, max 36 MPixel, max 10 MB.
    - La foto entra in un gruppo `caricate` già creato (plan §3): un gruppo
      `create_ai` solleva DatiNonValidi (CA-47).
    - Max 20 foto per gruppo (CA-13).
    - Compensazione atomica anti-TOCTOU: se il database fallisce o solleva eccezione,
      il file su disco viene rimosso immediatamente.
    """
    if ruolo != "artigiano":
        raise NonPermesso("Solo un artigiano può caricare foto.")

    rec = db.get(Campagna, campagna_id)
    if rec is None:
        raise NonTrovato("Campagna non trovata.")

    profilo = artigiani_service.profilo_di(db, utente_id)
    if profilo is None or rec.profilo_id != profilo.id:
        raise NonTrovato("Campagna non trovata.")

    if rec.stato != BOZZA:
        raise StatoNonValido(
            "Le foto possono essere caricate solo per campagne in bozza."
        )

    gruppo = db.scalar(
        select(GruppoFoto).where(GruppoFoto.id == gruppo_id).with_for_update()
    )
    if gruppo is None:
        raise NonTrovato("Gruppo non trovato.")
    if gruppo.campagna_id != rec.id:
        raise DatiNonValidi("Il gruppo specificato appartiene a un'altra campagna.")
    if gruppo.origine == "create_ai":
        raise DatiNonValidi("Non è consentito caricare foto in un gruppo create_ai.")

    # Spec R-13, CA-13: al massimo 20 foto per gruppo
    conteggio = (
        db.scalar(select(func.count(Foto.id)).where(Foto.gruppo_id == gruppo.id)) or 0
    )
    if conteggio >= MAX_FOTO_PER_GRUPPO:
        raise DatiNonValidi(
            f"Un gruppo può contenere al massimo {MAX_FOTO_PER_GRUPPO} foto caricate."
        )

    # Ispezione binaria e vincoli di dimensione/sicurezza (R-13, CA-13, Defense in Depth)
    info = analizza_e_valida_immagine(contenuto)

    archivio = ottieni_archivio()
    nome_file = archivio.salva(contenuto, info.estensione)

    _al_termine_transazione(db, su_rollback=lambda: archivio.elimina(nome_file))

    try:
        nuova_foto = Foto(
            profilo_id=profilo.id,
            campagna_id=rec.id,
            gruppo_id=gruppo.id,
            origine="caricata",
            file=nome_file,
            mime=info.mime,
            larghezza=info.larghezza,
            altezza=info.altezza,
            da_usare=False,
        )
        db.add(nuova_foto)
        db.flush()
        return nuova_foto
    except Exception:
        archivio.elimina(nome_file)
        raise


def imposta_stella_foto(
    db: Session,
    utente_id: int,
    ruolo: str,
    foto_id: int,
    da_usare: bool,
) -> Foto:
    """Imposta il flag stella (da_usare) sulla foto (PUT /foto/{id})."""
    if ruolo != "artigiano":
        raise NonPermesso(
            "Solo l'artigiano proprietario può modificare la stella della foto."
        )

    foto = db.get(Foto, foto_id)
    if foto is None or foto.campagna_id is None:
        raise NonTrovato("Foto non trovata.")

    rec = db.get(Campagna, foto.campagna_id)
    if rec is None:
        raise NonTrovato("Campagna non trovata.")

    profilo = artigiani_service.profilo_di(db, utente_id)
    if profilo is None or rec.profilo_id != profilo.id:
        raise NonTrovato("Foto non trovata.")

    if rec.stato != BOZZA:
        raise StatoNonValido(
            "La stella può essere modificata solo per campagne in bozza."
        )

    foto.da_usare = da_usare
    db.flush()
    return foto


def elimina_foto(
    db: Session,
    utente_id: int,
    ruolo: str,
    foto_id: int,
) -> None:
    """Elimina una singola foto dalla campagna in bozza e rimuove il file fisico."""
    if ruolo != "artigiano":
        raise NonPermesso("Solo l'artigiano proprietario può eliminare le foto.")

    foto = db.get(Foto, foto_id)
    if foto is None or foto.campagna_id is None:
        raise NonTrovato("Foto non trovata.")

    rec = db.get(Campagna, foto.campagna_id)
    if rec is None:
        raise NonTrovato("Campagna non trovata.")

    profilo = artigiani_service.profilo_di(db, utente_id)
    if profilo is None or rec.profilo_id != profilo.id:
        raise NonTrovato("Foto non trovata.")

    if rec.stato != BOZZA:
        raise StatoNonValido(
            "Le foto possono essere eliminate solo per campagne in bozza."
        )

    nome_file = foto.file
    db.delete(foto)
    db.flush()

    archivio = ottieni_archivio()
    _al_termine_transazione(db, su_commit=lambda: archivio.elimina(nome_file))


def leggi_file_foto(
    db: Session,
    utente_id: int,
    ruolo: str,
    foto_id: int,
) -> tuple[bytes, str]:
    """Recupera il contenuto binario e il mime-type del file originale dall'archivio."""
    foto = db.get(Foto, foto_id)
    if foto is None or foto.campagna_id is None:
        raise NonTrovato("Foto non trovata.")

    rec = db.get(Campagna, foto.campagna_id)
    if rec is None:
        raise NonTrovato("Campagna non trovata.")

    if ruolo == "artigiano":
        profilo = artigiani_service.profilo_di(db, utente_id)
        if profilo is None or rec.profilo_id != profilo.id:
            raise NonTrovato("Foto non trovata.")
    elif ruolo not in ("operatore", "admin"):
        raise NonPermesso("Non hai i permessi per accedere al file della foto.")

    archivio = ottieni_archivio()
    try:
        contenuto = archivio.leggi(foto.file)
    except FileNotFoundError:
        raise NonTrovato("File immagine non trovato nell'archivio.")

    return contenuto, foto.mime


def _campagna_per_invio(db: Session, campagna_id: int) -> Campagna:
    """Serializza invio e riprova, rileggendo lo stato dopo il lock."""
    rec = db.scalar(
        select(Campagna)
        .where(Campagna.id == campagna_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if rec is None:
        raise NonTrovato("Campagna non trovata.")
    return rec


def invia_campagna(
    db: Session, utente_id: int, campagna_id: int, ora: datetime
) -> Campagna:
    """Ricontrolla la bozza e fotografa il profilo prima di accodare la generazione."""
    rec = _campagna_per_invio(db, campagna_id)
    profilo = artigiani_service.profilo_di(db, utente_id)
    if profilo is None:
        raise StatoNonValido("Salvare il profilo della bottega prima dell'invio.")
    if rec.profilo_id != profilo.id:
        raise NonTrovato("Campagna non trovata.")
    if rec.stato != BOZZA:
        raise StatoNonValido("Si possono inviare solo campagne in bozza.")

    oggi = ora.astimezone(ROMA).date() if ora.tzinfo else ora.date()
    anticipo = leggi_impostazioni().anticipo_minimo_giorni
    if rec.inizio < oggi + timedelta(days=anticipo):
        raise DatiNonValidi(
            f"La data di inizio deve essere ad almeno {anticipo} giorni da oggi."
        )
    if not 7 <= (rec.fine - rec.inizio).days + 1 <= 92:
        raise DatiNonValidi("La durata della campagna deve essere tra 7 e 92 giorni.")
    if not rec.canali:
        raise DatiNonValidi("Selezionare almeno un canale.")
    collegati = set(artigiani_service.canali_collegati(db, profilo.id))
    if any(canale not in collegati for canale in rec.canali):
        raise StatoNonValido("Collegare tutti i canali selezionati prima dell'invio.")

    gruppi = gruppi_della_campagna(db, rec.id)
    caricate = 0
    for gruppo in gruppi:
        if not gruppo.descrizione or not gruppo.descrizione.strip():
            raise DatiNonValidi("Ogni gruppo deve avere una descrizione.")
        if gruppo.da_usare_il is not None and not (
            rec.inizio <= gruppo.da_usare_il <= rec.fine
        ):
            raise DatiNonValidi(
                "La data del gruppo deve rientrare nel periodo della campagna."
            )
        if gruppo.origine == "caricate":
            fotografie = [
                f
                for f in gruppo.foto
                if f.origine == "caricata" and f.campagna_id == rec.id
            ]
            if len(fotografie) != len(gruppo.foto):
                raise DatiNonValidi(
                    "Il gruppo deve contenere solo foto caricate di questa campagna."
                )
            if not 1 <= len(fotografie) <= MAX_FOTO_PER_GRUPPO:
                raise DatiNonValidi(
                    "Ogni gruppo caricato deve contenere da 1 a 20 foto."
                )
            caricate += len(fotografie)
        elif gruppo.origine == "create_ai":
            if gruppo.n_immagini is None or not 1 <= gruppo.n_immagini <= 20:
                raise DatiNonValidi("Indicare da 1 a 20 immagini da creare.")
        else:
            raise DatiNonValidi("Origine del gruppo non valida.")
    if caricate < 4:
        raise DatiNonValidi("Caricare almeno 4 foto prima dell'invio.")

    rec.profilo_snapshot = {
        colonna.name: deepcopy(getattr(profilo, colonna.name))
        for colonna in profilo.__table__.columns
        if colonna.name not in ("id", "aggiornato_il")
    }
    rec.frequenza = profilo.frequenza
    rec.obiettivo = profilo.obiettivo
    rec.inviata_il = ora
    cambia_stato(db, rec, INVIATA, ora=ora)
    coda.accoda(coda.GENERA_CAMPAGNA, campagna_id=rec.id)
    return rec


def riprova_campagna(db: Session, campagna_id: int, ora: datetime) -> Campagna:
    """Riparte con gli stessi dati e senza cancellare le tappe già salvate (R-24)."""
    rec = _campagna_per_invio(db, campagna_id)
    if rec.stato != GENERAZIONE_FALLITA:
        raise StatoNonValido(
            "Si possono riprovare solo campagne con generazione fallita."
        )
    cambia_stato(db, rec, INVIATA, ora=ora)
    coda.accoda(coda.GENERA_CAMPAGNA, campagna_id=rec.id)
    return rec
