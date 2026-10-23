"""Esegue probe di sicurezza con log live e guard rigoroso sul DB di test."""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import sys

import pytest
from sqlalchemy.engine import make_url

BACKEND_PATH = Path(__file__).resolve().parents[1]
if str(BACKEND_PATH) not in sys.path:
    sys.path.insert(0, str(BACKEND_PATH))

from app.core.config import leggi_impostazioni
from app.core.log_jsonl import id_test_redatto, scrivi_jsonl


class RegistroValutazione:
    def __init__(self, percorso: Path):
        self.percorso = percorso
        percorso.write_text("", encoding="utf-8")

    def scrivi(self, event_type: str, **campi) -> None:
        evento = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            **campi,
        }
        scrivi_jsonl(
            self.percorso,
            json.dumps(evento, ensure_ascii=True, separators=(",", ":")),
        )


class PluginValutazione:
    def __init__(self, registro: RegistroValutazione):
        self.registro = registro

    def pytest_sessionstart(self, session) -> None:
        self.registro.scrivi("suite_started")

    def pytest_runtest_logstart(self, nodeid, location) -> None:
        self.registro.scrivi("test_started", test=id_test_redatto(nodeid))

    def pytest_runtest_logreport(self, report) -> None:
        evento = {
            "test": id_test_redatto(report.nodeid),
            "phase": report.when,
            "outcome": report.outcome,
            "duration_ms": round(report.duration * 1000, 2),
        }
        if report.failed:
            evento["failure"] = _errore_sintetico(report)
        self.registro.scrivi("test_phase_finished", **evento)

    def pytest_terminal_summary(self, terminalreporter, exitstatus, config) -> None:
        stats = terminalreporter.stats
        self.registro.scrivi(
            "suite_summary",
            exit_code=int(exitstatus),
            passed=len(stats.get("passed", [])),
            failed=len(stats.get("failed", [])),
            errors=len(stats.get("error", [])),
            skipped=len(stats.get("skipped", [])),
        )


def _errore_sintetico(report) -> str:
    """Riporta il punto e il tipo di errore, senza dump di input o credenziali."""
    crash = getattr(report.longrepr, "reprcrash", None)
    if crash is None:
        return "Errore senza dettagli strutturati."
    percorso = Path(crash.path).name if crash.path else "test"
    messaggio = str(crash.message)
    messaggio = re.sub(
        r"(?i)\b(password|token|secret|api[_-]?key|authorization)\b"
        r"(\s*[:=]\s*)[^,\s]+",
        r"\1\2[REDACTED]",
        messaggio,
    )
    messaggio = re.sub(
        r"(?:postgres(?:ql)?(?:\+\w+)?://)[^/\s:@]+:[^@\s/]+@",
        "postgresql://[REDACTED]@",
        messaggio,
    )
    return f"{percorso}:{crash.lineno}: {messaggio[:800]}"


def _righe_jsonl_non_valide(percorso: Path) -> list[int]:
    righe_non_valide = []
    with percorso.open(encoding="utf-8") as file:
        for numero, riga in enumerate(file, start=1):
            try:
                json.loads(riga)
            except json.JSONDecodeError:
                righe_non_valide.append(numero)
    return righe_non_valide


def _url_test_isolato(url: str) -> tuple[str, int]:
    parsed = make_url(url)
    host = (parsed.host or "").lower()
    if (
        parsed.database != "adflow_test"
        or host not in {"localhost", "127.0.0.1"}
        or parsed.port != 5432
    ):
        raise SystemExit(
            "Rifiuto di avviare i test distruttivi: DATABASE_URL_TEST deve puntare "
            "esattamente a adflow_test su localhost:5432."
        )
    return host, parsed.port


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--security-only",
        action="store_true",
        help="Esegue solo i probe SAST/DAST, senza inizializzare il DB di test.",
    )
    args = parser.parse_args()

    backend = BACKEND_PATH
    os.chdir(backend)
    impostazioni = leggi_impostazioni()
    url_test = impostazioni.database_url_test

    if args.security_only:
        test_url = make_url(url_test)
        host = (test_url.host or "").lower()
        if host not in {"localhost", "127.0.0.1"} or test_url.database != "adflow_test":
            raise SystemExit(
                "Rifiuto di avviare i probe: DATABASE_URL_TEST non punta "
                "esattamente al database locale adflow_test."
            )
    else:
        host, _ = _url_test_isolato(url_test)

    cartella_log = backend / "security-assessment-logs"
    cartella_log.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    percorso_log = cartella_log / f"valutazione-{timestamp}.jsonl"

    # Il limiter login usa DATABASE_URL tramite motore(), non DATABASE_URL_TEST.
    # In questo processo entrambi puntano esplicitamente al solo DB isolato.
    os.environ["DATABASE_URL"] = url_test
    os.environ["DATABASE_URL_TEST"] = url_test
    os.environ["REGISTRO_RICHIESTE_FILE"] = str(percorso_log)
    leggi_impostazioni.cache_clear()
    impostazioni_test = leggi_impostazioni()
    url_app = make_url(impostazioni_test.database_url)
    url_fixture = make_url(impostazioni_test.database_url_test)
    if (
        url_app.database != "adflow_test"
        or url_fixture.database != "adflow_test"
        or url_app.host not in {"localhost", "127.0.0.1"}
        or url_fixture.host not in {"localhost", "127.0.0.1"}
    ):
        raise SystemExit("Rifiuto di avviare i test: isolamento DB non verificato.")

    registro = RegistroValutazione(percorso_log)
    plugin = PluginValutazione(registro)
    registro.scrivi(
        "assessment_started",
        database="adflow_test",
        host=host,
        mode="security_only" if args.security_only else "full_suite",
    )
    print(f"Log valutazione: {percorso_log}", flush=True)
    print("Database verificato: adflow_test su localhost; URL app e fixture allineati.")

    test = (
        [
            "tests/test_sast_security.py",
            "tests/test_dast_security.py",
            "tests/test_log_jsonl.py",
        ]
        if args.security_only
        else ["tests"]
    )
    exit_code = int(pytest.main(["-q", "--tb=short", *test], plugins=[plugin]))
    righe_non_valide = _righe_jsonl_non_valide(percorso_log)
    registro.scrivi(
        "assessment_log_integrity",
        valid=not righe_non_valide,
        invalid_lines=righe_non_valide,
    )
    if righe_non_valide:
        exit_code = exit_code or 1
    registro.scrivi("assessment_finished", exit_code=exit_code)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
