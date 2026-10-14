"""Interfaccia dell'adattatore social (plan §5)."""

from abc import ABC, abstractmethod
from dataclasses import dataclass

TIPI_ERRORE = ("temporaneo", "definitivo")


@dataclass
class EsitoPubblicazione:
    """Risultato di un tentativo di pubblicazione su un social network.

    Attributes:
        ok: ``True`` se la pubblicazione è andata a buon fine.
        id_esterno: id del post sulla piattaforma (solo se ``ok``).
        errore: messaggio dell'errore (solo se non ``ok``).
        tipo_errore: ``"temporaneo"`` per errori riprovabili,
            ``"definitivo"`` per errori irreversibili (solo se non ``ok``).
    """

    ok: bool
    id_esterno: str | None = None
    errore: str | None = None
    tipo_errore: str | None = None


class SocialAdapter(ABC):
    """Interfaccia per la pubblicazione sui social network.

    Ogni piattaforma ha la sua implementazione; in sviluppo e nei test si usa
    ``SocialFinto``, che restituisce risultati prevedibili senza rete.
    """

    @abstractmethod
    def pubblica(
        self,
        canale: str,
        testo: str,
        hashtag: list[str],
        foto: list[bytes],
        url_foto: list[str],
    ) -> EsitoPubblicazione:
        """Pubblica un post su un canale con testo, hashtag e una o più foto.

        Args:
            canale: ``"facebook"`` o ``"instagram"``.
            testo: testo del post.
            hashtag: hashtag del post, senza il simbolo ``#``.
            foto: contenuto dei file delle foto (già sistemate per il canale,
                spec R-42), almeno una, nell'ordine in cui devono uscire.
                Servono alle piattaforme che accettano l'upload, come Facebook.
            url_foto: indirizzi pubblici delle stesse foto, nello stesso
                ordine. Servono alle piattaforme che scaricano la foto da
                un URL, come Instagram (T3-23).

        Returns:
            ``EsitoPubblicazione`` con il risultato del tentativo.
        """
        raise NotImplementedError
