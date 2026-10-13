"""Implementazione finta dell'adattatore social per sviluppo e test."""

from datetime import timedelta

from app.core.orologio import adesso

from .base import EsitoCollegamento, EsitoPubblicazione, SocialAdapter

MARCA_ERRORE_TEMPORANEO = "FAIL_TEMP"
MARCA_ERRORE_DEFINITIVO = "FAIL_DEF"
MARCA_ERRORE_COLLEGAMENTO = "FAIL_COLLEGAMENTO"
DURATA_PERMESSO_GIORNI = 60


class SocialFinto(SocialAdapter):
    """Adattatore social simulato che restituisce risultati prevedibili.

    Di default ogni pubblicazione riesce con un id progressivo. Per comandare
    un esito si mette una marca nel testo del post:

    - ``FAIL_TEMP``: errore temporaneo;
    - ``FAIL_DEF``: errore definitivo.

    Il collegamento di un account riesce con un permesso finto che scade dopo
    ``DURATA_PERMESSO_GIORNI`` giorni; la marca ``FAIL_COLLEGAMENTO`` nel nome
    della piattaforma comanda l'errore.

    Ogni chiamata si registra in ``pubblicazioni`` e ``collegamenti``, per i
    test che controllano che cosa è stato fatto; i permessi non si registrano.
    Nessuna chiamata di rete.
    """

    def __init__(self) -> None:
        self._conta = 0
        self._conta_collegamenti = 0
        self.pubblicazioni: list[dict] = []
        self.collegamenti: list[dict] = []

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

    def collega_account(self, piattaforma: str) -> EsitoCollegamento:
        # Solo la piattaforma si registra: il permesso non va mai nei log.
        self.collegamenti.append({"piattaforma": piattaforma})
        if MARCA_ERRORE_COLLEGAMENTO.lower() in piattaforma.lower():
            return EsitoCollegamento(ok=False, errore="Collegamento simulato fallito.")
        self._conta_collegamenti += 1
        return EsitoCollegamento(
            ok=True,
            id_pagina=f"pagina-finto-{piattaforma}-{self._conta_collegamenti}",
            permesso=f"permesso-finto-{self._conta_collegamenti}",
            scadenza=adesso() + timedelta(days=DURATA_PERMESSO_GIORNI),
        )
