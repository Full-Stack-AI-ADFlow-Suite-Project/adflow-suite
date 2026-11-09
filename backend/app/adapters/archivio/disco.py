"""Implementazione su disco locale dell'adattatore archivio foto.

Salva, legge ed elimina file all'interno della cartella configurata da ARCHIVIO_FOTO_DIR.
Include controlli rigorosi di sicurezza per prevenire attacchi di Directory Traversal.
"""

import os
from pathlib import Path
from typing import Optional

from app.core.config import leggi_impostazioni
from .base import CARTELLA_DERIVATE, ArchivioAdapter, Derivato


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
        ext_normalizzata = self.valida_payload(contenuto, estensione)
        nome_file = self.genera_nome_file(ext_normalizzata)
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
        """Elimina il file da disco in modo atomico, prevenendo race condition TOCTOU.

        Se il file non esiste, restituisce False. Eventuali PermissionError vengono
        lasciati propagare affinché il sistema di monitoraggio possa rilevarli.
        """
        percorso = self._valida_e_risolvi_percorso(nome_file)
        try:
            percorso.unlink(missing_ok=False)
            return True
        except FileNotFoundError:
            return False
        except IsADirectoryError:
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

    # --- File derivati (RT-06) ---------------------------------------------------

    def _percorso_derivato(self, foto_id: int, chiave: str) -> Path:
        """``<radice>/derivate/<foto_id>/<chiave>.jpg``, dentro ``derivate/`` (come ``_valida_e_risolvi_percorso``)."""
        foto_id, chiave = self.valida_derivato(foto_id, chiave)
        base = (self._radice / CARTELLA_DERIVATE).resolve()
        percorso = (base / str(foto_id) / f"{chiave}.jpg").resolve()
        if not percorso.is_relative_to(base):
            raise ValueError(
                "Accesso negato: il percorso richiesto è esterno alla cartella dei derivati."
            )
        return percorso

    def salva_derivato(self, foto_id: int, chiave: str, contenuto: bytes) -> None:
        """Scrive il derivato in modo atomico (file temporaneo, poi rinomina)."""
        self.valida_payload_derivato(contenuto)
        percorso = self._percorso_derivato(foto_id, chiave)
        percorso.parent.mkdir(parents=True, exist_ok=True)
        temporaneo = percorso.with_name(f"{percorso.name}.{os.getpid()}.tmp")
        try:
            temporaneo.write_bytes(contenuto)
            temporaneo.replace(percorso)
        finally:
            temporaneo.unlink(missing_ok=True)

    def leggi_derivato(self, foto_id: int, chiave: str) -> bytes:
        percorso = self._percorso_derivato(foto_id, chiave)
        if not percorso.is_file():
            raise FileNotFoundError(f"Derivato non trovato: foto {foto_id}")
        return percorso.read_bytes()

    def esiste_derivato(self, foto_id: int, chiave: str) -> bool:
        try:
            return self._percorso_derivato(foto_id, chiave).is_file()
        except ValueError:
            return False

    def elimina_derivato(self, foto_id: int, chiave: str) -> bool:
        percorso = self._percorso_derivato(foto_id, chiave)
        try:
            percorso.unlink(missing_ok=False)
        except (FileNotFoundError, IsADirectoryError):
            return False
        return True

    def elenca_derivati(self) -> list[Derivato]:
        base = self._radice / CARTELLA_DERIVATE
        if not base.is_dir():
            return []
        trovati: list[Derivato] = []
        for percorso in base.glob("*/*.jpg"):
            cartella = percorso.parent.name
            if not (percorso.is_file() and cartella.isdecimal() and int(cartella) > 0):
                continue
            try:
                self.valida_derivato(int(cartella), percorso.stem)
            except ValueError:
                continue
            trovati.append(
                Derivato(int(cartella), percorso.stem, percorso.stat().st_mtime)
            )
        return trovati
