"""T3-31, T3-34: il costo di ogni chiamata all'AI si registra in `chiamata_ai` (spec R-44).

CA-82 per analisi, piano, testi e immagini: la generazione e la rigenerazione
scrivono una riga per chiamata, Vedi campagna mostra il totale.
"""

from collections import Counter
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import select

from app.adapters.ai import AIFinto, UsoAI, usa_ai
from app.adapters.archivio import ArchivioFinto, usa_archivio
from app.moduli.campagne import service as campagne
from app.moduli.contenuti import jobs
from app.moduli.contenuti.models import ChiamataAI, Post
from app.moduli.contenuti.service import (
    accendi_intervento,
    costo_ai_della_campagna,
    registra_chiamata_ai,
)
from app.moduli.revisione.service import vedi_campagna
from tests.moduli.campagne.fabbrica import campagna_inviata, foto
from tests.moduli.contenuti.fabbrica import post_da_approvare
from tests.moduli.artigiani.fabbrica import profilo

ADESSO = datetime(2030, 1, 1, 9, tzinfo=timezone.utc)
COSTO = Decimal("0.002")
CANALI = ["facebook", "instagram"]


@pytest.fixture
def ai() -> Iterator[AIFinto]:
    with usa_ai(AIFinto(costo_chiamata=COSTO)) as finto:
        yield finto


@pytest.fixture(autouse=True)
def archivio() -> Iterator[ArchivioFinto]:
    with usa_archivio(ArchivioFinto()) as finto:
        yield finto


@pytest.fixture(autouse=True)
def transazioni_di_prova(db, monkeypatch) -> None:
    @contextmanager
    def transazione():
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise

    monkeypatch.setattr(jobs, "transazione", transazione)
    monkeypatch.setattr(jobs, "adesso", lambda: ADESSO)


def _righe(db, campagna_id: int) -> list[ChiamataAI]:
    return list(
        db.scalars(
            select(ChiamataAI)
            .where(ChiamataAI.campagna_id == campagna_id)
            .order_by(ChiamataAI.id)
        )
    )


def test_ca82_ogni_chiamata_della_generazione_ha_il_suo_costo(db, ai):
    """4 foto, 3 post a settimana su 14 giorni, 2 canali: 1 analisi, 1 piano, 12 testi, 2 immagini."""
    bottega = profilo(db, canali=CANALI, frequenza="f3_4")
    campagna = campagna_inviata(
        db, profilo_id=bottega.id, inizio=date(2030, 1, 7), fine=date(2030, 1, 20)
    )
    db.commit()

    for esecuzione in range(1, 4):
        if not jobs.esegui_generazione(campagna.id, esecuzione):
            break
    assert campagna.stato == "in_revisione"

    righe = _righe(db, campagna.id)
    assert Counter(riga.tipo for riga in righe) == {
        "analisi": 1,
        "piano": 1,
        "testo": 12,
        "immagine": 2,
    }
    assert {(r.provider_ai, r.modello_ai) for r in righe} == {("finto", "finto")}
    assert all(r.costo_usd == COSTO for r in righe)
    # testi e immagini portano il post, analisi e piano no
    assert all(
        (r.post_id is not None) == (r.tipo in ("testo", "immagine")) for r in righe
    )
    assert {r.post_id for r in righe if r.tipo == "testo"} == set(
        db.scalars(select(Post.id).where(Post.campagna_id == campagna.id))
    )
    # una sola immagine per uscita, anche se l'uscita ha due post
    assert all(r.n_immagini == 1 for r in righe if r.tipo == "immagine")
    assert all(r.n_immagini is None for r in righe if r.tipo != "immagine")

    assert costo_ai_della_campagna(db, campagna.id) == COSTO * 16
    assert vedi_campagna(db, campagna.id).costo_ai == COSTO * 16


def test_una_campagna_senza_chiamate_costa_zero(db):
    bottega = profilo(db, canali=CANALI)
    campagna = campagna_inviata(db, profilo_id=bottega.id)
    assert costo_ai_della_campagna(db, campagna.id) == 0
    assert vedi_campagna(db, campagna.id).costo_ai == 0


def test_la_rigenerazione_di_un_testo_registra_la_sua_chiamata(db, ai):
    uno = post_da_approvare(db)
    accendi_intervento(db, uno.id, "rigenera_totale", ADESSO)
    db.commit()

    assert jobs.esegui_rigenerazione(uno.id, None, None, 1) is False

    (riga,) = _righe(db, uno.campagna_id)
    assert (riga.tipo, riga.post_id, riga.costo_usd) == ("testo", uno.id, COSTO)


def test_registra_chiamata_ai_conserva_token_e_immagini(db):
    bottega = profilo(db, canali=CANALI)
    campagna = campagna_inviata(db, profilo_id=bottega.id)
    uso = UsoAI(
        "immagine",
        "litellm",
        "modello",
        token_ingresso=10,
        token_uscita=20,
        immagini=1,
        costo_usd=Decimal("0.040000"),
    )
    riga = registra_chiamata_ai(db, campagna.id, uso)
    assert (riga.token_ingresso, riga.token_uscita, riga.n_immagini) == (10, 20, 1)
    assert riga.costo_usd == Decimal("0.04")
    assert registra_chiamata_ai(db, campagna.id, None) is None


# --- Storico dell'AI (T3-916, R-50, CA-109) -----------------------------------


def _generata(db, ai):
    bottega = profilo(db, canali=CANALI, frequenza="f3_4")
    campagna = campagna_inviata(
        db, profilo_id=bottega.id, inizio=date(2030, 1, 7), fine=date(2030, 1, 20)
    )
    db.commit()
    esecuzioni = []
    for esecuzione in range(1, 4):
        esecuzioni.append(esecuzione)
        if not jobs.esegui_generazione(campagna.id, esecuzione):
            break
    return campagna


def test_ca109_ogni_chiamata_ha_prompt_richiesta_risposta_esito_e_durata(db, ai):
    campagna = _generata(db, ai)

    righe = _righe(db, campagna.id)
    assert len(righe) == len(ai.chiamate) == 16
    for riga in righe:
        assert riga.versione_prompt == "finto-1"
        assert riga.esito == "ok" and riga.errore is None
        assert riga.durata_ms is not None
        assert riga.tentativo is not None
        assert riga.richiesta  # niente byte né chiavi: solo testo e id
    assert all(r.risposta for r in righe if r.tipo != "immagine")
    analisi = next(r for r in righe if r.tipo == "analisi")
    assert all(f.startswith("<foto ") for f in analisi.richiesta["foto"])
    assert analisi.tentativo == 1
    assert [r.tentativo for r in righe if r.tipo == "piano"] == [1]
    assert {r.tentativo for r in righe if r.tipo == "testo"} == {1}


def test_ca109_un_errore_temporaneo_sul_piano_resta_dopo_l_annullamento(db, ai):
    ai.comanda_errore("pianifica_campagna", "temporaneo", volte=None)
    bottega = profilo(db, canali=CANALI, frequenza="f3_4")
    campagna = campagna_inviata(
        db, profilo_id=bottega.id, inizio=date(2030, 1, 7), fine=date(2030, 1, 20)
    )
    db.commit()

    assert jobs.esegui_generazione(campagna.id, 1) is True

    fallite = [r for r in _righe(db, campagna.id) if r.esito != "ok"]
    assert len(fallite) == 1
    riga = fallite[0]
    assert (riga.tipo, riga.esito, riga.costo_usd) == ("piano", "temporaneo", 0)
    assert "temporaneo" in riga.errore and riga.versione_prompt == "finto-1"
    assert riga.risposta is None and riga.tentativo == 1
    # l'analisi, salvata da un passo prima, è ancora lì
    assert [r.tipo for r in _righe(db, campagna.id)].count("analisi") == 1


def test_ca109_la_chiamata_fallita_di_una_foto_sola_porta_la_foto(db, ai):
    bottega = profilo(db, canali=CANALI, frequenza="f3_4")
    campagna = campagna_inviata(
        db, profilo_id=bottega.id, inizio=date(2030, 1, 7), fine=date(2030, 1, 20)
    )
    db.commit()
    ids = [f.id for f in campagne.foto_della_campagna(db, campagna.id)]
    ai.comanda_errore("analizza_gruppo", "richiesta", foto_id=ids[0])

    jobs.esegui_generazione(campagna.id, 1)

    riga = next(r for r in _righe(db, campagna.id) if r.esito == "richiesta")
    assert (riga.tipo, riga.foto_id) == ("analisi", ids[0])


def test_ca109_una_rigenerazione_fallita_lascia_la_sua_chiamata(db, ai):
    uno = post_da_approvare(db)
    accendi_intervento(db, uno.id, "rigenera_totale", ADESSO)
    db.commit()
    ai.comanda_errore("genera_post", "temporaneo", volte=1)

    assert jobs.esegui_rigenerazione(uno.id, None, None, 1) is True

    (riga,) = _righe(db, uno.campagna_id)
    assert (riga.esito, riga.post_id, riga.costo_usd) == ("temporaneo", uno.id, 0)
    assert riga.tentativo == 1 and riga.errore
