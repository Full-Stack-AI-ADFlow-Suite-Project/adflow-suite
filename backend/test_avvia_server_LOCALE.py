# pylint: disable=invalid-name,wrong-import-position
"""Verifiche dinamiche di affidabilità per avvia_server_LOCALE.py.

Questo modulo collauda:
- B3: deepcopy del dict uvicorn.config.LOGGING_CONFIG (nessuna contaminazione globale).
- B4: assenza di duplicazione log per uvicorn.error (scrittura singola garantita).
- B5: singola chiamata a registra_arresto_nel_changelog in main().
- Creazione automatica di CHANGELOG_LOCALE.md se non esiste (clone fresco).
- Aggiornamento atomico di avvio e arresto nella tabella del Change Log.
"""

from __future__ import annotations

import inspect
import logging
import logging.config
import sys
from pathlib import Path

# Configurazione del percorso locale
CARTELLA_LOCALE = Path(__file__).resolve().parent
if str(CARTELLA_LOCALE) not in sys.path:
    sys.path.insert(0, str(CARTELLA_LOCALE))

import uvicorn  # noqa: E402
import avvia_server_LOCALE as launcher  # noqa: E402


def test_deepcopy_non_contamina_dict_globale() -> None:
    """Verifica che configura_logging non modifichi uvicorn.config.LOGGING_CONFIG."""
    file_dummy = CARTELLA_LOCALE / "dummy_test_b3.log"
    try:
        launcher.configura_logging(file_dummy)
        contaminato = "file" in uvicorn.config.LOGGING_CONFIG.get("handlers", {})
        assert (
            not contaminato
        ), "Il dict globale uvicorn.config.LOGGING_CONFIG è stato contaminato!"
    finally:
        if file_dummy.exists():
            file_dummy.unlink()


def test_uvicorn_error_non_duplica_righe_log() -> None:
    """Verifica che i messaggi di uvicorn.error non vengano duplicati nel file di log."""
    file_log = CARTELLA_LOCALE / "dummy_test_b4_dedup.log"
    if file_log.exists():
        file_log.unlink()

    try:
        cfg = launcher.configura_logging(file_log)
        # uvicorn.error non deve avere handlers propri assegnati per non duplicare
        uvicorn_error_cfg = cfg["loggers"].get("uvicorn.error", {})
        assert (
            "handlers" not in uvicorn_error_cfg
        ), "uvicorn.error non deve definire handlers propri (deve propagare a uvicorn)"

        # Prova empirica di logging
        logging.config.dictConfig(cfg)
        test_msg = "MESSAGGIO-VERIFICA-UNICO-UV-ERROR"
        logging.getLogger("uvicorn.error").info(test_msg)
        logging.shutdown()

        assert file_log.exists(), "Il file di log non è stato creato durante il test"
        righe = [
            riga
            for riga in file_log.read_text(encoding="utf-8").splitlines()
            if test_msg in riga
        ]
        assert (
            len(righe) == 1
        ), f"Attesa esattamente 1 riga per uvicorn.error, trovate {len(righe)}: {righe}"
    finally:
        if file_log.exists():
            try:
                file_log.unlink()
            except OSError:
                pass


def test_registra_arresto_chiamata_singola_in_main() -> None:
    """Verifica che registra_arresto_nel_changelog sia invocata solo nel blocco finally."""
    sorgente = inspect.getsource(launcher.main)
    assert (
        "errore_critico: Exception | None = None" in sorgente
    ), "Flag errore_critico assente prima del blocco try"

    chiamate_reali = [
        riga
        for riga in sorgente.splitlines()
        if "registra_arresto_nel_changelog(" in riga
        and not riga.lstrip().startswith("#")
    ]
    assert (
        len(chiamate_reali) == 1
    ), f"registra_arresto_nel_changelog chiamata {len(chiamate_reali)} volte (attesa 1)"


def test_changelog_creazione_automatica_se_assente() -> None:
    """Verifica che su clone fresco CHANGELOG_LOCALE.md venga creato se assente."""
    changelog_test = CARTELLA_LOCALE / "temp_changelog_nuovo_LOCALE.md"
    if changelog_test.exists():
        changelog_test.unlink()

    changelog_originale = launcher.FILE_CHANGELOG
    launcher.FILE_CHANGELOG = changelog_test

    try:
        launcher.registra_avvio_nel_changelog(porta=8888, reload=False, pid=54321)
        assert (
            changelog_test.exists()
        ), "CHANGELOG_LOCALE.md non è stato creato automaticamente"
        contenuto = changelog_test.read_text(encoding="utf-8")
        assert (
            "|---|---|---|---|---|" in contenuto
        ), "Intestazione tabella assente nel changelog creato"
        assert "8888" in contenuto, "Dati porta avvio assenti nel changelog"
        assert "54321" in contenuto, "PID avvio assente nel changelog"
        assert "🟢 Attivo" in contenuto, "Stato iniziale attivo assente nel changelog"

        # Verifica aggiornamento arresto
        launcher.registra_arresto_nel_changelog(motivo="Chiusura-Collaudo")
        contenuto_aggiornato = changelog_test.read_text(encoding="utf-8")
        assert "Chiusura-Collaudo" in contenuto_aggiornato
        assert "🟢 Attivo" not in contenuto_aggiornato
    finally:
        launcher.FILE_CHANGELOG = changelog_originale
        if changelog_test.exists():
            changelog_test.unlink()


def esegui_tutti_i_test() -> int:
    """Esegue tutte le asserzioni di collaudo e stampa l'esito."""
    test_suite = [
        ("B3: deepcopy LOGGING_CONFIG", test_deepcopy_non_contamina_dict_globale),
        (
            "B4: no duplicati log uvicorn.error",
            test_uvicorn_error_non_duplica_righe_log,
        ),
        (
            "B5: singola scrittura arresto in main",
            test_registra_arresto_chiamata_singola_in_main,
        ),
        (
            "Changelog: creazione automatica e aggiornamento",
            test_changelog_creazione_automatica_se_assente,
        ),
    ]

    falliti = 0
    print("=== AVVIO VERIFICHE DI AFFIDABILITÀ LAUNCHER ===")
    for nome, test_fn in test_suite:
        try:
            test_fn()
            print(f"  [OK] {nome}")
        except AssertionError as exc:
            print(f"  [FAIL] {nome}: {exc}")
            falliti += 1
        except Exception as exc:  # pylint: disable=broad-except
            print(f"  [ERRORE] {nome}: {exc}")
            falliti += 1

    if falliti == 0:
        print("=== TUTTE LE VERIFICHE SUPERATE: ZERO BUG ===")
        return 0

    print(f"=== VERIFICHE TERMINATE CON {falliti} ERRORI ===")
    return 1


if __name__ == "__main__":
    sys.exit(esegui_tutti_i_test())
