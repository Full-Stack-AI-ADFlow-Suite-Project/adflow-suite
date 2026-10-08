"""Logica del modulo campagne: l'unica parte che gli altri moduli possono importare."""

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.orm import Session, selectinload

from app.core.config import leggi_impostazioni
from app.core.errori import DatiNonValidi, NonPermesso, NonTrovato, StatoNonValido
from app.core import orologio
from app.core.orologio import ROMA
from app.core.transizioni import verifica_transizione
from app.moduli.artigiani import service as artigiani_service

from .domain import (
    BOZZA,
    ESITI_DECISIONE,
    ESITO_RESPINTA,
    MOTIVI_DECISIONE,
    ORIGINI_FOTO,
    STATI,
    STATI_CHIUSI,
    TRANSIZIONI,
)
from .models import Campagna, DecisioneCampagna, Foto, GruppoFoto
from .schemas import (
    CampagnaCrea,
    CampagnaDettaglio,
    CampagnaElencoItem,
    DecisioneSintetica,
    FotoSintetica,
    GruppoSintetico,
)

CANALI_AMMESSI = ("facebook", "instagram")
POST_A_SETTIMANA = {"f1_2": 2, "f3_4": 3, "f5_piu": 5, "decidete_voi": 3}
LIMITI_POLICY_FOTO = {"meno_5": 4, "da5_a12": 12, "da12_a20": 20}


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

    # R-22, CA-48: verifica canali ammessi e collegati
    canali_richiesti = dati.canali
    if not canali_richiesti:
        raise DatiNonValidi("Selezionare almeno un canale.")
    for c in canali_richiesti:
        if c not in CANALI_AMMESSI:
            raise DatiNonValidi(f"Canale '{c}' non ammesso.")

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
        raise DatiNonValidi("La data di inizio deve essere ad almeno 3 giorni da oggi.")

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
        profilo_ids = list({c.profilo_id for c in campagne})
        rows = db.execute(
            text("SELECT id, nome, citta FROM profilo_bottega WHERE id = ANY(:ids)"),
            {"ids": profilo_ids},
        ).fetchall()
        mappa_profili = {r[0]: (r[1], r[2]) for r in rows}
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
    giorni = (rec.fine - rec.inizio).days + 1
    frequenza_val = rec.frequenza
    foto_policy_val = None

    if profilo is not None:
        if not frequenza_val:
            frequenza_val = profilo.frequenza
        foto_policy_val = profilo.foto_policy
    else:
        p_row = db.execute(
            text("SELECT frequenza, foto_policy FROM profilo_bottega WHERE id = :pid"),
            {"pid": rec.profilo_id},
        ).fetchone()
        if p_row:
            if not frequenza_val:
                frequenza_val = p_row[0]
            foto_policy_val = p_row[1]

    freq = frequenza_val or "decidete_voi"
    post_sett = POST_A_SETTIMANA.get(freq, 3)
    post_chiesti = (post_sett * giorni) // 7

    canali = rec.canali or []
    post_chiesti_per_canale = {canale: post_chiesti for canale in canali}

    # Calcolo avvisi informativi (spec R-25, CA-54)
    n_foto_caricate = sum(len(g.foto) for g in gruppi_db if g.origine == "caricate")
    avvisi: list[str] = []
    for _canale in canali:
        if post_chiesti > 0 and n_foto_caricate < post_chiesti:
            if "foto_poche" not in avvisi:
                avvisi.append("foto_poche")
        if post_chiesti > n_foto_caricate and (post_chiesti - n_foto_caricate) > (
            n_foto_caricate / 2
        ):
            if "riempitivi_molti" not in avvisi:
                avvisi.append("riempitivi_molti")

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
