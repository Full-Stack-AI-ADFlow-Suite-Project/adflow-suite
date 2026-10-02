"""Logica del modulo campagne: l'unica parte che gli altri moduli possono importare."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errori import DatiNonValidi, NonTrovato
from app.core.transizioni import verifica_transizione

from .domain import ESITI_DECISIONE, ESITO_RESPINTA, MOTIVI_DECISIONE, TRANSIZIONI
from .models import Campagna, DecisioneCampagna, Foto


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
        nota: testo libero facoltativo dell'operatore.
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
