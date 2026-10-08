"""Test dell'adattatore social finto: nessuna chiamata di rete."""

import pytest

from app.adapters.social import (
    SocialAdapter,
    SocialFinto,
    ottieni_social,
    usa_social,
)

FOTO = [b"foto-uno", b"foto-due"]
HASHTAG = ["artigianato", "ceramica"]


def test_ottieni_social_restituisce_il_finto():
    assert isinstance(ottieni_social(), SocialFinto)


def test_ottieni_social_restituisce_sempre_la_stessa_istanza():
    assert ottieni_social() is ottieni_social()


def test_pubblica_con_una_o_piu_foto():
    finto = SocialFinto()

    esito = finto.pubblica("Testo del post", HASHTAG, FOTO[:1])
    assert esito.ok is True
    assert esito.id_esterno == "finto-1"
    assert esito.errore is None
    assert esito.tipo_errore is None

    esito = finto.pubblica("Altro post", HASHTAG, FOTO)
    assert esito.ok is True
    assert esito.id_esterno == "finto-2"


def test_pubblica_registra_testo_hashtag_e_numero_di_foto():
    finto = SocialFinto()
    finto.pubblica("Testo del post", HASHTAG, FOTO)

    assert finto.pubblicazioni == [
        {"testo": "Testo del post", "hashtag": HASHTAG, "n_foto": 2}
    ]


def test_pubblica_senza_foto_non_ammessa():
    with pytest.raises(ValueError, match="almeno una foto"):
        SocialFinto().pubblica("Solo testo", HASHTAG, [])


def test_pubblica_errore_temporaneo_a_comando():
    esito = SocialFinto().pubblica("Post con FAIL_TEMP nel testo", HASHTAG, FOTO)

    assert esito.ok is False
    assert esito.errore == "Errore temporaneo simulato"
    assert esito.tipo_errore == "temporaneo"
    assert esito.id_esterno is None


def test_pubblica_errore_definitivo_a_comando():
    esito = SocialFinto().pubblica("Post con FAIL_DEF nel testo", HASHTAG, FOTO)

    assert esito.ok is False
    assert esito.errore == "Errore definitivo simulato"
    assert esito.tipo_errore == "definitivo"
    assert esito.id_esterno is None


def test_usa_social_sostituisce_e_ripristina():
    originale = ottieni_social()
    finto = SocialFinto()
    with usa_social(finto):
        assert ottieni_social() is finto
    assert ottieni_social() is originale


def test_usa_social_ripristina_anche_in_caso_di_errore():
    originale = ottieni_social()
    with pytest.raises(RuntimeError):
        with usa_social(SocialFinto()):
            raise RuntimeError("boom")
    assert ottieni_social() is originale


def test_social_finto_e_un_adattatore_social():
    assert isinstance(SocialFinto(), SocialAdapter)
