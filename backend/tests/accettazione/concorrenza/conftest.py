"""Aiuto per le prove di concorrenza di T4-103.

Le prove chiamano i service direttamente, con **una sessione e una connessione
PostgreSQL per thread** e commit veri: è il livello dove vivono le corse
(lettura condizionale, incremento in Python, accodamento). La barriera
(`threading.Barrier`) fa partire le azioni insieme; il primo thread che arriva
aspetta gli altri.

Il database è quello delle fixture di plan §7 (`adflow_test`). Le prove
committano, quindi il modulo si pulisce da solo alla fine: senza la pulizia i
dati resterebbero visibili ai test successivi.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from typing import Any

import pytest
from sqlalchemy import Engine, text
from sqlalchemy.orm import Session

from app.core.config import leggi_impostazioni
from app.core.db import crea_motore
from tests.moduli.accesso.fabbrica import utente
from tests.moduli.artigiani.fabbrica import profilo

SECONDI_TIMEOUT = 60


@pytest.fixture(scope="module")
def motore_concorrenza(motore_test: Engine) -> Engine:
    """Un motore suo su adflow_test: ogni thread apre e chiude la sua sessione.

    `motore_test` porta il database all'ultima migrazione: su una macchina pulita
    le tabelle non ci sono ancora.
    """
    motore = crea_motore(leggi_impostazioni().database_url_test)
    yield motore
    motore.dispose()


@pytest.fixture(scope="module", autouse=True)
def pulizia_del_modulo(motore_concorrenza: Engine):
    """A fine modulo il database torna vuoto: le prove hanno scritto con commit."""
    yield
    with motore_concorrenza.begin() as connessione:
        tabelle = list(
            connessione.scalars(
                text(
                    "SELECT tablename FROM pg_tables "
                    "WHERE schemaname = 'public' AND tablename <> 'alembic_version'"
                )
            )
        )
        if tabelle:
            nomi = ", ".join(f'"{tabella}"' for tabella in tabelle)
            connessione.execute(text(f"TRUNCATE TABLE {nomi} CASCADE"))


def crea_con_commit(motore: Engine, costruisci: Callable[[Session], Any]) -> Any:
    """Esegue `costruisci` in una sessione sua e committa: i thread la vedranno."""
    with Session(motore, expire_on_commit=False) as sessione:
        risultato = costruisci(sessione)
        sessione.commit()
        return risultato


def esegui_in_parallelo(
    motore: Engine, azioni: list[Callable[[Session], Any]]
) -> tuple[list[Any], list[BaseException | None]]:
    """Esegue le azioni in thread diversi, tutte ferme alla barriera prima di partire.

    Ogni azione riceve la sua `Session` sul database di test e, se non solleva,
    fa commit. Torna i risultati e le eccezioni, nell'ordine delle azioni.
    """
    barriera = threading.Barrier(len(azioni))
    risultati: list[Any] = [None] * len(azioni)
    errori: list[BaseException | None] = [None] * len(azioni)

    def esegui(indice: int, azione: Callable[[Session], Any]) -> None:
        try:
            barriera.wait(timeout=SECONDI_TIMEOUT)
        except threading.BrokenBarrierError as errore:
            errori[indice] = errore
            return
        with Session(motore, expire_on_commit=False) as sessione:
            try:
                risultati[indice] = azione(sessione)
                sessione.commit()
            except BaseException as errore:  # noqa: BLE001 — lo legge il test
                sessione.rollback()
                errori[indice] = errore

    fili = [
        threading.Thread(target=esegui, args=(indice, azione), daemon=True)
        for indice, azione in enumerate(azioni)
    ]
    for filo in fili:
        filo.start()
    for filo in fili:
        filo.join(timeout=SECONDI_TIMEOUT)
    assert all(not filo.is_alive() for filo in fili), "un thread non è terminato"
    return risultati, errori


@pytest.fixture
def mondo_concorrenza(motore_concorrenza: Engine) -> dict:
    """Due operatori, due artigiani con la loro bottega: utenti con commit vero."""

    def costruisci(sessione: Session) -> dict:
        operatore = utente(sessione, "operatore")
        operatore2 = utente(sessione, "operatore")
        artigiano = utente(sessione, "artigiano")
        artigiano2 = utente(sessione, "artigiano")
        bottega = profilo(sessione, utente_id=artigiano.id)
        bottega2 = profilo(sessione, utente_id=artigiano2.id)
        return {
            "operatore": operatore,
            "operatore2": operatore2,
            "artigiano": artigiano,
            "artigiano2": artigiano2,
            "bottega": bottega,
            "bottega2": bottega2,
        }

    return crea_con_commit(motore_concorrenza, costruisci)
