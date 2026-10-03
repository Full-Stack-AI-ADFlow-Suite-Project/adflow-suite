"""cli.py: seed e comando crea-utente."""
from collections.abc import Iterator
from contextlib import contextmanager

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import cli
from app.core.errori import DatiNonValidi
from app.core.security import verifica_password
from app.moduli.accesso.models import Utente
from app.moduli.artigiani import domain
from app.moduli.artigiani.models import ProfiloBottega
from app.moduli.artigiani.service import profilo_di
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
