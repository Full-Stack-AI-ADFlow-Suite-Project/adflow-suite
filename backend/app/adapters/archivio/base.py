"""Interfaccia astratta per l'adattatore dell'archivio foto.

Definisce le operazioni di salvataggio, lettura ed eliminazione delle immagini,
garantendo che il nome del file sia sempre generato dal server (Costituzione §3).
"""

from abc import ABC, abstractmethod
from pathlib import Path
import re
import uuid

LUNGHEZZA_MAX_ESTENSIONE = 10
CARATTERI_VIETATI_NEL_NOME = (
    "/",
    "\\",
    "..",
    ":",
    "*",
    "?",
    '"',
    "<",
    ">",
    "|",
    "\x00",
)


class ArchivioAdapter(ABC):
    """Contratto base per l'archiviazione dei file delle foto."""

    @staticmethod
    def genera_nome_file(estensione: str) -> str:
        """Genera un nome file univoco e sicuro generato dal server.

        Args:
            estensione: estensione del file, con o senza punto iniziale (es. 'jpg', '.png').

        Returns:
            Nome file univoco nel formato '<uuid>.<estensione_sanitizzata>'.
            Se l'estensione è vuota, non valida o più lunga di
            LUNGHEZZA_MAX_ESTENSIONE caratteri, si usa '.bin'.
        """
        ext_pulita = ".bin"
        if estensione and isinstance(estensione, str):
            ext = estensione.strip().lower().lstrip(".")
            # Sanitizza: mantiene solo caratteri alfanumerici
            ext = re.sub(r"[^a-z0-9]", "", ext)
            if 0 < len(ext) <= LUNGHEZZA_MAX_ESTENSIONE:
                ext_pulita = f".{ext}"

        identificativo = uuid.uuid4().hex
        return f"{identificativo}{ext_pulita}"

    @staticmethod
    def valida_nome_file(nome_file: str) -> str:
        """Verifica che un nome file sia un semplice nome, senza percorsi.

        La regola è unica per tutte le implementazioni, così l'archivio finto
        dei test si comporta come quello reale.

        Args:
            nome_file: nome del file da controllare.

        Returns:
            Lo stesso nome, se valido.

        Raises:
            ValueError: se il nome è vuoto, non è una stringa, contiene separatori
                di percorso, risalite ('..') o caratteri riservati (es. ':' che su
                Windows apre gli Alternate Data Streams).
        """
        if not nome_file or not isinstance(nome_file, str):
            raise ValueError("Il nome del file non può essere vuoto.")

        if any(c in nome_file for c in CARATTERI_VIETATI_NEL_NOME):
            raise ValueError(
                "Nome file non valido: sono vietati separatori di percorso, "
                "caratteri riservati o risalite di directory."
            )

        if Path(nome_file).name != nome_file:
            raise ValueError("Nome file non valido.")

        return nome_file

    @abstractmethod
    def salva(self, contenuto: bytes, estensione: str) -> str:
        """Salva il contenuto di un file e restituisce il nome generato dal server.

        Args:
            contenuto: byte del file da salvare.
            estensione: estensione del file (es. '.jpg', '.png', '.webp').

        Returns:
            Nome univoco del file generato dal server.

        Raises:
            TypeError: se il contenuto non è di tipo bytes.
        """
        raise NotImplementedError

    @abstractmethod
    def leggi(self, nome_file: str) -> bytes:
        """Legge e restituisce i byte del file specificato.

        Args:
            nome_file: nome del file salvato nell'archivio.

        Returns:
            Byte del file.

        Raises:
            ValueError: se il nome del file non è valido.
            FileNotFoundError: se il file non esiste nell'archivio.
        """
        raise NotImplementedError

    @abstractmethod
    def elimina(self, nome_file: str) -> bool:
        """Elimina il file specificato dall'archivio.

        Args:
            nome_file: nome del file da eliminare.

        Returns:
            True se il file è stato eliminato, False se non esisteva.

        Raises:
            ValueError: se il nome del file non è valido.
        """
        raise NotImplementedError

    @abstractmethod
    def esiste(self, nome_file: str) -> bool:
        """Verifica se il file specificato esiste nell'archivio.

        Args:
            nome_file: nome del file da verificare.

        Returns:
            True se il file esiste, False altrimenti (anche per nomi non validi).
        """
        raise NotImplementedError
