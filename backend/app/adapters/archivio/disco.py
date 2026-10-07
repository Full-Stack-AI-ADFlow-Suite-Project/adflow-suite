"""Implementazione su disco locale dell'adattatore archivio foto.

Salva, legge ed elimina file all'interno della cartella configurata da ARCHIVIO_FOTO_DIR.
Include controlli rigorosi di sicurezza per prevenire attacchi di Directory Traversal.
"""

from pathlib import Path
from typing import Optional

from app.core.config import leggi_impostazioni
from .base import ArchivioAdapter


class ArchivioDisco(ArchivioAdapter):
    """Gestione dell'archiviazione foto su file system locale."""

    def __init__(self, radice: Optional[Path | str] = None) -> None:
        """Inizializza l'archivio su disco.

        Args:
            radice: percorso base in cui memorizzare le foto. Se non specificato,
                    viene letto da ARCHIVIO_FOTO_DIR nelle impostazioni di configurazione.
        """
        if radice is not None:
            self._radice = Path(radice).resolve()
        else:
            self._radice = Path(leggi_impostazioni().archivio_foto_dir).resolve()

        # Crea la cartella radice se non esiste ancora
        self._radice.mkdir(parents=True, exist_ok=True)

    @property
    def cartella_radice(self) -> Path:
        """Restituisce il percorso assoluto della cartella radice dell'archivio."""
        return self._radice

    def _valida_e_risolvi_percorso(self, nome_file: str) -> Path:
        """Valida il nome del file e ne calcola il percorso assoluto in sicurezza.

        Previene attacchi di tipo Directory Traversal (CWE-22): il nome è
        controllato da `valida_nome_file` (regola comune a tutte le implementazioni)
        e il percorso finale deve risiedere interamente nella cartella radice
        (copre anche i collegamenti simbolici).

        Args:
            nome_file: nome del file richiesto.

        Returns:
            Percorso assoluto del file.

        Raises:
            ValueError: se il nome del file non è valido o tenta un path traversal.
        """
        nome_valido = self.valida_nome_file(nome_file)
        percorso_risolto = (self._radice / nome_valido).resolve()

        # Verifica di sicurezza: il percorso deve rimanere all'interno della radice
        if not percorso_risolto.is_relative_to(self._radice):
            raise ValueError(
                "Accesso negato: il percorso richiesto è esterno alla cartella dell'archivio."
            )

        return percorso_risolto

    def salva(self, contenuto: bytes, estensione: str) -> str:
        """Salva il contenuto su disco con un nome sicuro generato dal server."""
        nome_file = self.genera_nome_file(estensione)
        percorso = self._valida_e_risolvi_percorso(nome_file)
        percorso.write_bytes(contenuto)
        return nome_file

    def leggi(self, nome_file: str) -> bytes:
        """Legge i byte del file specificato da disco."""
        percorso = self._valida_e_risolvi_percorso(nome_file)
        if not percorso.is_file():
            raise FileNotFoundError(f"File non trovato nell'archivio: {nome_file}")
        return percorso.read_bytes()

    def elimina(self, nome_file: str) -> bool:
        """Elimina il file da disco se esistente."""
        percorso = self._valida_e_risolvi_percorso(nome_file)
        if percorso.is_file():
            percorso.unlink()
            return True
        return False

    def esiste(self, nome_file: str) -> bool:
        """Verifica l'esistenza fisica del file su disco."""
        try:
            percorso = self._valida_e_risolvi_percorso(nome_file)
            return percorso.is_file()
        except ValueError:
            return False

    def percorso_file(self, nome_file: str) -> Path:
        """Restituisce il Path sicuro del file, verificando che esista."""
        percorso = self._valida_e_risolvi_percorso(nome_file)
        if not percorso.is_file():
            raise FileNotFoundError(f"File non trovato nell'archivio: {nome_file}")
        return percorso
