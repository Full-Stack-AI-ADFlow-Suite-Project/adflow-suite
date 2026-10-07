"""Implementazione finta (in memoria) dell'adattatore archivio per test e sviluppo."""

from .base import ArchivioAdapter


class ArchivioFinto(ArchivioAdapter):
    """Archivio simulato in memoria che non tocca il file system.

    Si comporta come ArchivioDisco: stessa validazione dei nomi e stessi errori.
    """

    def __init__(self) -> None:
        self._archivio: dict[str, bytes] = {}

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

    @property
    def file_salvati(self) -> list[str]:
        """Restituisce l'elenco dei nomi file memorizzati."""
        return list(self._archivio.keys())
