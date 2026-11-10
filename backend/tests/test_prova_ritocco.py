"""RT-32: `prova-ritocco` carica una cartella di foto, genera la campagna e scrive rapporto e foglio.

Con il provider e l'archivio finti: nessuna chiamata reale (la prova vera si lancia
a mano, con `AI_PROVIDER=litellm` in `backend/.env`).
"""

import json
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timezone
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace

import pytest
from PIL import Image
from sqlalchemy.orm import Session

from app import cli, prova_ritocco
from app.adapters.ai import AIFinto, usa_ai
from app.adapters.archivio import ArchivioFinto, usa_archivio
from app.core.errori import DatiNonValidi
from app.moduli.accesso.models import Utente
from tests.moduli.artigiani.fabbrica import profilo

ADESSO = datetime(2030, 1, 1, 9, tzinfo=timezone.utc)


@pytest.fixture
def finti() -> Iterator[SimpleNamespace]:
    ai, archivio = AIFinto(costo_chiamata=Decimal("0.01")), ArchivioFinto()
    with usa_ai(ai), usa_archivio(archivio):
        yield SimpleNamespace(ai=ai, archivio=archivio)


@pytest.fixture(autouse=True)
def cli_sul_db_di_test(db: Session, monkeypatch: pytest.MonkeyPatch) -> None:
    @contextmanager
    def transazione() -> Iterator[Session]:
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise

    monkeypatch.setattr(cli, "transazione", transazione)


def _cartella(tmp_path: Path, quante: int = 2) -> Path:
    cartella = tmp_path / "foto"
    cartella.mkdir()
    for n in range(quante):
        uscita = BytesIO()
        Image.new("RGB", (1080, 1350), (40 * n + 30, 120, 90)).save(uscita, "JPEG")
        (cartella / f"foto{n}.jpg").write_bytes(uscita.getvalue())
    (cartella / "note.txt").write_text("non è una foto")
    return cartella


def _email(db: Session) -> str:
    bottega = profilo(db, canali=["facebook", "instagram"], frequenza="f3_4")
    db.commit()
    return db.get(Utente, bottega.utente_id).email


def test_il_rapporto_e_il_foglio_con_tre_immagini_per_foto(db, finti, tmp_path):
    email = _email(db)

    esito = cli.esegui_prova_ritocco(
        _cartella(tmp_path), email, None, ora=lambda: ADESSO
    )

    assert esito.prova.errore is None and esito.caricate == 2
    assert "Prova ritocco · campagna" in esito.rapporto
    assert "in cache" in esito.rapporto and "totale" in esito.rapporto
    for nome in ("foto0.jpg", "foto1.jpg"):
        assert nome in esito.rapporto
        # Originale, Standard e Spinta di ogni foto, incorporate nel foglio.
        assert esito.foglio.count(f'alt="{nome} ·') == 3
    assert esito.foglio.count("data:image/jpeg;base64,") == 6
    assert "Confronto con la verità" not in esito.rapporto


def test_il_confronto_con_la_verita_misura_riquadri_note_e_volti(db, finti, tmp_path):
    email = _email(db)
    verita = tmp_path / "verita.json"
    verita.write_text(
        json.dumps(
            {
                "foto0.jpg": {
                    "soggetto": [0.1, 0.1, 0.8, 0.8],
                    "volti": 1,
                    "note": ["scura"],
                }
            }
        )
    )

    esito = cli.esegui_prova_ritocco(
        _cartella(tmp_path), email, verita, ora=lambda: ADESSO
    )

    assert "Confronto con la verità" in esito.rapporto
    assert "richiamo dei volti" in esito.rapporto


def test_una_cartella_senza_foto_valide_si_rifiuta(db, tmp_path):
    email = _email(db)
    vuota = tmp_path / "vuota"
    vuota.mkdir()
    with pytest.raises(DatiNonValidi):
        prova_ritocco.carica_cartella(db, vuota, email, ADESSO)
    with pytest.raises(DatiNonValidi):
        prova_ritocco.carica_cartella(db, tmp_path / "manca", email, ADESSO)
    with pytest.raises(DatiNonValidi):
        prova_ritocco.carica_cartella(db, vuota, "nessuno@esempio.it", ADESSO)


def test_un_file_di_verita_illeggibile_e_un_errore_chiaro(tmp_path):
    guasto = tmp_path / "v.json"
    guasto.write_text("[1, 2")
    with pytest.raises(DatiNonValidi):
        prova_ritocco.leggi_verita(guasto)


def test_sovrapposizione_e_errore_degli_angoli():
    riquadro = {"x": 0.0, "y": 0.0, "larghezza": 0.5, "altezza": 0.5}
    assert prova_ritocco.sovrapposizione(riquadro, [0, 0, 0.5, 0.5]) == pytest.approx(1)
    assert prova_ritocco.sovrapposizione(riquadro, [0.5, 0.5, 0.5, 0.5]) == 0
    angoli = [[0.1, 0.1], [0.9, 0.1], [0.9, 0.9], [0.1, 0.9]]
    ruotati = angoli[2:] + angoli[:2]  # stessi angoli, altro ordine
    assert prova_ritocco.errore_angoli(ruotati, angoli, 1000, 1000) == pytest.approx(0)
    spostati = [[x + 0.01, y] for x, y in angoli]
    assert prova_ritocco.errore_angoli(spostati, angoli, 1000, 1000) == pytest.approx(1)
