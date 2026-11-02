"""T3-925: `prova-prompt` clona una campagna di prova, la genera e la confronta con l'originale.

Con il provider e l'archivio finti: nessuna chiamata reale (la prova vera si
lancia a mano, con `AI_PROVIDER=litellm` in `backend/.env`).
"""

from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date, datetime, timezone
from decimal import Decimal
from io import BytesIO
from types import SimpleNamespace

import pytest
from PIL import Image
from sqlalchemy.orm import Session

from app import cli
from app.adapters.ai import AIFinto, usa_ai
from app.adapters.archivio import ArchivioFinto, usa_archivio
from app.core.coda import GENERA_CAMPAGNA
from app.moduli.campagne import service as campagne
from app.moduli.campagne.schemas import CampagnaCrea, GruppoCrea
from app.moduli.contenuti.service import riepilogo_ai_della_campagna
from tests.moduli.artigiani.fabbrica import profilo

ADESSO = datetime(2030, 1, 1, 9, tzinfo=timezone.utc)
COSTO = Decimal("0.01")


@pytest.fixture
def finti() -> Iterator[SimpleNamespace]:
    ai, archivio = AIFinto(costo_chiamata=COSTO), ArchivioFinto()
    with usa_ai(ai), usa_archivio(archivio):
        yield SimpleNamespace(ai=ai, archivio=archivio)


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


def _jpeg(tinta: int) -> bytes:
    uscita = BytesIO()
    Image.new("RGB", (1080, 1350), (tinta, 120, 90)).save(uscita, "JPEG")
    return uscita.getvalue()


def _origine(db: Session, *, n_foto: int = 3):
    """Una campagna di 14 giorni, 3 post a settimana su due canali, già generata."""
    bottega = profilo(
        db,
        nome="Ceramiche Bianchi",
        canali=["facebook", "instagram"],
        frequenza="f3_4",
    )
    bozza = campagne.crea_bozza(
        db,
        bottega.utente_id,
        CampagnaCrea(
            titolo="Autunno in bottega",
            inizio=date(2030, 1, 10),
            fine=date(2030, 1, 23),
            descrizione="I piatti nuovi.",
            canali=["facebook", "instagram"],
        ),
        ADESSO,
    )
    gruppo = campagne.crea_gruppo(
        db,
        bottega.utente_id,
        "artigiano",
        bozza.id,
        GruppoCrea(descrizione="Piatti sul banco", da_usare_il=date(2030, 1, 15)),
    )
    for tinta in range(n_foto):
        campagne.carica_foto(
            db, bottega.utente_id, "artigiano", bozza.id, _jpeg(40 * tinta), gruppo.id
        )
    campagne.invia_campagna(db, bottega.utente_id, bozza.id, ADESSO, dichiarazione=True)
    db.commit()
    return bozza


def test_la_copia_ha_bottega_canali_durata_gruppi_e_foto(db, finti, coda):
    origine = _origine(db)

    esito = cli.clona_e_invia(db, origine.id, ADESSO)

    nuova = campagne.campagna(db, esito.campagna_id)
    assert nuova.id != origine.id and nuova.profilo_id == origine.profilo_id
    assert nuova.titolo == "Autunno in bottega · prova prompt"
    assert nuova.stato == "inviata"
    assert list(nuova.canali) == ["facebook", "instagram"]
    assert nuova.descrizione == "I piatti nuovi."
    # Inizio tra 4 giorni, stessa durata; la data «da usare» si sposta con il periodo.
    assert nuova.inizio == date(2030, 1, 5)
    assert nuova.fine - nuova.inizio == origine.fine - origine.inizio
    [gruppo] = campagne.gruppi_della_campagna(db, nuova.id)
    assert gruppo.descrizione == "Piatti sul banco"
    assert gruppo.da_usare_il == date(2030, 1, 10)
    assert (esito.caricate, esito.scartate) == (3, [])
    assert len(gruppo.foto) == 3
    # La campagna di partenza non cambia.
    assert campagne.campagna(db, origine.id).inizio == date(2030, 1, 10)
    assert len(campagne.gruppi_della_campagna(db, origine.id)[0].foto) == 3
    # L'invio ha messo in coda la generazione della copia, e solo di quella.
    argomenti = [
        job["args"]["campagna_id"]
        for job in coda.jobs.values()
        if job["task_name"] == GENERA_CAMPAGNA
    ]
    assert esito.campagna_id in argomenti and origine.id in argomenti


def test_una_foto_che_non_supera_i_controlli_si_scarta_con_il_motivo(db, finti):
    origine = _origine(db)
    [gruppo] = campagne.gruppi_della_campagna(db, origine.id)
    guasta = gruppo.foto[1]
    finti.archivio._archivio[guasta.file] = b"non e una foto"

    esito = cli.clona_e_invia(db, origine.id, ADESSO)

    assert esito.caricate == 2
    assert [foto_id for foto_id, _ in esito.scartate] == [guasta.id]
    assert esito.scartate[0][1]


def test_la_prova_confronta_la_copia_con_l_originale(db, finti):
    origine = _origine(db)
    assert cli.esegui_prova_ai(origine.id, ora=lambda: ADESSO).errore is None
    with cli.transazione() as sessione:
        prima = riepilogo_ai_della_campagna(sessione, origine.id)
    esito = cli.clona_e_invia(db, origine.id, ADESSO)

    prova = cli.esegui_prova_ai(esito.campagna_id, ora=lambda: ADESSO)

    assert prova.errore is None and prova.stato == "in_revisione"
    rapporto = cli.rapporto_confronto(prima, prova.riepilogo)
    assert f"campagna {origine.id} (prima) e {esito.campagna_id} (adesso)" in rapporto
    # Stessa bottega e stessa durata: 12 post, 1 analisi, 1 piano, 12 testi e 3 immagini per parte.
    assert prima.n_post == prova.riepilogo.n_post == 12
    righe = {riga.split()[0]: riga.split()[1:] for riga in rapporto.splitlines()[2:6]}
    assert righe["analisi"][:2] == ["1", "1"]
    assert righe["piano"][:2] == ["1", "1"]
    assert righe["testo"][:2] == ["12", "12"]
    # Analisi, piano, 12 testi e 3 immagini AI: 17 chiamate da 0,01 $ per parte.
    assert rapporto.splitlines()[6].split()[1:] == ["0.1700", "$", "0.1700", "$"]
    assert "Riscritture del piano:      0 · 0" in rapporto


def test_il_comando_stampa_la_copia_il_rapporto_e_il_confronto(
    db, finti, capsys, monkeypatch
):
    origine = _origine(db)
    monkeypatch.setattr(cli, "adesso", lambda: ADESSO)

    codice = cli.main(["prova-prompt", "--da-campagna", str(origine.id)])

    fuori = capsys.readouterr().out
    assert codice == 0
    assert "inviata: 3 foto copiate." in fuori
    assert "Prova AI · campagna" in fuori and "Confronto · campagna" in fuori
