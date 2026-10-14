"""Test dell'adattatore Meta con HTTP simulato: nessuna chiamata di rete (CA-83)."""

import httpx
import pytest

from app.adapters.social import (
    SocialFinto,
    SocialMeta,
    imposta_social,
    ottieni_social,
)
from app.core.config import leggi_impostazioni

TOKEN = "token-di-prova-molto-segreto"
PAGINA = "1234567890"
IG = "17841400000000000"
FOTO = [b"byte-della-foto"]
URL_FOTO = ["https://pubblico.test/foto.jpg"]
HASHTAG = ["artigianato", "ceramica"]


def _meta(handler, instagram_id: str = IG) -> SocialMeta:
    """SocialMeta su un client httpx con trasporto simulato."""
    return SocialMeta(
        pagina_id=PAGINA,
        token=TOKEN,
        instagram_id=instagram_id,
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        attesa_contenitore=0,
    )


def _errore_graph(codice: int, messaggio: str = "Errore di Meta") -> httpx.Response:
    return httpx.Response(400, json={"error": {"message": messaggio, "code": codice}})


def test_facebook_pubblica_con_foto_e_didascalia():
    richieste = []

    def handler(request: httpx.Request) -> httpx.Response:
        richieste.append(request)
        return httpx.Response(200, json={"id": "f1", "post_id": "123_456"})

    esito = _meta(handler).pubblica(
        "facebook", "Testo del post", HASHTAG, FOTO, URL_FOTO
    )

    assert esito.ok is True
    assert esito.id_esterno == "123_456"
    [richiesta] = richieste
    assert richiesta.url.path == f"/v26.0/{PAGINA}/photos"
    corpo = richiesta.content.decode()
    assert "Testo del post\n\n#artigianato #ceramica" in corpo
    assert b"byte-della-foto" in richiesta.content


def test_instagram_pubblica_con_contenitore_pronto():
    passi = []

    def handler(request: httpx.Request) -> httpx.Response:
        passi.append((request.method, request.url.path))
        if request.url.path.endswith("/media"):
            assert b"https%3A%2F%2Fpubblico.test%2Ffoto.jpg" in request.content
            return httpx.Response(200, json={"id": "cont-1"})
        if request.url.path.endswith("/media_publish"):
            return httpx.Response(200, json={"id": "media-9"})
        return httpx.Response(200, json={"status_code": "FINISHED"})

    esito = _meta(handler).pubblica("instagram", "Testo", HASHTAG, FOTO, URL_FOTO)

    assert esito.ok is True
    assert esito.id_esterno == "media-9"
    metodi = [metodo for metodo, _ in passi]
    assert metodi == ["POST", "GET", "POST"]


def test_instagram_contenitore_non_pronto_riprova_due_volte():
    controlli = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal controlli
        if request.url.path.endswith("/media"):
            return httpx.Response(200, json={"id": "cont-1"})
        controlli += 1
        return httpx.Response(200, json={"status_code": "IN_PROGRESS"})

    esito = _meta(handler).pubblica("instagram", "Testo", HASHTAG, FOTO, URL_FOTO)

    assert esito.ok is False
    assert esito.tipo_errore == "temporaneo"
    # Primo controllo + due nuovi tentativi (brief-meta §5)
    assert controlli == 3


def test_instagram_contenitore_diventa_pronto_al_secondo_controllo():
    stati = iter(["IN_PROGRESS", "FINISHED"])

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/media"):
            return httpx.Response(200, json={"id": "cont-1"})
        if request.url.path.endswith("/media_publish"):
            return httpx.Response(200, json={"id": "media-9"})
        return httpx.Response(200, json={"status_code": next(stati)})

    esito = _meta(handler).pubblica("instagram", "Testo", HASHTAG, FOTO, URL_FOTO)

    assert esito.ok is True
    assert esito.id_esterno == "media-9"


def test_instagram_contenitore_in_errore_e_definitivo():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/media"):
            return httpx.Response(200, json={"id": "cont-1"})
        return httpx.Response(200, json={"status_code": "ERROR"})

    esito = _meta(handler).pubblica("instagram", "Testo", HASHTAG, FOTO, URL_FOTO)

    assert esito.ok is False
    assert esito.tipo_errore == "definitivo"


def test_instagram_senza_url_assoluto_fallisce_senza_chiamate():
    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("Nessuna chiamata di rete attesa")

    esito = _meta(handler).pubblica(
        "instagram", "Testo", HASHTAG, FOTO, ["/api/foto/1/pubblica?firma=x"]
    )

    assert esito.ok is False
    assert esito.tipo_errore == "definitivo"
    assert "FOTO_URL_PUBBLICO" in esito.errore


def test_instagram_senza_id_ripiega_sul_finto():
    meta = _meta(
        lambda request: (_ for _ in ()).throw(
            AssertionError("Nessuna chiamata di rete attesa")
        ),
        instagram_id="",
    )

    esito = meta.pubblica("instagram", "Testo", HASHTAG, FOTO, URL_FOTO)

    assert esito.ok is True
    assert esito.id_esterno == "finto-1"
    assert isinstance(meta._finto, SocialFinto)


def test_timeout_e_errore_temporaneo():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("timeout", request=request)

    esito = _meta(handler).pubblica("facebook", "Testo", HASHTAG, FOTO, URL_FOTO)

    assert esito.ok is False
    assert esito.tipo_errore == "temporaneo"
    assert TOKEN not in (esito.errore or "")


def test_5xx_e_errore_temporaneo():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="Service Unavailable")

    esito = _meta(handler).pubblica("facebook", "Testo", HASHTAG, FOTO, URL_FOTO)

    assert esito.ok is False
    assert esito.tipo_errore == "temporaneo"


@pytest.mark.parametrize("codice", [1, 2, 4, 17, 32, 613])
def test_codici_graph_di_limite_sono_temporanei(codice: int):
    def handler(request: httpx.Request) -> httpx.Response:
        return _errore_graph(codice)

    esito = _meta(handler).pubblica("facebook", "Testo", HASHTAG, FOTO, URL_FOTO)

    assert esito.ok is False
    assert esito.tipo_errore == "temporaneo", f"codice {codice}"


@pytest.mark.parametrize("codice", [190, 10, 200, 100, 36003])
def test_altri_codici_graph_sono_definitivi(codice: int):
    def handler(request: httpx.Request) -> httpx.Response:
        return _errore_graph(codice, messaggio=f"Motivo {codice}")

    esito = _meta(handler).pubblica("facebook", "Testo", HASHTAG, FOTO, URL_FOTO)

    assert esito.ok is False
    assert esito.tipo_errore == "definitivo", f"codice {codice}"
    assert esito.errore == f"Motivo {codice}"


def test_il_token_non_finisce_mai_nel_messaggio():
    def handler(request: httpx.Request) -> httpx.Response:
        return _errore_graph(190, messaggio=f"Token {TOKEN} non valido")

    esito = _meta(handler).pubblica("facebook", "Testo", HASHTAG, FOTO, URL_FOTO)

    assert esito.ok is False
    assert TOKEN not in esito.errore
    assert "***" in esito.errore


def test_risposta_200_senza_id_e_definitivo():
    """Una risposta ok ma senza id non deve propagare un KeyError nel tick."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"unexpected": True})

    for canale in ("facebook", "instagram"):
        esito = _meta(handler).pubblica(canale, "Testo", HASHTAG, FOTO, URL_FOTO)
        assert esito.ok is False
        assert esito.tipo_errore == "definitivo"


def test_canale_non_gestito_e_definitivo():
    esito = _meta(lambda request: httpx.Response(500)).pubblica(
        "tiktok", "Testo", HASHTAG, FOTO, URL_FOTO
    )

    assert esito.ok is False
    assert esito.tipo_errore == "definitivo"


def test_senza_config_meta_errore_chiaro():
    with pytest.raises(ValueError, match="META_PAGINA_ID"):
        SocialMeta(pagina_id="", token="")


def test_ottieni_social_con_provider_meta(monkeypatch):
    impostazioni = leggi_impostazioni()
    monkeypatch.setattr(impostazioni, "social_provider", "meta")
    monkeypatch.setattr(impostazioni, "meta_pagina_id", PAGINA)
    monkeypatch.setattr(impostazioni, "meta_token_pagina", TOKEN)
    monkeypatch.setattr(impostazioni, "meta_instagram_id", IG)
    imposta_social(None)
    try:
        assert isinstance(ottieni_social(), SocialMeta)
    finally:
        imposta_social(None)


def test_didascalia_senza_hashtag():
    def handler(request: httpx.Request) -> httpx.Response:
        assert b"Testo semplice" in request.content
        assert b"#" not in request.content
        return httpx.Response(200, json={"post_id": "p1"})

    esito = _meta(handler).pubblica("facebook", "Testo semplice", [], FOTO, URL_FOTO)
    assert esito.ok is True
