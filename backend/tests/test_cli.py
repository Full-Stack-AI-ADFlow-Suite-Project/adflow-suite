"""cli.py: seed, demo e comando crea-utente."""
import json
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date, datetime, timezone
from pathlib import Path

import pytest
from PIL import Image
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import cli
from app.adapters.archivio import ArchivioFinto, usa_archivio
from app.core.errori import DatiNonValidi, StatoNonValido
from app.core.security import verifica_password
from app.moduli.accesso.models import Utente
from app.moduli.artigiani import domain
from app.moduli.artigiani.models import ProfiloBottega
from app.moduli.artigiani.service import canali_collegati, profilo_di
from app.moduli.campagne.domain import BOZZA
from app.moduli.campagne.models import Campagna
from app.moduli.campagne.service import foto_della_campagna
from tests.moduli.accesso.fabbrica import utente

PASSWORD = "PasswordDelSeed!2026"


@pytest.fixture
def cli_sul_db_di_test(db: Session, monkeypatch: pytest.MonkeyPatch) -> None:
    """La riga di comando usa la sessione del test e non chiede nulla a terminale."""

    @contextmanager
    def transazione() -> Iterator[Session]:
        yield db

    monkeypatch.setattr(cli, "transazione", transazione)
    monkeypatch.setattr(cli, "getpass", lambda _: PASSWORD)


def _del_seed(db: Session) -> dict[str, Utente]:
    email = [email for email, _, _ in cli.UTENTI_SEED]
    trovati = db.scalars(select(Utente).where(Utente.email.in_(email)))
    return {u.ruolo: u for u in trovati}


def test_seed_crea_artigiano_operatore_e_admin(db: Session) -> None:
    creati = cli.esegui_seed(db, PASSWORD)

    utenti = _del_seed(db)
    assert set(utenti) == {"artigiano", "operatore", "admin"}
    assert len(creati) == 3
    for record in utenti.values():
        assert record.attivo
        assert verifica_password(PASSWORD, record.password_hash)
        assert PASSWORD not in record.password_hash


def test_seed_da_il_profilo_solo_all_artigiano(db: Session) -> None:
    cli.esegui_seed(db, PASSWORD)

    utenti = _del_seed(db)
    assert profilo_di(db, utenti["artigiano"].id) is not None
    assert profilo_di(db, utenti["operatore"].id) is None
    assert profilo_di(db, utenti["admin"].id) is None


def test_il_profilo_del_seed_usa_i_valori_ammessi(db: Session) -> None:
    cli.esegui_seed(db, PASSWORD)
    profilo = profilo_di(db, _del_seed(db)["artigiano"].id)

    for campo in domain.OBBLIGATORI:
        assert getattr(profilo, campo)
    assert profilo.tipo_prodotto in domain.TIPI_PRODOTTO
    assert profilo.obiettivo in domain.OBIETTIVI
    assert profilo.fascia_prezzo in domain.FASCE_PREZZO
    assert profilo.cortesia in domain.CORTESIE
    assert profilo.frequenza in domain.FREQUENZE
    assert set(profilo.canali) <= set(domain.CANALI)
    assert set(profilo.valori) <= set(domain.VALORI)
    assert set(profilo.tono) <= set(domain.TONI)
    assert set(profilo.social_esistenti["canali"]) <= set(
        domain.CANALI_SOCIAL_ESISTENTI
    )
    assert profilo.foto_policy["quantita_mese"] in domain.FOTO_QUANTITA_MESE
    assert profilo.foto_policy["chi_scatta"] in domain.FOTO_CHI_SCATTA
    assert profilo.foto_policy["persone"] in domain.FOTO_PERSONE
    assert all(e["tipo"] in domain.TIPI_EVENTO for e in profilo.eventi_ricorrenti)


def test_seed_si_puo_rilanciare(db: Session) -> None:
    cli.esegui_seed(db, PASSWORD)
    hash_prima = _del_seed(db)["admin"].password_hash

    assert cli.esegui_seed(db, "UnAltraPassword!2026") == []

    assert len(_del_seed(db)) == 3
    assert _del_seed(db)["admin"].password_hash == hash_prima
    assert db.scalar(select(func.count()).select_from(ProfiloBottega)) == 1


def test_comando_seed(
    db: Session, cli_sul_db_di_test: None, capsys: pytest.CaptureFixture[str]
) -> None:
    assert cli.main(["seed"]) == 0

    assert len(_del_seed(db)) == 3
    uscita = capsys.readouterr().out
    assert "artigiano@example.com (creato)" in uscita
    assert PASSWORD not in uscita


def test_comando_crea_utente_chiama_il_service_di_accesso(
    db: Session,
    cli_sul_db_di_test: None,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    chiamate = []

    def crea_utente_finto(db, email, password, nome, ruolo):
        chiamate.append((db, email, password, nome, ruolo))
        return utente(db, ruolo, email=email, nome=nome)

    monkeypatch.setattr(cli, "crea_utente", crea_utente_finto)

    argomenti = ["--email", "nuovo@example.com", "--nome", "Nuovo", "--ruolo", "admin"]
    assert cli.main(["crea-utente", *argomenti]) == 0

    assert chiamate == [(db, "nuovo@example.com", PASSWORD, "Nuovo", "admin")]
    uscita = capsys.readouterr().out
    assert "nuovo@example.com" in uscita
    assert PASSWORD not in uscita


def test_comando_crea_utente_mostra_l_errore_del_service(
    cli_sul_db_di_test: None,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def crea_utente_finto(*_):
        raise DatiNonValidi("Email già registrata.")

    monkeypatch.setattr(cli, "crea_utente", crea_utente_finto)

    argomenti = [
        "--email",
        "doppio@example.com",
        "--nome",
        "Doppio",
        "--ruolo",
        "admin",
    ]
    assert cli.main(["crea-utente", *argomenti]) == 1
    assert "Email già registrata." in capsys.readouterr().err


def test_comando_crea_utente_vuole_tutti_gli_argomenti(
    cli_sul_db_di_test: None,
) -> None:
    with pytest.raises(SystemExit):
        cli.main(["crea-utente", "--email", "x@example.com", "--nome", "X"])


def test_password_non_confermata(monkeypatch: pytest.MonkeyPatch) -> None:
    risposte = iter(["una", "altra"])
    monkeypatch.setattr(cli, "getpass", lambda _: next(risposte))
    with pytest.raises(SystemExit):
        cli.main(["seed"])


# --- demo (T3-06) -----------------------------------------------------------

ORA_DEMO = datetime(2030, 1, 10, 9, 0, tzinfo=timezone.utc)


def _jpeg(percorso: Path, lato: int) -> None:
    Image.new("RGB", (lato, lato), (150, 90, 40)).save(percorso, "JPEG")


@pytest.fixture
def cartella_demo(tmp_path: Path) -> Iterator[Path]:
    """Tre foto valide, una troppo piccola e un file che non è un'immagine."""
    for nome in ("a.jpg", "c.jpg", "e.jpg"):
        _jpeg(tmp_path / nome, 1200)
    _jpeg(tmp_path / "b-piccola.jpg", 800)
    (tmp_path / "d-nota.txt").write_text("non è una foto")
    with usa_archivio(ArchivioFinto()):
        yield tmp_path


def test_demo_prepara_bottega_e_campagna_in_bozza(
    db: Session, cartella_demo: Path
) -> None:
    esito = cli.esegui_demo(db, PASSWORD, cartella_demo, 2, ORA_DEMO)

    assert esito.creati == [*(e for e, _, _ in cli.UTENTI_SEED), cli.DEMO_EMAIL]
    artigiano = db.scalar(select(Utente).where(Utente.email == cli.DEMO_EMAIL))
    assert artigiano.ruolo == "artigiano"
    assert verifica_password(PASSWORD, artigiano.password_hash)
    profilo = profilo_di(db, artigiano.id)
    assert profilo.nome == cli.PROFILO_SEED["nome"]
    assert artigiano.nome == cli.PROFILO_SEED["referente"]
    assert set(canali_collegati(db, profilo.id)) == {"facebook", "instagram"}

    campagna = db.get(Campagna, esito.campagna_id)
    assert campagna.stato == BOZZA
    assert campagna.profilo_id == profilo.id
    assert campagna.inizio == date(2030, 1, 14)
    assert (campagna.fine - campagna.inizio).days + 1 == 7
    assert esito.caricate == ["a.jpg", "c.jpg"]
    assert [nome for nome, _ in esito.scartate] == ["b-piccola.jpg"]
    assert len(foto_della_campagna(db, campagna.id)) == 2


def test_demo_con_zero_carica_tutte_le_foto_valide(
    db: Session, cartella_demo: Path
) -> None:
    esito = cli.esegui_demo(db, PASSWORD, cartella_demo, 0, ORA_DEMO)

    assert esito.caricate == ["a.jpg", "c.jpg", "e.jpg"]
    assert [nome for nome, _ in esito.scartate] == ["b-piccola.jpg", "d-nota.txt"]
    assert all(motivo for _, motivo in esito.scartate)


def test_demo_di_default_lascia_due_post_alle_immagini_ai(
    db: Session, cartella_demo: Path
) -> None:
    esito = cli.esegui_demo(db, PASSWORD, cartella_demo, None, ORA_DEMO)

    # Seed: 3 post a settimana, 7 giorni → 3 post per canale, 1 foto.
    assert esito.post_per_canale == 3
    assert esito.caricate == ["a.jpg"]


def test_demo_json_sostituisce_profilo_campagna_e_gruppo(
    db: Session, cartella_demo: Path
) -> None:
    (cartella_demo / cli.FILE_DEMO).write_text(
        json.dumps(
            {
                "profilo": {"nome": "Mosaici d'Arte", "frequenza": "f5_piu"},
                "campagna": {"titolo": "Collezione d'autunno"},
                "gruppo": "Ritratti in mosaico",
            }
        ),
        encoding="utf-8",
    )

    esito = cli.esegui_demo(db, PASSWORD, cartella_demo, None, ORA_DEMO)

    campagna = db.get(Campagna, esito.campagna_id)
    assert campagna.titolo == "Collezione d'autunno"
    assert esito.post_per_canale == 5
    assert esito.caricate == ["a.jpg", "c.jpg", "e.jpg"]
    assert cli.FILE_DEMO not in [nome for nome, _ in esito.scartate]
    artigiano = db.scalar(select(Utente).where(Utente.email == cli.DEMO_EMAIL))
    assert profilo_di(db, artigiano.id).nome == "Mosaici d'Arte"
    assert profilo_di(db, artigiano.id).citta == cli.PROFILO_SEED["citta"]


@pytest.mark.parametrize(
    "contenuto",
    ["{non json", '{"altro": 1}', '{"profilo": {"tipo_prodotto": "astronavi"}}'],
)
def test_demo_json_non_valido(db: Session, cartella_demo: Path, contenuto: str) -> None:
    (cartella_demo / cli.FILE_DEMO).write_text(contenuto, encoding="utf-8")

    with pytest.raises(DatiNonValidi):
        cli.esegui_demo(db, PASSWORD, cartella_demo, None, ORA_DEMO)


def test_demo_si_prepara_una_volta_sola(db: Session, cartella_demo: Path) -> None:
    cli.esegui_demo(db, PASSWORD, cartella_demo, 1, ORA_DEMO)

    with pytest.raises(StatoNonValido):
        cli.esegui_demo(db, PASSWORD, cartella_demo, 1, ORA_DEMO)


def test_demo_vuole_una_cartella_che_esiste(db: Session, tmp_path: Path) -> None:
    with pytest.raises(DatiNonValidi):
        cli.esegui_demo(db, PASSWORD, tmp_path / "manca", 1, ORA_DEMO)


def test_comando_demo(
    db: Session,
    cli_sul_db_di_test: None,
    cartella_demo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert cli.main(["demo", "--foto", str(cartella_demo), "--quante", "1"]) == 0

    uscita = capsys.readouterr().out
    assert f"utente creato: {cli.DEMO_EMAIL}" in uscita
    assert "caricata  a.jpg" in uscita
    assert PASSWORD not in uscita
