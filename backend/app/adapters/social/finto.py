"""Implementazione finta dell'adattatore social per sviluppo e test."""

from .base import EsitoPubblicazione, SocialAdapter

MARCA_ERRORE_TEMPORANEO = "FAIL_TEMP"
MARCA_ERRORE_DEFINITIVO = "FAIL_DEF"


class SocialFinto(SocialAdapter):
    """Adattatore social simulato che restituisce risultati prevedibili.

    Di default ogni pubblicazione riesce con un id progressivo. Per comandare
    un esito si mette una marca nel testo del post:

    - ``FAIL_TEMP``: errore temporaneo;
    - ``FAIL_DEF``: errore definitivo.

    Ogni chiamata si registra in ``pubblicazioni``, per i test che controllano
    che cosa è stato pubblicato. Nessuna chiamata di rete.
    """

    def __init__(self) -> None:
        self._conta = 0
        self.pubblicazioni: list[dict] = []

    def pubblica(
        self,
        testo: str,
        hashtag: list[str],
        foto: list[bytes],
    ) -> EsitoPubblicazione:
        if not foto:
            raise ValueError("La pubblicazione richiede almeno una foto.")
        self.pubblicazioni.append(
            {"testo": testo, "hashtag": list(hashtag), "n_foto": len(foto)}
        )
        testo_min = testo.lower()
        if MARCA_ERRORE_TEMPORANEO.lower() in testo_min:
            return EsitoPubblicazione(
                ok=False,
                errore="Errore temporaneo simulato",
                tipo_errore="temporaneo",
            )
        if MARCA_ERRORE_DEFINITIVO.lower() in testo_min:
            return EsitoPubblicazione(
                ok=False,
                errore="Errore definitivo simulato",
                tipo_errore="definitivo",
            )
        self._conta += 1
        return EsitoPubblicazione(ok=True, id_esterno=f"finto-{self._conta}")
