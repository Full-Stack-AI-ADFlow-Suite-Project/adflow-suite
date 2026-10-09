"""Interfaccia dell'adattatore AI (plan §5, spec §2.2).

L'adattatore non conosce i moduli: riceve e restituisce dati semplici. Il
piano ha la forma che ``contenuti`` controlla (``piano.contenuto``):

    {"strategia": "...",
     "uscite": [{"numero": 1, "tema": "...", "gruppo_id": 3,
                 "post": [{"canale": "facebook", "formato": "singola",
                           "foto": [12], "riempitivo": null,
                           "data_ora": "2030-01-07T10:00:00+01:00"}]}]}
"""

from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

# R-35: i tipi di errore tecnico dell'AI.
TIPI_ERRORE = ("temporaneo", "risposta", "configurazione", "richiesta", "rifiuto")


class ErroreAI(Exception):
    """Errore tecnico dell'AI, con il tipo di R-35 e un messaggio per l'operatore.

    È l'adattatore a tradurre gli errori del provider: chi chiama legge solo
    ``tipo``, ``messaggio`` e, se l'errore riguarda una sola foto, ``foto_id``.
    """

    def __init__(self, tipo: str, messaggio: str, *, foto_id: int | None = None):
        if tipo not in TIPI_ERRORE:
            raise ValueError(f"Tipo di errore AI non valido: {tipo}")
        super().__init__(messaggio)
        self.tipo = tipo
        self.messaggio = messaggio
        self.foto_id = foto_id


@dataclass
class FotoAI:
    """Una foto caricata. ``analisi`` è vuota finché la foto non è analizzata."""

    id: int
    file: str
    mime: str
    da_usare: bool = False
    analisi: dict[str, Any] | None = None


@dataclass
class GruppoAI:
    """Un gruppo di foto caricate, con la descrizione scritta dall'artigiano."""

    id: int
    descrizione: str | None
    da_usare_il: date | None = None
    foto: list[FotoAI] = field(default_factory=list)


@dataclass
class CampagnaAI:
    """Ciò che l'AI deve sapere della campagna."""

    titolo: str
    inizio: date
    fine: date
    descrizione: str | None = None
    obiettivo: str | None = None


@dataclass
class PostAI:
    """Un post del piano, per chiederne testo e hashtag."""

    canale: str
    tema: str
    formato: str
    data_ora: datetime
    riempitivo: str | None = None
    descrizione_gruppo: str | None = None
    foto: list[FotoAI] = field(default_factory=list)


@dataclass
class PianoAI:
    """Il piano scritto dall'AI, con chi lo ha scritto."""

    contenuto: dict[str, Any]
    provider: str
    modello: str
    versione_prompt: str


@dataclass
class PostScritto:
    """Testo e hashtag (senza ``#``) di un post, con chi li ha scritti."""

    testo: str
    hashtag: list[str]
    provider: str
    modello: str
    versione_prompt: str


class AIAdapter(ABC):
    """Interfaccia verso il provider AI.

    In sviluppo e nei test si usa ``AIFinto``, che risponde senza rete. Ogni
    metodo solleva ``ErroreAI`` per gli errori tecnici di R-35.
    """

    @abstractmethod
    def analizza_gruppo(self, gruppo: GruppoAI) -> dict[int, dict[str, Any]]:
        """Analizza le foto di un gruppo, con la sua descrizione.

        Returns:
            Per ogni id di foto il JSON di ``foto.analisi_ai``: ``idonea``,
            ``simile_a``, ``tipo``, ``punteggio``, ``motivo``, ``soggetto``.

        Raises:
            ErroreAI: con ``foto_id`` se l'errore riguarda una sola foto.
        """
        raise NotImplementedError

    @abstractmethod
    def pianifica_campagna(
        self,
        snapshot: Mapping[str, Any],
        campagna: CampagnaAI,
        gruppi: Sequence[GruppoAI],
        limiti: Mapping[str, Mapping[str, Any]],
        schede: Mapping[str, Mapping[str, Any]],
        *,
        non_prima_di: datetime,
        piano_precedente: Mapping[str, Any] | None = None,
        violazioni: Sequence[Mapping[str, Any]] | None = None,
    ) -> PianoAI:
        """Scrive il piano: strategia, uscite e post per canale.

        Args:
            snapshot: la fotografia del profilo salvata all'invio (R-11).
            campagna: titolo, periodo, descrizione e obiettivo.
            gruppi: i gruppi di foto caricate, già analizzati.
            limiti: per canale ``post_chiesti``, ``foto_disponibili`` e
                ``riempitivi``: il numero dei post non lo decide l'AI (R-05).
            schede: la scheda di ogni canale (R-21).
            non_prima_di: nessun post può uscire prima di questo momento (R-08).
            piano_precedente, violazioni: nelle riscritture, il piano che non
                ha passato il controllo e le regole che non rispettava (R-09).
        """
        raise NotImplementedError

    @abstractmethod
    def genera_post(
        self,
        snapshot: Mapping[str, Any],
        campagna: CampagnaAI,
        post: PostAI,
        scheda: Mapping[str, Any],
        *,
        testo_precedente: str | None = None,
        violazioni: Sequence[Mapping[str, Any]] | None = None,
    ) -> PostScritto:
        """Scrive testo e hashtag di un post per il suo canale.

        Args:
            scheda: la scheda del canale del post (R-21).
            testo_precedente, violazioni: nelle riscritture, il testo che non
                ha passato il validatore e ciò che il validatore ha trovato.
        """
        raise NotImplementedError
