from datetime import datetime, timedelta
from typing import Any
import uuid
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.adapters.archivio import ottieni_archivio
from app.core.config import leggi_impostazioni
from app.core.errori import DatiNonValidi, NonPermesso, NonTrovato, StatoNonValido
from app.core.orologio import ROMA
from app.core.transizioni import verifica_transizione
from app.moduli.artigiani import service as artigiani_service

from .domain import (
    ANNULLATA,
    BOZZA,
    CONCLUSA,
    ESITI_DECISIONE,
    ESITO_RESPINTA,
    MOTIVI_DECISIONE,
    RESPINTA,
    SCADUTA,
    STATI,
    TRANSIZIONI,
)
from .immagini import analizza_e_valida_immagine
from .models import Campagna, DecisioneCampagna, Foto
from .schemas import CampagnaCrea, CampagnaDettaglio


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

    Raises:
        StatoNonValido: se la transizione da stato attuale a ``nuovo`` non è
            ammessa dal diagramma di ``campagne/domain.py``.
    """
    verifica_transizione(TRANSIZIONI, campagna.stato, nuovo)
    campagna.stato = nuovo
    db.flush()


def registra_decisione(
    db: Session,
    campagna: Campagna,
    utente_id: int,
    esito: str,
    motivo: str | None,
    nota: str | None,
    foto_segnate: list[int],
) -> None:
    """Scrive una riga nella tabella ``decisione_campagna``.

    Usata da ``revisione`` dopo ogni approvazione, rimanda o respinta.
    Le decisioni non si cancellano mai (constitution §1.2): questa funzione
    crea sempre un nuovo record, non aggiorna quelli esistenti.

    Args:
        db: sessione del database (aperta e chiusa dal chiamante).
        campagna: il record ``Campagna`` a cui appartiene la decisione.
        utente_id: id dell'operatore che ha preso la decisione.
        esito: ``"approvata"``, ``"rimandata"`` o ``"respinta"``.
        motivo: obbligatorio se ``esito`` è ``"respinta"`` (``"foto"`` o
                ``"altro"``), ``None`` altrimenti.
        nota: testo libero dell'operatore; obbligatoria se ``esito`` è
              ``"respinta"``, facoltativa altrimenti.
        foto_segnate: lista di id delle foto segnalate come problematiche,
                      vuota se non applicabile.

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


def crea_bozza(
    db: Session,
    utente_id: int,
    dati: CampagnaCrea,
    ora: datetime,
) -> Campagna:
    """Crea una nuova campagna nello stato bozza per l'artigiano autenticato.

    Verifica le regole di pianificazione R-08 e i vincoli di unicità R-12:
    - Anticipo minimo di 3 giorni rispetto a oggi (CA-09).
    - Data di fine successiva a data di inizio (CA-10).
    - Durata massima di 92 giorni (CA-10).
    - Una sola bozza contemporanea per l'artigiano (CA-11).
    - Periodo non sovrapposto con campagne attive o in corso dello stesso artigiano (CA-12).

    Args:
        db: sessione del database aperta dal chiamante.
        utente_id: ID dell'utente artigiano.
        dati: payload validato con titolo, date, descrizione e flag crea_immagini_ai.
        ora: data e ora correnti (per calcolo anticipo minimo).

    Returns:
        Il record Campagna appena creato in stato bozza.

    Raises:
        DatiNonValidi: se i vincoli temporali (R-08) non sono rispettati o manca il profilo.
        StatoNonValido: se esiste già una bozza aperta (CA-11) o c'è sovrapposizione (CA-12).
    """
    profilo = artigiani_service.profilo_di(db, utente_id)
    if profilo is None:
        raise DatiNonValidi("Profilo bottega non trovato.")

    # Concorrenza atomica: lock di transazione sull'artigiano per serializzare richieste concorrenti
    db.execute(text("SELECT pg_advisory_xact_lock(:chiave)"), {"chiave": profilo.id})

    oggi = ora.astimezone(ROMA).date() if ora.tzinfo else ora.date()
    impostazioni = leggi_impostazioni()
    anticipo_minimo = timedelta(days=impostazioni.anticipo_minimo_giorni)

    if dati.inizio < oggi + anticipo_minimo:
        raise DatiNonValidi("La data di inizio deve essere ad almeno 3 giorni da oggi.")

    if dati.fine <= dati.inizio:
        raise DatiNonValidi(
            "La data di fine deve essere successiva alla data di inizio."
        )

    if (dati.fine - dati.inizio).days > 92:
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

    # R-12, CA-12: campagne non annullata/conclusa/respinta/scaduta non sovrapposte
    stati_non_bloccanti = [ANNULLATA, CONCLUSA, RESPINTA, SCADUTA]
    campagna_sovrapposta = db.scalar(
        select(Campagna.id).where(
            Campagna.profilo_id == profilo.id,
            Campagna.stato.not_in(stati_non_bloccanti),
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
        crea_immagini_ai=dati.crea_immagini_ai,
        stato=BOZZA,
    )
    db.add(nuova)
    db.flush()
    return nuova


def elenca_campagne(
    db: Session,
    utente_id: int,
    ruolo: str,
    stato: str | None = None,
) -> list[Campagna]:
    """Elenca le campagne accessibili all'utente autenticato.

    L'artigiano visualizza solo le proprie campagne (legate alla sua bottega).
    L'operatore e l'admin visualizzano tutte le campagne del consorzio.
    Supporta il filtro opzionale per stato.
    """
    query = select(Campagna)

    if ruolo == "artigiano":
        profilo = artigiani_service.profilo_di(db, utente_id)
        if profilo is None:
            return []
        query = query.where(Campagna.profilo_id == profilo.id)
    elif ruolo not in ("operatore", "admin"):
        return []

    if stato:
        if stato not in STATI:
            raise DatiNonValidi("Stato della campagna non valido.")
        query = query.where(Campagna.stato == stato)

    query = query.order_by(Campagna.id.desc())
    return list(db.scalars(query))


def dettaglio_campagna(
    db: Session,
    utente_id: int,
    ruolo: str,
    campagna_id: int,
) -> CampagnaDettaglio:
    """Restituisce il dettaglio della campagna con controlli di accesso granulari.

    Se l'utente è un artigiano e la campagna appartiene a un altro artigiano,
    solleva NonTrovato (404) per evitare fuga di informazioni (CA-04).
    Per operatori e admin include anche snapshot e decisioni pregresse.
    """
    rec = db.get(Campagna, campagna_id)
    if rec is None:
        raise NonTrovato("Campagna non trovata.")

    if ruolo == "artigiano":
        profilo = artigiani_service.profilo_di(db, utente_id)
        if profilo is None or rec.profilo_id != profilo.id:
            raise NonTrovato("Campagna non trovata.")
    elif ruolo not in ("operatore", "admin"):
        raise NonPermesso("Non hai i permessi per visualizzare le campagne.")

    foto = foto_della_campagna(db, campagna_id)

    decisioni = []
    snapshot = None
    if ruolo in ("operatore", "admin"):
        snapshot = rec.profilo_snapshot
        decisioni = list(
            db.scalars(
                select(DecisioneCampagna)
                .where(DecisioneCampagna.campagna_id == campagna_id)
                .order_by(DecisioneCampagna.id)
            )
        )

    return CampagnaDettaglio(
        id=rec.id,
        profilo_id=rec.profilo_id,
        titolo=rec.titolo,
        inizio=rec.inizio,
        fine=rec.fine,
        descrizione=rec.descrizione,
        crea_immagini_ai=rec.crea_immagini_ai,
        stato=rec.stato,
        canali=rec.canali,
        frequenza=rec.frequenza,
        obiettivo=rec.obiettivo,
        inviata_il=rec.inviata_il,
        rimandata=rec.rimandata,
        foto=foto,
        profilo_snapshot=snapshot,
        decisioni=decisioni,
    )


def carica_foto(
    db: Session,
    utente_id: int,
    ruolo: str,
    campagna_id: int,
    contenuto: bytes,
    gruppo_id: UUID | None = None,
) -> Foto:
    """Valida, archivia e registra una foto caricata dall'artigiano per la campagna in bozza.

    Verifiche di sicurezza e conformità:
    - Solo l'artigiano proprietario della bottega può caricare foto (CA-04).
    - La campagna deve essere nello stato 'bozza' (altrimenti StatoNonValido).
    - Ispezione binaria e limiti dimensionali (R-13, CA-13): lato corto >= 1080 px,
      max 8192x8192, max 36 MPixel, max 10 MB.
    - Se gruppo_id è fornito e già usato, eredita la descrizione del gruppo;
      se appartiene a un'altra campagna solleva DatiNonValidi.
    - Salvataggio con nome univoco generato dal server (UUID).
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

    # Ispezione binaria e vincoli di dimensione/sicurezza
    info = analizza_e_valida_immagine(contenuto)

    # Determinazione gruppo e descrizione
    descrizione_gruppo: str | None = None
    if gruppo_id is None:
        gruppo_effettivo = uuid.uuid4()
    else:
        gruppo_effettivo = gruppo_id
        # Verifica se il gruppo è già associato a un'altra campagna
        altro_uso = db.scalar(
            select(Foto.campagna_id)
            .where(
                Foto.gruppo_id == gruppo_effettivo,
                Foto.campagna_id != campagna_id,
            )
            .limit(1)
        )
        if altro_uso is not None:
            raise DatiNonValidi("Il gruppo specificato appartiene a un'altra campagna.")

        # Eredita eventuale descrizione esistente del gruppo nella campagna
        foto_esistente = db.scalar(
            select(Foto)
            .where(
                Foto.campagna_id == campagna_id,
                Foto.gruppo_id == gruppo_effettivo,
            )
            .limit(1)
        )
        if foto_esistente is not None:
            descrizione_gruppo = foto_esistente.descrizione

    # Salvataggio fisico su archivio
    archivio = ottieni_archivio()
    nome_file = archivio.salva(contenuto, info.estensione)

    # Inserimento DB con rollback/compensazione del file fisico in caso di errore
    try:
        nuova_foto = Foto(
            profilo_id=profilo.id,
            campagna_id=campagna_id,
            gruppo_id=gruppo_effettivo,
            origine="caricata",
            file=nome_file,
            mime=info.mime,
            larghezza=info.larghezza,
            altezza=info.altezza,
            descrizione=descrizione_gruppo,
        )
        db.add(nuova_foto)
        db.flush()
        return nuova_foto
    except Exception:
        archivio.elimina(nome_file)
        raise


def aggiorna_descrizione_gruppo(
    db: Session,
    utente_id: int,
    ruolo: str,
    campagna_id: int,
    gruppo_id: UUID,
    descrizione: str,
) -> None:
    """Aggiorna la descrizione di tutte le foto appartenenti a un gruppo della campagna.

    Consentito solo all'artigiano proprietario per campagne in stato 'bozza'.
    """
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
            "La descrizione può essere modificata solo per campagne in bozza."
        )

    foto_gruppo = list(
        db.scalars(
            select(Foto).where(
                Foto.campagna_id == campagna_id,
                Foto.gruppo_id == gruppo_id,
            )
        )
    )
    if not foto_gruppo:
        raise NonTrovato("Gruppo di foto non trovato nella campagna.")

    for f in foto_gruppo:
        f.descrizione = descrizione
    db.flush()


def elimina_foto(
    db: Session,
    utente_id: int,
    ruolo: str,
    foto_id: int,
) -> None:
    """Elimina una singola foto dalla campagna in bozza e rimuove il file fisico.

    Atomicità e anti-TOCTOU: il record a database viene rimosso prima con flush(),
    e solo a operazione DB completata con successo viene rimosso il file fisico.
    """
    if ruolo != "artigiano":
        raise NonPermesso("Solo l'artigiano proprietario può eliminare le foto.")

    foto = db.get(Foto, foto_id)
    if foto is None:
        raise NonTrovato("Foto non trovata.")

    rec = db.get(Campagna, foto.campagna_id)
    if rec is None:
        raise NonTrovato("Foto non trovata.")

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
    archivio.elimina(nome_file)


def elimina_gruppo(
    db: Session,
    utente_id: int,
    ruolo: str,
    campagna_id: int,
    gruppo_id: UUID,
) -> None:
    """Elimina tutte le foto appartenenti a un gruppo e rimuove i rispettivi file fisici."""
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

    foto_gruppo = list(
        db.scalars(
            select(Foto).where(
                Foto.campagna_id == campagna_id,
                Foto.gruppo_id == gruppo_id,
            )
        )
    )
    if not foto_gruppo:
        raise NonTrovato("Gruppo di foto non trovato nella campagna.")

    nomi_file = [f.file for f in foto_gruppo]
    for f in foto_gruppo:
        db.delete(f)
    db.flush()

    archivio = ottieni_archivio()
    for nome in nomi_file:
        archivio.elimina(nome)


def leggi_file_foto(
    db: Session,
    utente_id: int,
    ruolo: str,
    foto_id: int,
) -> tuple[bytes, str]:
    """Recupera il contenuto binario e il mime-type del file originale dall'archivio.

    L'accesso è consentito all'artigiano proprietario della campagna,
    oppure a operatori e amministratori del consorzio.
    """
    foto = db.get(Foto, foto_id)
    if foto is None:
        raise NonTrovato("Foto non trovata.")

    rec = db.get(Campagna, foto.campagna_id)
    if rec is None:
        raise NonTrovato("Foto non trovata.")

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
