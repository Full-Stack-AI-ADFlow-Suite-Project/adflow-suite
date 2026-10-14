"""Adattatore Meta: pubblicazione su Facebook e Instagram via Graph API (T3-42, brief-meta).

Nell'MVP esiste una sola Pagina di prova, da ``.env`` (``META_PAGINA_ID``,
``META_INSTAGRAM_ID``, ``META_TOKEN_PAGINA``, ``META_GRAPH_VERSIONE``); la
tabella ``account_social`` non si legge. Se ``META_INSTAGRAM_ID`` è vuoto il
canale Instagram passa al finto (ripiego di D1, perimetro-mvp).

- Facebook: ``POST /{pagina}/photos`` con la foto caricata (``source``) e
  ``message`` → ``id_esterno`` è ``post_id``.
- Instagram: ``POST /{ig}/media`` con ``image_url`` e ``caption`` → id del
  contenitore; quando lo stato è ``FINISHED``, ``POST /{ig}/media_publish``
  con ``creation_id``. Se il contenitore non è pronto, due nuovi tentativi a
  pochi secondi, poi errore ``temporaneo``: il prossimo tick riprova con un
  contenitore nuovo. Niente attese lunghe nel tick.

Errori: timeout, connessione, 5xx e i codici Graph di limite o temporanei
(1, 2, 4, 17, 32, 613) → ``temporaneo``; token non valido (190), permessi
(10, 200), parametri (100) e il resto → ``definitivo``, con il messaggio di
Meta. Il token non finisce mai nei messaggi restituiti.
"""

import time
from typing import Final

import httpx

from .base import EsitoPubblicazione, SocialAdapter
from .finto import SocialFinto

URL_GRAPH = "https://graph.facebook.com"
# Codici Graph di limite o temporanei (brief-meta §6)
CODICI_TEMPORANEI: Final[frozenset[int]] = frozenset({1, 2, 4, 17, 32, 613})
# Controlli dello stato del contenitore: il primo più due nuovi tentativi
CONTENITORE_CONTROLLI: Final[int] = 3
CONTENITORE_ATTESA_SECONDI: Final[float] = 3.0


class SocialMeta(SocialAdapter):
    """Pubblica sulla Pagina di prova e sull'account Instagram collegato."""

    def __init__(
        self,
        pagina_id: str,
        token: str,
        instagram_id: str = "",
        versione_graf: str = "v26.0",
        client: httpx.Client | None = None,
        attesa_contenitore: float = CONTENITORE_ATTESA_SECONDI,
    ) -> None:
        if not pagina_id or not token:
            raise ValueError(
                "SOCIAL_PROVIDER=meta richiede META_PAGINA_ID e "
                "META_TOKEN_PAGINA in backend/.env."
            )
        self._pagina_id = pagina_id
        self._instagram_id = instagram_id
        self._token = token
        self._base = f"{URL_GRAPH}/{versione_graf.strip('/')}"
        self._client = client or httpx.Client(timeout=30)
        self._attesa_contenitore = attesa_contenitore
        # Ripiego D1: senza META_INSTAGRAM_ID il canale Instagram resta simulato
        self._finto = SocialFinto()

    def pubblica(
        self,
        canale: str,
        testo: str,
        hashtag: list[str],
        foto: list[bytes],
        url_foto: list[str],
    ) -> EsitoPubblicazione:
        if not foto:
            raise ValueError("La pubblicazione richiede almeno una foto.")
        didascalia = _didascalia(testo, hashtag)
        if canale == "facebook":
            return self._facebook(didascalia, foto)
        if canale == "instagram":
            if not self._instagram_id:
                return self._finto.pubblica(canale, testo, hashtag, foto, url_foto)
            return self._instagram(didascalia, url_foto)
        return EsitoPubblicazione(
            ok=False,
            errore=f"Canale {canale} non gestito dall'adattatore Meta.",
            tipo_errore="definitivo",
        )

    # ------------------------------------------------------------------
    # Facebook
    # ------------------------------------------------------------------

    def _facebook(self, didascalia: str, foto: list[bytes]) -> EsitoPubblicazione:
        if len(foto) > 1:
            return EsitoPubblicazione(
                ok=False,
                errore="Nell'MVP un post ha una sola foto.",
                tipo_errore="definitivo",
            )
        esito = self._post(
            f"{self._pagina_id}/photos",
            data={"message": didascalia, "access_token": self._token},
            files={"source": ("foto.jpg", foto[0], "image/jpeg")},
        )
        if isinstance(esito, EsitoPubblicazione):
            return esito
        id_post = esito.get("post_id") or esito.get("id")
        if not id_post:
            return _risposta_inattesa()
        return EsitoPubblicazione(ok=True, id_esterno=id_post)

    # ------------------------------------------------------------------
    # Instagram
    # ------------------------------------------------------------------

    def _instagram(self, didascalia: str, url_foto: list[str]) -> EsitoPubblicazione:
        if len(url_foto) > 1:
            return EsitoPubblicazione(
                ok=False,
                errore="Nell'MVP un post ha una sola foto.",
                tipo_errore="definitivo",
            )
        if not url_foto or not url_foto[0].startswith("http"):
            return EsitoPubblicazione(
                ok=False,
                errore="Manca l'indirizzo pubblico della foto: "
                "configura FOTO_URL_PUBBLICO in backend/.env.",
                tipo_errore="definitivo",
            )
        esito = self._post(
            f"{self._instagram_id}/media",
            data={
                "image_url": url_foto[0],
                "caption": didascalia,
                "access_token": self._token,
            },
        )
        if isinstance(esito, EsitoPubblicazione):
            return esito
        contenitore = esito.get("id")
        if not contenitore:
            return _risposta_inattesa()
        pronto = self._attendi_contenitore(contenitore)
        if isinstance(pronto, EsitoPubblicazione):
            return pronto
        esito = self._post(
            f"{self._instagram_id}/media_publish",
            data={"creation_id": contenitore, "access_token": self._token},
        )
        if isinstance(esito, EsitoPubblicazione):
            return esito
        id_media = esito.get("id")
        if not id_media:
            return _risposta_inattesa()
        return EsitoPubblicazione(ok=True, id_esterno=id_media)

    def _attendi_contenitore(self, contenitore: str) -> EsitoPubblicazione | None:
        """Controlla ``status_code`` fino a ``FINISHED``; oltre, errore temporaneo."""
        for controllo in range(CONTENITORE_CONTROLLI):
            if controllo:
                time.sleep(self._attesa_contenitore)
            esito = self._get(
                contenitore,
                {"fields": "status_code", "access_token": self._token},
            )
            if isinstance(esito, EsitoPubblicazione):
                return esito
            stato = esito.get("status_code")
            if stato == "FINISHED":
                return None
            if stato == "ERROR":
                return EsitoPubblicazione(
                    ok=False,
                    errore="Il contenitore Instagram è in errore.",
                    tipo_errore="definitivo",
                )
        return EsitoPubblicazione(
            ok=False,
            errore="Il contenitore Instagram non è pronto: riprova al prossimo tick.",
            tipo_errore="temporaneo",
        )

    # ------------------------------------------------------------------
    # Chiamate Graph ed errori
    # ------------------------------------------------------------------

    def _post(self, percorso: str, **kwargs) -> dict | EsitoPubblicazione:
        return self._richiedi(self._client.post, percorso, **kwargs)

    def _get(self, percorso: str, params: dict) -> dict | EsitoPubblicazione:
        return self._richiedi(self._client.get, percorso, params=params)

    def _richiedi(self, metodo, percorso: str, **kwargs) -> dict | EsitoPubblicazione:
        try:
            risposta = metodo(f"{self._base}/{percorso}", **kwargs)
        except httpx.HTTPError as exc:
            return self._errore_rete(exc)
        if risposta.status_code >= 400:
            return self._errore_http(risposta)
        try:
            return risposta.json()
        except ValueError:
            return EsitoPubblicazione(
                ok=False,
                errore="Risposta di Meta non leggibile.",
                tipo_errore="temporaneo",
            )

    def _errore_rete(self, exc: httpx.HTTPError) -> EsitoPubblicazione:
        """Timeout e problemi di connessione sono temporanei (il tick riprova)."""
        return EsitoPubblicazione(
            ok=False,
            errore=f"Meta irraggiungibile: {exc.__class__.__name__}",
            tipo_errore="temporaneo",
        )

    def _errore_http(self, risposta: httpx.Response) -> EsitoPubblicazione:
        if risposta.status_code >= 500:
            return EsitoPubblicazione(
                ok=False,
                errore=f"Errore di Meta ({risposta.status_code}).",
                tipo_errore="temporaneo",
            )
        try:
            errore = risposta.json().get("error", {})
        except ValueError:
            errore = {}
        messaggio = self._senza_token(
            str(errore.get("message") or f"Errore di Meta ({risposta.status_code}).")
        )
        temporaneo = bool(
            errore.get("code") in CODICI_TEMPORANEI or errore.get("is_transient")
        )
        return EsitoPubblicazione(
            ok=False,
            errore=messaggio,
            tipo_errore="temporaneo" if temporaneo else "definitivo",
        )

    def _senza_token(self, testo: str) -> str:
        """Il token della Pagina non finisce mai nei messaggi (constitution §3)."""
        return testo.replace(self._token, "***")


def _risposta_inattesa() -> EsitoPubblicazione:
    """Meta ha risposto 200 ma senza l'id atteso: non si riprova alla cieca."""
    return EsitoPubblicazione(
        ok=False,
        errore="Risposta di Meta senza l'identificativo atteso.",
        tipo_errore="definitivo",
    )


def _didascalia(testo: str, hashtag: list[str]) -> str:
    """Testo, una riga vuota e gli hashtag con ``#`` (brief-meta §3)."""
    if hashtag:
        return testo + "\n\n" + " ".join(f"#{tag.lstrip('#')}" for tag in hashtag)
    return testo
