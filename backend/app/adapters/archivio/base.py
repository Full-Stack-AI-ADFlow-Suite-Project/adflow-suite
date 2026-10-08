"""Interfaccia astratta per l'adattatore dell'archivio foto.

Definisce le operazioni di salvataggio, lettura ed eliminazione delle immagini,
garantendo:
- Nome del file generato esclusivamente dal server (Costituzione §3);
- Validazione della dimensione massima del payload (10 MB come da Spec R-13, anti-DoS);
- Whitelist rigorosa delle estensioni ammesse (JPG, PNG, WEBP) e verifica magic bytes (anti-spoofing);
- Validazione unificata dei percorsi per prevenire Directory Traversal (CWE-22).
"""

from abc import ABC, abstractmethod
from pathlib import Path
import re
import uuid

# Limite di specifica R-13: immagini <= 10 MB
DIMENSIONE_MAX_BYTE: int = 10 * 1024 * 1024

# Estensioni supportate dal dominio (Spec R-13)
ESTENSIONI_AMMESSE: frozenset[str] = frozenset({".jpg", ".jpeg", ".png", ".webp"})

CARATTERI_VIETATI_NEL_NOME: tuple[str, ...] = (
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

    @classmethod
    def normalizza_e_valida_estensione(cls, estensione: str) -> str:
        """Sanitizza e valida l'estensione contro la whitelist ammessa.

        Args:
            estensione: estensione con o senza punto iniziale (es. 'jpg', '.png').

        Returns:
            Estensione normalizzata (es. '.jpg', '.png', '.webp').

        Raises:
            ValueError: se l'estensione non è supportata o non valida.
        """
        if not estensione or not isinstance(estensione, str):
            raise ValueError("L'estensione del file non può essere vuota.")

        ext = estensione.strip().lower()
        if not ext.startswith("."):
            ext = f".{ext}"

        # Sanitizza rimuovendo caratteri non alfanumerici dopo il punto
        ext_pulita = "." + re.sub(r"[^a-z0-9]", "", ext[1:])

        if ext_pulita not in ESTENSIONI_AMMESSE:
            ammessi = ", ".join(sorted(ESTENSIONI_AMMESSE))
            raise ValueError(
                f"Estensione '{estensione}' non supportata. Formati consentiti: {ammessi}"
            )

        return ext_pulita

    @classmethod
    def valida_dimensione_payload(cls, contenuto: bytes) -> None:
        """Verifica che la dimensione del payload rispetti il limite massimo.

        Args:
            contenuto: byte del file da verificare.

        Raises:
            TypeError: se il contenuto non è un tipo binario.
            ValueError: se il contenuto è vuoto o supera DIMENSIONE_MAX_BYTE.
        """
        if not isinstance(contenuto, (bytes, bytearray, memoryview)):
            raise TypeError("Il contenuto da salvare deve essere di tipo bytes.")

        lunghezza = len(contenuto)
        if lunghezza == 0:
            raise ValueError("Il payload del file non può essere vuoto.")

        if lunghezza > DIMENSIONE_MAX_BYTE:
            limite_mb = DIMENSIONE_MAX_BYTE // (1024 * 1024)
            raise ValueError(
                f"La dimensione del file ({lunghezza} byte) supera il limite massimo di {limite_mb} MB."
            )

    @classmethod
    def valida_magic_bytes(cls, contenuto: bytes, estensione_normalizzata: str) -> None:
        """Verifica la coerenza tra estensione dichiarata e magic bytes reali del file.

        Args:
            contenuto: byte del file.
            estensione_normalizzata: estensione validata (es. '.jpg', '.png', '.webp').

        Raises:
            ValueError: se l'intestazione binaria non corrisponde all'estensione.
        """
        dati = bytes(contenuto)

        if estensione_normalizzata in (".jpg", ".jpeg"):
            if not dati.startswith(b"\xff\xd8\xff"):
                raise ValueError(
                    "Il contenuto non corrisponde a un'immagine JPEG valida."
                )
        elif estensione_normalizzata == ".png":
            if not dati.startswith(b"\x89PNG\r\n\x1a\n"):
                raise ValueError(
                    "Il contenuto non corrisponde a un'immagine PNG valida."
                )
        elif estensione_normalizzata == ".webp":
            if not (len(dati) >= 12 and dati[:4] == b"RIFF" and dati[8:12] == b"WEBP"):
                raise ValueError(
                    "Il contenuto non corrisponde a un'immagine WEBP valida."
                )

    @classmethod
    def valida_payload(cls, contenuto: bytes, estensione: str) -> str:
        """Valida integralmente dimensione, estensione e magic bytes del file.

        Args:
            contenuto: byte del file da salvare.
            estensione: estensione del file dichiarata.

        Returns:
            Estensione normalizzata e validata.
        """
        cls.valida_dimensione_payload(contenuto)
        ext_normalizzata = cls.normalizza_e_valida_estensione(estensione)
        cls.valida_magic_bytes(contenuto, ext_normalizzata)
        return ext_normalizzata

    @classmethod
    def genera_nome_file(cls, estensione: str) -> str:
        """Genera un nome file univoco e sicuro generato dal server.

        Args:
            estensione: estensione del file (es. 'jpg', '.png', '.webp').

        Returns:
            Nome file univoco nel formato '<uuid>.<estensione_sanitizzata>'.
        """
        ext_pulita = cls.normalizza_e_valida_estensione(estensione)
        identificativo = uuid.uuid4().hex
        return f"{identificativo}{ext_pulita}"

    @staticmethod
    def valida_nome_file(nome_file: str) -> str:
        """Verifica che un nome file sia un semplice nome, senza percorsi.

        Args:
            nome_file: nome del file da controllare.

        Returns:
            Lo stesso nome, se valido.

        Raises:
            ValueError: se il nome è vuoto, non è una stringa, contiene separatori
                di percorso, risalite ('..') o caratteri riservati.
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
        """Salva il contenuto di un file e restituisce il nome generato dal server."""
        raise NotImplementedError

    @abstractmethod
    def leggi(self, nome_file: str) -> bytes:
        """Legge e restituisce i byte del file specificato."""
        raise NotImplementedError

    @abstractmethod
    def elimina(self, nome_file: str) -> bool:
        """Elimina il file specificato dall'archivio."""
        raise NotImplementedError

    @abstractmethod
    def esiste(self, nome_file: str) -> bool:
        """Verifica se il file specificato esiste nell'archivio."""
        raise NotImplementedError
