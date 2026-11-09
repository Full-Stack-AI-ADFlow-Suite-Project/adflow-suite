"""Implementazione finta (in memoria) dell'adattatore archivio per test e sviluppo."""

import time

from .base import ArchivioAdapter, Derivato


class ArchivioFinto(ArchivioAdapter):
    """Archivio simulato in memoria che non tocca il file system.

    Si comporta come ArchivioDisco: stessa validazione dei nomi e stessi errori.
    """

    def __init__(self) -> None:
        self._archivio: dict[str, bytes] = {}
        self._derivati: dict[tuple[int, str], tuple[bytes, float]] = {}

    def salva(self, contenuto: bytes, estensione: str) -> str:
        """Salva il contenuto in memoria generando un nome univoco."""
        ext_normalizzata = self.valida_payload(contenuto, estensione)
        nome_file = self.genera_nome_file(ext_normalizzata)
        self._archivio[nome_file] = bytes(contenuto)
        return nome_file

    def leggi(self, nome_file: str) -> bytes:
        """Restituisce i byte del file in memoria."""
        self.valida_nome_file(nome_file)
        if nome_file not in self._archivio:
            raise FileNotFoundError(f"File non trovato nell'archivio: {nome_file}")
        return self._archivio[nome_file]

    def elimina(self, nome_file: str) -> bool:
        """Elimina il file dalla memoria se presente."""
        self.valida_nome_file(nome_file)
        if nome_file in self._archivio:
            del self._archivio[nome_file]
            return True
        return False

    def esiste(self, nome_file: str) -> bool:
        """Controlla se il file è presente in memoria."""
        try:
            self.valida_nome_file(nome_file)
        except ValueError:
            return False
        return nome_file in self._archivio

    def svuota(self) -> None:
        """Azzera tutti i file salvati in memoria (utile per reset nei test)."""
        self._archivio.clear()
        self._derivati.clear()

    @property
    def file_salvati(self) -> list[str]:
        """Restituisce l'elenco dei nomi file memorizzati."""
        return list(self._archivio.keys())

    # --- File derivati (RT-06) ---------------------------------------------------

    def salva_derivato(self, foto_id: int, chiave: str, contenuto: bytes) -> None:
        self.valida_payload_derivato(contenuto)
        self.valida_derivato(foto_id, chiave)
        self._derivati[(foto_id, chiave)] = (bytes(contenuto), time.time())

    def leggi_derivato(self, foto_id: int, chiave: str) -> bytes:
        self.valida_derivato(foto_id, chiave)
        try:
            return self._derivati[(foto_id, chiave)][0]
        except KeyError:
            raise FileNotFoundError(f"Derivato non trovato: foto {foto_id}") from None

    def esiste_derivato(self, foto_id: int, chiave: str) -> bool:
        try:
            self.valida_derivato(foto_id, chiave)
        except ValueError:
            return False
        return (foto_id, chiave) in self._derivati

    def elimina_derivato(self, foto_id: int, chiave: str) -> bool:
        self.valida_derivato(foto_id, chiave)
        return self._derivati.pop((foto_id, chiave), None) is not None

    def elenca_derivati(self) -> list[Derivato]:
        return [Derivato(f, c, t) for (f, c), (_, t) in self._derivati.items()]

    def invecchia_derivato(self, foto_id: int, chiave: str, scritto_il: float) -> None:
        """Per i test: sposta l'istante di scrittura di un derivato."""
        contenuto, _ = self._derivati[(foto_id, chiave)]
        self._derivati[(foto_id, chiave)] = (contenuto, scritto_il)
