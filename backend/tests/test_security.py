"""core/security.py: password con scrypt e token di sessione."""
import pytest

from app.core.security import (
    genera_token,
    hash_password,
    hash_token,
    verifica_password,
)


@pytest.fixture(scope="module")
def hash_di_esempio() -> str:
    return hash_password("Segreta!2026")


def test_hash_password_ha_il_formato_scrypt(hash_di_esempio: str) -> None:
    schema, n, r, p, salt, digest = hash_di_esempio.split("$")
    assert (schema, n, r, p) == ("scrypt", "16384", "8", "1")
    assert len(bytes.fromhex(salt)) == 16
    assert len(bytes.fromhex(digest)) == 64
    assert "Segreta!2026" not in hash_di_esempio


def test_verifica_password_accetta_quella_giusta(hash_di_esempio: str) -> None:
    assert verifica_password("Segreta!2026", hash_di_esempio)


def test_verifica_password_rifiuta_quella_sbagliata(hash_di_esempio: str) -> None:
    assert not verifica_password("segreta!2026", hash_di_esempio)


def test_stessa_password_hash_diversi(hash_di_esempio: str) -> None:
    assert hash_password("Segreta!2026") != hash_di_esempio


@pytest.mark.parametrize(
    "malformato",
    [
        "",
        "non-un-hash",
        "bcrypt$16384$8$1$00$00",
        "scrypt$16384$8$1$zz$zz",
        "scrypt$x$8$1$00$00",
        "scrypt$3$8$1$00$00",
        "scrypt$1073741824$8$1$00$00",
        "scrypt$16384$8$1$00",
    ],
)
def test_verifica_password_rifiuta_un_hash_malformato(malformato: str) -> None:
    assert not verifica_password("Segreta!2026", malformato)


def test_genera_token_e_casuale() -> None:
    assert genera_token() != genera_token()
    assert len(genera_token()) >= 43


def test_hash_token_e_sha256_stabile() -> None:
    token = genera_token()
    assert hash_token(token) == hash_token(token)
    assert len(hash_token(token)) == 64
    assert hash_token(token) != token
    assert (
        hash_token("abc")
        == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    )
