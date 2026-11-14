"""Script ufficiale di generazione e aggiornamento di CHANGELOG.md per AdFlow Suite.

Estrae l'intera cronologia dei commit dal repository Git, cataloga ciascun commit
con tag semantico ([FEAT], [FIX], [SECURITY], [DOCS], [TEST], [REFACTOR], [CHORE], [MERGE])
e modulo/corsia di appartenenza, raggruppando le modifiche nelle fasi/sprint di progetto.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def trova_radice_repo() -> Path:
    """Individua la radice del repository Git corrente."""
    percorso_script = Path(__file__).resolve().parent
    # Se lo script è in adflow-suite/scripts, la radice del repo è la cartella genitore
    candidato = percorso_script.parent
    if (candidato / ".git").exists():
        return candidato
    # Fallback con git rev-parse
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )
        return Path(res.stdout.strip())
    except Exception:
        return candidato


REPO_PATH = trova_radice_repo()
OUTPUT_CHANGELOG = REPO_PATH / "CHANGELOG.md"


def estrai_commits(repo_path: Path) -> list[dict[str, str]]:
    """Estrae tutti i commit formattati dalla cronologia Git."""
    cmd = [
        "git",
        "-C",
        str(repo_path),
        "log",
        "--pretty=format:%h|||%cd|||%an|||%s",
        "--date=iso",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if res.returncode != 0:
        print(f"Errore durante l'esecuzione di git log: {res.stderr}", file=sys.stderr)
        sys.exit(res.returncode)

    righe = res.stdout.strip().splitlines()
    commits = []
    for r in righe:
        p = r.split("|||")
        if len(p) == 4:
            data_str = p[1].strip()
            dt_part = data_str[:19]
            tz_part = data_str[20:]
            commits.append(
                {
                    "hash": p[0].strip(),
                    "data_ora": dt_part,
                    "tz": tz_part,
                    "autore": p[2].strip(),
                    "messaggio": p[3].strip(),
                }
            )
    return commits


def determina_tag_e_corsia(messaggio: str) -> tuple[str, str]:
    """Determina il tag descrittivo e la corsia/modulo di competenza dal messaggio."""
    msg_low = messaggio.lower()

    # Identificazione del tag
    if msg_low.startswith("merge"):
        tag = "MERGE"
    elif msg_low.startswith("feat"):
        tag = "FEAT"
    elif msg_low.startswith("fix"):
        tag = "FIX"
    elif msg_low.startswith("docs"):
        tag = "DOCS"
    elif msg_low.startswith("test"):
        tag = "TEST"
    elif msg_low.startswith("chore"):
        tag = "CHORE"
    elif msg_low.startswith("refactor"):
        tag = "REFACTOR"
    elif any(
        k in msg_low for k in ["sicurezza", "sast", "dast", "sanitizz", "anti-dos"]
    ):
        tag = "SECURITY"
    elif "aggiung" in msg_low or "crea" in msg_low or "implement" in msg_low:
        tag = "FEAT"
    elif "corregg" in msg_low or "risolv" in msg_low:
        tag = "FIX"
    else:
        tag = "CHORE"

    # Identificazione della corsia / modulo
    if any(
        k in msg_low
        for k in [
            "foto",
            "archivio",
            "sistemazione",
            "immagini",
            "lato corto",
            "t3-21",
            "t3-22",
            "t3-23",
        ]
    ):
        corsia = "Corsia 2 · Campagne & Foto"
    elif any(
        k in msg_low
        for k in [
            "litellm",
            "prompt",
            "chiamata_ai",
            "generazione",
            "t3-31",
            "t3-32",
            "t3-33",
            "t3-34",
        ]
    ):
        corsia = "Corsia 3 · Motore AI & Testi"
    elif any(
        k in msg_low
        for k in [
            "meta",
            "facebook",
            "instagram",
            "pubblicazione",
            "tick",
            "social",
            "t3-42",
            "t3-43",
        ]
    ):
        corsia = "Corsia 4 · Meta & Pubblicazione"
    elif any(
        k in msg_low
        for k in [
            "frontend",
            "vetrina",
            "accesso",
            "wordmark",
            "react",
            "vite",
            "mantine",
            "guscio",
            "pagina",
        ]
    ):
        corsia = "Corsia 5 · Frontend & Interfaccia"
    elif any(
        k in msg_low
        for k in ["login", "session", "csrf", "auth", "utente", "ruolo", "artigiano"]
    ):
        corsia = "Corsia 1 · Accesso & Artigiani"
    elif any(
        k in msg_low
        for k in [
            "avvia",
            "worker",
            "procrastinate",
            "coda",
            "database",
            "alembic",
            "tabell",
            "contratt",
            "adr",
        ]
    ):
        corsia = "Corsia 0 · Core, Coda & Architettura"
    else:
        corsia = "Comune / Sistema"

    return tag, corsia


def raggruppa_per_fase(commits: list[dict[str, str]]) -> list[dict]:
    """Raggruppa i commit nelle fasi e negli sprint storici del progetto."""
    fasi = [
        {
            "id": "fase-7",
            "titolo": "Sviluppo Corrente, Risoluzione Bug e Rafforzamento Difese (Novembre 2026 - In corso)",
            "filtro": lambda c: c["data_ora"] >= "2026-11-06",
        },
        {
            "id": "fase-6",
            "titolo": "Sprint 5 · Chiusura, Vetrina Pubblica, Orchestratore e Design (1–5 Novembre 2026)",
            "filtro": lambda c: "2026-11-01" <= c["data_ora"] < "2026-11-06",
        },
        {
            "id": "fase-5",
            "titolo": "Sprint 4 · Accettazione, Hardening, Simulazione e Concorrenza (26–31 Ottobre 2026)",
            "filtro": lambda c: "2026-10-26" <= c["data_ora"] < "2026-11-01",
        },
        {
            "id": "fase-4",
            "titolo": "Sprint 3 · MVP Base: AI Vera, Sistemazione Foto e Pubblicazione Meta (15–25 Ottobre 2026)",
            "filtro": lambda c: "2026-10-15" <= c["data_ora"] < "2026-10-26",
        },
        {
            "id": "fase-3",
            "titolo": "Sprint 2b · Notifiche, Interventi e Macchina a Stati (11–14 Ottobre 2026)",
            "filtro": lambda c: "2026-10-11" <= c["data_ora"] < "2026-10-15",
        },
        {
            "id": "fase-2",
            "titolo": "Sprint 2a · Profilo Bottega, Gruppi Foto e Invio Bozza (8–10 Ottobre 2026)",
            "filtro": lambda c: "2026-10-08" <= c["data_ora"] < "2026-10-11",
        },
        {
            "id": "fase-1",
            "titolo": "Sprint 1 · Fondamenta Modulari, Tabelle PostgreSQL e Contratti (1–7 Ottobre 2026)",
            "filtro": lambda c: "2026-10-01" <= c["data_ora"] < "2026-10-08",
        },
        {
            "id": "fase-0",
            "titolo": "Setup Iniziale, Architettura e Reset Documentale (25–30 Settembre 2026)",
            "filtro": lambda c: c["data_ora"] < "2026-10-01",
        },
    ]

    risultati = []
    usati = set()
    for f in fasi:
        gruppo = []
        for c in commits:
            if c["hash"] not in usati and f["filtro"](c):
                gruppo.append(c)
                usati.add(c["hash"])
        risultati.append(
            {
                "id": f["id"],
                "titolo": f["titolo"],
                "commits": gruppo,
            }
        )
    return risultati


def genera_markdown(commits: list[dict[str, str]], gruppi: list[dict]) -> str:
    """Genera il documento Markdown completo e formattato."""
    testo = []
    testo.append("# Registro Ufficiale delle Modifiche al Software · AdFlow Suite\n\n")
    testo.append(
        "> **Documento Ufficiale di Progetto (`CHANGELOG.md`)**<br>\n"
        "> Tracciamento storico dettagliato di tutte le modifiche, interventi, rilasci e integrazioni al software "
        "dal primo commit del 25 Settembre 2026 ad oggi.<br>\n"
        "> Ogni voce riporta data e ora esatta (`YYYY-MM-DD HH:MM:SS`), autore, identificativo commit, "
        "etichetta di tipologia (`[FEAT]`, `[FIX]`, `[SECURITY]`, `[DOCS]`, `[TEST]`, `[REFACTOR]`, `[CHORE]`, `[MERGE]`) "
        "e l'area di competenza architetturale.\n\n"
    )
    testo.append("---\n\n")
    testo.append("## 🏷️ Guida alle Etichette (Taxonomy)\n\n")
    testo.append(
        "| Etichetta | Significato | Descrizione Operativa |\n"
        "|---|---|---|\n"
        "| `[FEAT]` | Nuova Funzionalità | Nuovi endpoint API, moduli di dominio, pagine frontend o logiche applicative |\n"
        "| `[FIX]` | Correzione Bug | Risoluzione di anomalie funzionali, difetti nei calcoli o test intermittenti (flaky) |\n"
        "| `[SECURITY]` | Sicurezza & Hardening | Difese anti-DoS, sanitizzazione input, rate-limiting, audit SAST/DAST e crittografia |\n"
        "| `[DOCS]` | Documentazione | Aggiornamento di ADR, specifiche funzionali (spec), piani tecnici e guide operative |\n"
        "| `[TEST]` | Collaudo & QA | Test di unità, integrazione, confini di dominio, carico con Locust o guasti ordinati |\n"
        "| `[REFACTOR]` | Refactoring | Riorganizzazione interna del codice senza modifiche al comportamento esterno |\n"
        "| `[CHORE]` | Manutenzione & Setup | Manutenzione dipendenze, file di configurazione (`.gitignore`, linters, scripts) |\n"
        "| `[MERGE]` | Integrazione PR | Fusione e approvazione formale di rami di lavoro su `origin/main` |\n\n"
    )
    testo.append("---\n\n")
    testo.append("## 📊 Indice Cronologico delle Fasi e degli Sprint\n\n")
    testo.append(
        "| Fase / Sprint | Periodo | N. Modifiche | Obiettivo Principale |\n"
        "|---|---|:---:|---|\n"
    )

    for g in gruppi:
        n_c = len(g["commits"])
        periodo = (
            g["titolo"].split(" (")[-1].rstrip(")") if " (" in g["titolo"] else "-"
        )
        nome_fase = g["titolo"].split(" (")[0]
        testo.append(
            f"| **{nome_fase}** | {periodo} | {n_c} commit | {g['titolo']} |\n"
        )

    testo.append("\n---\n\n")

    # Corpo dettagliato per ciascuna fase
    for g in gruppi:
        if not g["commits"]:
            continue
        testo.append(f"## 🚀 {g['titolo']}\n\n")
        testo.append(
            f"Totale modifiche registrate nella fase: **{len(g['commits'])}**\n\n"
        )
        testo.append(
            "| Data e Ora | Commit | Autore | Tipo | Corsia / Modulo | Descrizione Dettagliata della Modifica |\n"
            "|---|:---:|---|:---:|---|---|\n"
        )

        for c in g["commits"]:
            tag, corsia = determina_tag_e_corsia(c["messaggio"])
            msg_pulito = c["messaggio"].replace("|", "\\|")
            testo.append(
                f"| `{c['data_ora']}` | `{c['hash']}` | {c['autore']} | `[{tag}]` | **{corsia}** | {msg_pulito} |\n"
            )

        testo.append("\n---\n\n")

    return "".join(testo).strip() + "\n"


def aggiorna_changelog(
    repo_path: Path = REPO_PATH, output_path: Path = OUTPUT_CHANGELOG
) -> bool:
    """Estrae i commit e rigenera CHANGELOG.md se ci sono modifiche.

    Ritorna True se il file è stato creato o aggiornato, False se era già identico.
    """
    commits = estrai_commits(repo_path)
    gruppi = raggruppa_per_fase(commits)
    nuovo_contenuto = genera_markdown(commits, gruppi)

    if output_path.exists():
        vecchio_contenuto = output_path.read_text(encoding="utf-8").replace(
            "\r\n", "\n"
        )
        if vecchio_contenuto == nuovo_contenuto:
            print(
                f"Nessuna nuova modifica: {output_path.name} e' gia' aggiornato ({len(commits)} commit)."
            )
            return False

    output_path.write_text(nuovo_contenuto, encoding="utf-8", newline="\n")
    print(
        f"Aggiornato con successo {output_path} ({len(commits)} commit, {len(nuovo_contenuto)} byte)."
    )
    return True


if __name__ == "__main__":
    aggiorna_changelog()
