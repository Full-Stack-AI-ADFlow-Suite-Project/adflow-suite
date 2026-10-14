"""T3-32: `prova-ai` genera una campagna e stampa cosa ha fatto e speso l'AI.

Con il provider finto: nessuna chiamata reale (la prova vera si lancia a mano,
con `AI_PROVIDER=litellm` in `backend/.env`).
"""

from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app import cli
from app.adapters.ai import AIFinto, usa_ai
from app.core.errori import NonTrovato
from app.moduli.campagne import service as campagne
from app.moduli.contenuti.models import Post
from app.moduli.contenuti.service import riepilogo_ai_della_campagna
from tests.moduli.artigiani.fabbrica import profilo
from tests.moduli.campagne.fabbrica import campagna_in_revisione, campagna_inviata, foto

ADESSO = datetime(2030, 1, 1, 9, tzinfo=timezone.utc)
COSTO = Decimal("0.01")


@pytest.fixture
def ai() -> Iterator[AIFinto]:
    with usa_ai(AIFinto(costo_chiamata=COSTO)) as finto:
        yield finto


@pytest.fixture(autouse=True)
def cli_sul_db_di_test(db: Session, monkeypatch: pytest.MonkeyPatch) -> None:
    """Come nel worker: commit alla fine di ogni passo, rollback se c'è un errore."""

    @contextmanager
    def transazione() -> Iterator[Session]:
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise

    monkeypatch.setattr(cli, "transazione", transazione)


def _prova(campagna_id: int) -> cli.EsitoProva:
    return cli.esegui_prova_ai(campagna_id, ora=lambda: ADESSO)


def _campagna(db: Session, *, n_foto: int = 6):
    """Campagna `inviata` di 14 giorni, 3 post a settimana, due canali: 12 post."""
    bottega = profilo(
        db,
        nome="Ceramiche Bianchi",
        canali=["facebook", "instagram"],
        frequenza="f3_4",
    )
    campagna = campagna_inviata(
        db, profilo_id=bottega.id, inizio=date(2030, 1, 7), fine=date(2030, 1, 20)
    )
    mazzo = campagne.gruppi_della_campagna(db, campagna.id)[0]
    for _ in range(n_foto - 4):
        foto(db, gruppo=mazzo)
    db.commit()
    return campagna


def _tipo(esito: cli.EsitoProva, tipo: str):
    return next(r for r in esito.riepilogo.per_tipo if r.tipo == tipo)


def test_la_prova_genera_la_campagna_e_conta_le_chiamate_per_tipo(db, ai):
    campagna = _campagna(db)

    esito = _prova(campagna.id)

    assert esito.errore is None
    assert esito.stato == "in_revisione"
    riepilogo = esito.riepilogo
    assert riepilogo.n_post == 12
    # Una chiamata di analisi per gruppo, una di piano, una di testo per post.
    assert [r.tipo for r in riepilogo.per_tipo] == ["analisi", "piano", "testo"]
    assert _tipo(esito, "analisi").chiamate == 1
    assert _tipo(esito, "piano").chiamate == 1
    assert _tipo(esito, "testo").chiamate == 12
    assert riepilogo.costo_totale_usd == 14 * COSTO
    assert _tipo(esito, "testo").costo_usd == 12 * COSTO
    assert (riepilogo.riscritture_piano, riepilogo.riscritture_testi) == (0, 0)
    assert riepilogo.post_segnalati == []


def test_il_tempo_e_quello_del_lancio(db, ai):
    campagna = _campagna(db)
    secondi = iter([100.0, 107.5])

    esito = cli.esegui_prova_ai(
        campagna.id, ora=lambda: ADESSO, cronometro=lambda: next(secondi)
    )

    assert esito.secondi == 7.5


def test_le_riscritture_del_piano_sono_le_chiamate_oltre_la_prima(db, ai):
    ai.comanda_piano_non_valido(2)
    campagna = _campagna(db)

    esito = _prova(campagna.id)

    assert esito.errore is None
    assert _tipo(esito, "piano").chiamate == 3
    assert esito.riepilogo.riscritture_piano == 2


def test_le_riscritture_dei_testi_si_contano_per_post(db, ai):
    ai.comanda_testo("", volte=2, canale="facebook")
    campagna = _campagna(db)

    esito = _prova(campagna.id)

    assert esito.errore is None
    assert esito.riepilogo.riscritture_testi == 2
    assert _tipo(esito, "testo").chiamate == 14
    assert esito.riepilogo.post_segnalati == []


def test_un_post_con_un_blocco_e_nel_rapporto(db, ai):
    ai.comanda_testo("", volte=None, canale="instagram")
    campagna = _campagna(db)

    esito = _prova(campagna.id)

    assert esito.errore is None
    segnalati = esito.riepilogo.post_segnalati
    assert len(segnalati) == 6
    assert {p.canale for p in segnalati} == {"instagram"}
    assert all(p.con_blocco for p in segnalati)
    # Il testo si è riscritto fino al tetto di 3 volte, per ognuno dei 6 post.
    assert esito.riepilogo.riscritture_testi == 18
    rapporto = cli.rapporto_prova_ai(esito)
    assert "Post con blocchi o avvisi: 6" in rapporto
    assert "BLOCCO" in rapporto
    assert db.get(Post, segnalati[0].post_id).da_rivedere


def test_un_errore_ferma_la_prova_e_un_nuovo_lancio_riparte_da_dove_era(db, ai):
    ai.comanda_errore("pianifica_campagna", "configurazione", volte=1)
    campagna = _campagna(db)

    primo = _prova(campagna.id)

    assert primo.errore is not None
    assert "configurazione nella tappa piano" in primo.errore
    assert primo.stato == "in_generazione"
    assert _tipo(primo, "analisi").chiamate == 1  # già fatta e già costata
    assert primo.riepilogo.n_post == 0
    assert "interrotta" in cli.rapporto_prova_ai(primo)

    secondo = _prova(campagna.id)

    assert secondo.errore is None
    assert secondo.stato == "in_revisione"
    assert _tipo(secondo, "analisi").chiamate == 1  # non rifatta
    assert secondo.riepilogo.n_post == 12


def test_una_campagna_non_da_generare_e_rifiutata(db, ai):
    campagna = campagna_in_revisione(db)
    db.commit()

    with pytest.raises(cli.ErroreDominio, match="in_revisione"):
        _prova(campagna.id)


def test_una_campagna_che_non_esiste_e_rifiutata(db, ai):
    with pytest.raises(NonTrovato):
        _prova(999_999)


def test_il_comando_stampa_il_rapporto(db, ai, capsys, monkeypatch):
    campagna = _campagna(db)
    monkeypatch.setattr(cli, "adesso", lambda: ADESSO)

    codice = cli.main(["prova-ai", "--campagna", str(campagna.id)])

    fuori = capsys.readouterr().out
    assert codice == 0
    assert f"campagna {campagna.id}" in fuori
    assert "provider          finto" in fuori
    assert "completata (campagna in_revisione)" in fuori
    assert "analisi" in fuori and "piano" in fuori and "testo" in fuori
    assert "0.1400 $" in fuori  # 14 chiamate da 0,01 $
    assert "costo medio per post: 0.0117 $" in fuori
    assert "Riscritture del piano:  0" in fuori
    assert "Post con blocchi o avvisi: nessuno" in fuori


def test_il_comando_esce_con_1_e_dice_l_errore(db, ai, capsys):
    campagna = campagna_in_revisione(db)
    db.commit()

    codice = cli.main(["prova-ai", "--campagna", str(campagna.id)])

    assert codice == 1
    assert "in_revisione" in capsys.readouterr().err


def test_il_riepilogo_di_una_campagna_senza_chiamate_e_vuoto(db):
    campagna = campagna_in_revisione(db)

    riepilogo = riepilogo_ai_della_campagna(db, campagna.id)

    assert riepilogo.per_tipo == []
    assert riepilogo.costo_totale_usd == 0
    assert (riepilogo.riscritture_piano, riepilogo.riscritture_testi) == (0, 0)
