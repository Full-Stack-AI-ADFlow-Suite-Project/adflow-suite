"""Logica del modulo campagne: l'unica parte che gli altri moduli possono importare."""

from typing import Annotated, Any

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.db import get_db


def campagna(
    db: Annotated[Session, Depends(get_db)],
    id: int,
) -> Any:
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
        NotImplementedError: stub — implementazione in T1-04.
    """
    raise NotImplementedError  # T1-04


def foto_della_campagna(
    db: Annotated[Session, Depends(get_db)],
    id: int,
) -> list[Any]:
    """Restituisce tutte le foto associate alla campagna indicata.

    Usata da ``contenuti`` (analisi AI), ``revisione`` e ``pubblicazione``.
    Restituisce una lista vuota se la campagna non ha foto, senza sollevare
    eccezioni: la presenza di foto è verificata altrove (es. prima dell'invio).

    Args:
        db: sessione del database (aperta e chiusa dal chiamante).
        id: chiave primaria della campagna.

    Returns:
        Lista di record ``Foto``, vuota se la campagna non ne ha.

    Raises:
        NotImplementedError: stub — implementazione in T1-04.
    """
    raise NotImplementedError  # T1-04


def campagne_in_stato(
    db: Annotated[Session, Depends(get_db)],
    stati: list[str],
) -> list[Any]:
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

    Raises:
        NotImplementedError: stub — implementazione in T1-04.
    """
    raise NotImplementedError  # T1-04


def cambia_stato(
    db: Annotated[Session, Depends(get_db)],
    campagna: Any,
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
        NotImplementedError: stub — implementazione in T1-04.
    """
    raise NotImplementedError  # T1-04


def registra_decisione(
    db: Annotated[Session, Depends(get_db)],
    campagna: Any,
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
        NotImplementedError: stub — implementazione in T1-04.
    """
    raise NotImplementedError  # T1-04


def aggiorna_foto(
    db: Annotated[Session, Depends(get_db)],
    foto_id: int,
    analisi_ai: str | None,
    n_utilizzi: int,
) -> None:
    """Aggiorna il risultato dell'analisi AI e il contatore utilizzi di una foto.

    Chiamata da ``contenuti`` durante il job ``genera_campagna``, dopo che
    l'adattatore AI ha analizzato l'immagine. La foto appartiene al modulo
    campagne, quindi solo questo service può modificarla.

    Args:
        db: sessione del database (aperta e chiusa dal chiamante).
        foto_id: chiave primaria della foto da aggiornare.
        analisi_ai: testo descrittivo prodotto dall'AI, o ``None`` se
                    l'analisi non ha prodotto risultati.
        n_utilizzi: numero totale di volte che la foto è stata usata
                    in versioni di post.

    Raises:
        NonTrovato: se non esiste nessuna foto con quell'id.
        NotImplementedError: stub — implementazione in T1-04.
    """
    raise NotImplementedError  # T1-04
