"""Test dinamico dei bug B3, B4, B5 corretti in avvia_server_LOCALE.py.

Nota: i moduli uvicorn e avvia_server_LOCALE vengono importati dopo
sys.path.insert() perché il file si trova nella stessa cartella del launcher
e non nella struttura di package standard. Questo pattern e' intenzionale
per un file di test locale non inserito in pytest.
"""

# pylint: disable=C0103,C0413,C0411,wrong-import-position

from __future__ import annotations

import inspect
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import uvicorn  # noqa: E402
import avvia_server_LOCALE as launcher  # noqa: E402

FILE_TEST = Path("test_runtime_LOCALE.log")
errori: list[str] = []

# ---------------------------------------------------------------------------
# TEST B3: deepcopy non contamina il dict globale di uvicorn
# ---------------------------------------------------------------------------
cfg = launcher.configura_logging(FILE_TEST)
contaminato = "file" in uvicorn.config.LOGGING_CONFIG.get("handlers", {})
if contaminato:
    errori.append(
        "B3 FAIL: il dict globale uvicorn.config.LOGGING_CONFIG e' stato "
        "contaminato (shallow copy ancora presente)"
    )
else:
    print("B3 [deepcopy OK]: il dict globale uvicorn NON e' contaminato")

# ---------------------------------------------------------------------------
# TEST B4: uvicorn.error ottiene 'handlers' senza KeyError
# ---------------------------------------------------------------------------
uvicorn_error_cfg = cfg["loggers"].get("uvicorn.error", {})
ha_handlers = "handlers" in uvicorn_error_cfg
ha_file = "file" in uvicorn_error_cfg.get("handlers", [])
if not ha_handlers or not ha_file:
    errori.append(
        f"B4 FAIL: uvicorn.error handlers={uvicorn_error_cfg.get('handlers', 'MANCANTE')}"
    )
else:
    print(f"B4 [uvicorn.error handlers OK]: {uvicorn_error_cfg['handlers']}")

# ---------------------------------------------------------------------------
# TEST B5: registra_arresto_nel_changelog e' chiamata una sola volta in main()
# ---------------------------------------------------------------------------
sorgente_main = inspect.getsource(launcher.main)
ha_flag = "errore_critico: Exception | None = None" in sorgente_main
# Conta solo le chiamate effettive escludendo le righe di commento
chiamate_reali = [
    riga
    for riga in sorgente_main.splitlines()
    if "registra_arresto_nel_changelog(" in riga and not riga.lstrip().startswith("#")
]
ha_finally_unico = len(chiamate_reali) == 1

if not ha_flag:
    errori.append("B5 FAIL: variabile errore_critico non inizializzata prima del try")
elif not ha_finally_unico:
    errori.append(
        f"B5 FAIL: registra_arresto_nel_changelog ha {len(chiamate_reali)} chiamate "
        f"reali (attesa 1): {chiamate_reali}"
    )
else:
    print("B5 [single-write OK]: registra_arresto_nel_changelog chiamata 1 sola volta")

# ---------------------------------------------------------------------------
# TEST CHANGELOG: verifica inserimento riga di avvio e stato di arresto
# ---------------------------------------------------------------------------
changelog_test = Path("test_changelog_LOCALE.md")
contenuto_iniziale = (
    "# Test\n\n"
    "| Data e Ora | Componente | Comando | Esito | Note |\n"
    "|---|---|---|---|---|\n"
    "| voce esistente |\n"
)
changelog_test.write_text(contenuto_iniziale, encoding="utf-8")

# Monkey-patch: usa il file di test invece del CHANGELOG reale
changelog_originale = launcher.FILE_CHANGELOG
launcher.FILE_CHANGELOG = changelog_test

try:
    launcher.registra_avvio_nel_changelog(porta=9999, reload=True, pid=12345)
    risultato = changelog_test.read_text(encoding="utf-8")
    if "9999" in risultato and "12345" in risultato:
        print("CHANGELOG [registra_avvio OK]: riga inserita correttamente")
    else:
        errori.append("CHANGELOG FAIL: riga di avvio non inserita nel file")

    launcher.registra_arresto_nel_changelog(motivo="Test-Arresto")
    risultato2 = changelog_test.read_text(encoding="utf-8")
    if "Test-Arresto" in risultato2 and "Attivo" not in risultato2:
        print("CHANGELOG [registra_arresto OK]: stato aggiornato correttamente")
    else:
        errori.append("CHANGELOG FAIL: stato di arresto non aggiornato")
finally:
    launcher.FILE_CHANGELOG = changelog_originale
    if changelog_test.exists():
        changelog_test.unlink()

# Pulizia file di log di test
if FILE_TEST.exists():
    FILE_TEST.unlink()

# ---------------------------------------------------------------------------
# Risultato finale
# ---------------------------------------------------------------------------
print()
if errori:
    print("=== CICLO 3: BUG TROVATI ===")
    for voce in errori:
        print(f"  [FAIL] {voce}")
    sys.exit(1)
else:
    print("=== CICLO 3: TUTTI I TEST SUPERATI - ZERO BUG ===")
    sys.exit(0)
