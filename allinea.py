"""Allinea la tua copia di AdFlow Suite e ti dice da dove ripartire.

Dalla radice del repository:

    uv run python allinea.py 3        la prima volta, con il numero della tua corsia
    uv run python allinea.py          le volte dopo: la corsia è ricordata
    uv run python allinea.py tutte    lo stato di tutte le corsie
    uv run python allinea.py --stato  solo lo stato dei task, senza toccare nulla

Cosa fa, in ordine: scarica le novità da GitHub e aggiorna `main` (mai il tuo
branch di lavoro, mai con modifiche non salvate di mezzo), installa le dipendenze
cambiate, porta il database all'ultima migrazione, poi legge `docs/agenti/tasks.md`
e stampa i task pronti della tua corsia, cosa leggere e il branch da aprire.

`tasks.md` ha una sezione per sprint (`## Sprint 2a · …`): lo sprint corrente è
il primo che ha ancora un task da fare. Dei successivi si vedono solo i task
della propria corsia che sono già pronti.

Usa solo la libreria standard: funziona anche prima di installare le dipendenze.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

RADICE = Path(__file__).resolve().parent
BACKEND = RADICE / "backend"
TASKS = RADICE / "docs" / "agenti" / "tasks.md"
CHIAVE_CORSIA = "adflow.corsia"

FATTO, DA_FARE = "☑", "☐"
# T1-23, T2a-11, T2b-41, T3-07: sprint (con la lettera, se c'è), corsia, numero.
ID_TASK = r"T\d[ab]?-\d\d"


# --- lettura di tasks.md -----------------------------------------------------


@dataclass
class Task:
    id: str
    titolo: str
    leggi: str
    dipende_da: list[str]
    fatto_quando: str
    fatto: bool
    tutti: bool = False  # dipende da tutti gli altri task dello sprint
    tocca: str = ""  # i file del task, dove la tabella ha la colonna "Tocca"


@dataclass
class Corsia:
    numero: int
    nome: str
    chi: str
    task: list[Task] = field(default_factory=list)
    sprint: str = ""


def _titolo(cella: str) -> str:
    grassetto = re.match(r"\*\*(.+?)\*\*", cella)
    if grassetto:
        return grassetto.group(1)
    prima = cella.split(":")[0].strip()
    return prima if len(prima) <= 60 else prima[:57] + "…"


def leggi_tasks(testo: str) -> tuple[list[Corsia], list[str]]:
    """Corsie di ogni sprint con i loro task e, a parte, i follow-up ancora aperti.

    Una riga di task ha 6 celle (ID, Task, Leggi, Dipende da, Fatto quando,
    casella) oppure 7, con "Tocca" dopo il task.
    """
    corsie: list[Corsia] = []
    aperti: list[str] = []
    sprint = ""
    for riga in testo.splitlines():
        titolo_sprint = re.match(r"## Sprint (\S+) · ", riga)
        if titolo_sprint:
            sprint = titolo_sprint.group(1)
            continue
        intestazione = re.match(r"### Corsia (\d) · (.+?) \((.+)\)\s*$", riga)
        if intestazione:
            numero, nome, chi = intestazione.groups()
            corsie.append(Corsia(int(numero), nome, chi, sprint=sprint))
            continue
        if not riga.startswith("|"):
            continue
        celle = [c.strip() for c in riga.strip().strip("|").split("|")]
        if re.fullmatch(ID_TASK, celle[0]) and len(celle) in (6, 7) and corsie:
            leggi, dipende_da, fatto_quando, casella = celle[-4:]
            corsie[-1].task.append(
                Task(
                    id=celle[0],
                    titolo=_titolo(celle[1]),
                    leggi=leggi,
                    dipende_da=re.findall(ID_TASK, dipende_da),
                    fatto_quando=fatto_quando,
                    fatto=casella == FATTO,
                    tutti="tutti i task" in dipende_da,
                    tocca=celle[2] if len(celle) == 7 else "",
                )
            )
        elif celle[0].startswith("#") and celle[-1] == DA_FARE:
            aperti.append(f"{celle[0]} (corsia {celle[1]}): {celle[2]}")
    return corsie, aperti


def stato_dei_task(corsie: list[Corsia]) -> dict[str, list[str]]:
    """Per ogni task da fare, i task da cui dipende che non sono ancora fatti.

    "Tutti i task dello sprint" vuol dire tutti gli altri del suo sprint.
    """
    fatti = {t.id for c in corsie for t in c.task if t.fatto}
    manca: dict[str, list[str]] = {}
    for corsia in corsie:
        dello_sprint = [
            t.id for c in corsie if c.sprint == corsia.sprint for t in c.task
        ]
        for task in corsia.task:
            if task.fatto:
                continue
            attesi = (
                [i for i in dello_sprint if i != task.id]
                if task.tutti
                else task.dipende_da
            )
            manca[task.id] = [i for i in attesi if i not in fatti]
    return manca


def sprint_corrente(corsie: list[Corsia]) -> str:
    """Il primo sprint con un task ancora da fare; se sono tutti fatti, l'ultimo."""
    for corsia in corsie:
        if any(not task.fatto for task in corsia.task):
            return corsia.sprint
    return corsie[-1].sprint if corsie else ""


def pronti_in_anticipo(
    corsie: list[Corsia], manca: dict[str, list[str]], corrente: str, numero: int
) -> list[Task]:
    """I task della corsia negli sprint dopo quello corrente che sono già pronti."""
    ordine = list(dict.fromkeys(c.sprint for c in corsie))
    dopo = ordine[ordine.index(corrente) + 1 :] if corrente in ordine else []
    return [
        task
        for corsia in corsie
        if corsia.sprint in dopo and corsia.numero == numero
        for task in corsia.task
        if not task.fatto and not manca[task.id]
    ]


_VUOTE = {"a", "e", "di", "del", "il", "la", "le", "con", "per", "da", "in"}


def nome_del_branch(task: Task) -> str:
    semplice = unicodedata.normalize("NFKD", task.titolo.lower())
    semplice = semplice.encode("ascii", "ignore").decode()
    parole = [p for p in re.findall(r"[a-z0-9]+", semplice) if p not in _VUOTE][:3]
    return f"feature/{task.id}-{'-'.join(parole)}"


# --- comandi -----------------------------------------------------------------


def esegui(*comando: str, dove: Path = RADICE) -> tuple[int, str]:
    """Lancia un comando e restituisce codice di uscita e ciò che ha scritto."""
    try:
        esito = subprocess.run(
            comando,
            cwd=dove,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except FileNotFoundError:
        return 127, f"comando non trovato: {comando[0]}"
    return esito.returncode, (esito.stdout + esito.stderr).strip()


def git(*argomenti: str) -> tuple[int, str]:
    return esegui("git", *argomenti)


def passo(nome: str, esito: str, dettaglio: str = "") -> None:
    print(f"  {nome:<12} {esito}")
    for riga in dettaglio.splitlines()[-6:]:
        print(f"               {riga}")


def allinea_repository() -> None:
    codice, _ = git("fetch", "--prune", "origin")
    if codice != 0:
        passo("GitHub", "non raggiungibile: lavoro con ciò che c'è in locale")
    _, branch = git("branch", "--show-current")
    _, sporco = git("status", "--porcelain", "--untracked-files=no")

    if branch == "main":
        if sporco:
            passo("main", "hai modifiche non salvate su main: non lo aggiorno")
            print(
                "               Su main non si lavora: sposta le modifiche su un branch."
            )
            return
        _, prima = git("rev-parse", "HEAD")
        codice, uscita = git("pull", "--ff-only", "origin", "main")
        _, dopo = git("rev-parse", "HEAD")
        if codice != 0:
            passo("main", "non riesco ad aggiornarlo", uscita)
        elif prima == dopo:
            passo("main", "già aggiornato")
        else:
            _, nuovi = git("rev-list", "--count", f"{prima}..{dopo}")
            passo("main", f"aggiornato: {nuovi} commit nuovi")
        return

    passo("branch", f"sei su {branch or '(nessun branch)'}")
    _, indietro = git("rev-list", "--count", "HEAD..origin/main")
    codice, _ = git("merge-base", "--is-ancestor", "HEAD", "origin/main")
    if codice == 0:
        print("               È già tutto in main: torna su main con `git switch main`")
        print("               e rilancia questo comando.")
    elif indietro.isdigit() and int(indietro) > 0:
        print(
            f"               main ha {indietro} commit nuovi. Quando sei a un punto fermo:"
        )
        print("               `git merge origin/main`. Se c'è un conflitto in un file")
        print("               con funzioni della corsia 0, tieni la versione di main.")
    else:
        print("               È già allineato a main.")
    if sporco:
        print("               Hai modifiche non salvate: non le ho toccate.")


def allinea_ambiente() -> bool:
    """Dipendenze, file .env e hook. Restituisce False se il database non è pronto."""
    if shutil.which("uv") is None:
        passo("dipendenze", "manca uv: installalo (vedi README) e rilancia")
        return False
    if not (RADICE / ".venv").exists():
        codice, uscita = esegui("uv", "venv", "--python", "3.11", "--seed", ".venv")
        if codice != 0:
            passo("ambiente", "non riesco a creare .venv", uscita)
            return False
        passo("ambiente", "creato .venv")
    codice, uscita = esegui(
        "uv", "pip", "install", "-q", "-r", "backend/requirements.txt"
    )
    passo(
        "dipendenze",
        "a posto" if codice == 0 else "errore",
        "" if codice == 0 else uscita,
    )

    if not (RADICE / ".git" / "hooks" / "pre-commit").exists():
        codice, _ = esegui("uv", "run", "pre-commit", "install")
        if codice == 0:
            passo("pre-commit", "installato")

    if not (BACKEND / ".env").exists():
        shutil.copyfile(BACKEND / ".env.example", BACKEND / ".env")
        passo("backend/.env", "creato da .env.example")
        print("               Aprilo, metti utente e password del tuo PostgreSQL in")
        print("               DATABASE_URL e DATABASE_URL_TEST, poi rilancia.")
        return False
    return True


def allinea_database() -> None:
    codice, uscita = esegui("uv", "run", "alembic", "upgrade", "head", dove=BACKEND)
    if codice == 0:
        passo("database", "all'ultima migrazione")
    else:
        passo("database", "non riesco a migrare", uscita)
        print(
            "               PostgreSQL è acceso? backend/.env ha le credenziali giuste?"
        )


def allinea_frontend() -> None:
    frontend = RADICE / "frontend"
    if not (frontend / "package.json").exists():
        return
    if (frontend / "node_modules").exists():
        passo(
            "frontend",
            "node_modules presente (dopo un cambio di package.json: npm install)",
        )
        return
    if shutil.which("npm") is None:
        passo("frontend", "manca npm: installa Node 22+")
        return
    codice, uscita = esegui("npm", "install", dove=frontend)
    passo(
        "frontend",
        "dipendenze installate" if codice == 0 else "errore",
        "" if codice == 0 else uscita,
    )


def pr_aperte() -> None:
    if shutil.which("gh") is None:
        return
    codice, uscita = esegui(
        "gh",
        "pr",
        "list",
        "--state",
        "open",
        "--limit",
        "20",
        "--json",
        "number,title,headRefName,reviewDecision",
        "--template",
        '{{range .}}#{{.number}} {{.title}} ({{.headRefName}}){{if eq .reviewDecision "CHANGES_REQUESTED"}} · modifiche richieste{{end}}{{"\\n"}}{{end}}',
    )
    if codice != 0:
        return
    print("\nPR aperte, da rivedere in gruppo:")
    for riga in uscita.splitlines() or ["nessuna"]:
        print(f"  {riga}")


# --- stampa dello stato --------------------------------------------------------


def stampa_corsia(corsia: Corsia, manca: dict[str, list[str]], esteso: bool) -> None:
    fatti = sum(t.fatto for t in corsia.task)
    print(
        f"\nCorsia {corsia.numero} · {corsia.nome} ({corsia.chi}) · {fatti}/{len(corsia.task)} task fatti"
    )
    da_fare = [t for t in corsia.task if not t.fatto]
    if not da_fare:
        print(
            "  Corsia completa per questo sprint: resta la revisione delle PR aperte."
        )
        return
    for task in da_fare:
        if manca[task.id]:
            attesa = ", ".join(manca[task.id])
            if task.tutti:
                attesa = f"tutti gli altri task ({len(manca[task.id])} ancora da fare)"
            print(f"  ·  {task.id} {task.titolo} · aspetta {attesa}")
            continue
        print(f"  →  {task.id} {task.titolo} · PRONTO")
        if esteso:
            print(f"       leggi:        constitution.md, poi {task.leggi}")
            if task.tocca:
                print(f"       tocca:        {task.tocca}")
            print(f"       fatto quando: {task.fatto_quando}")
            print(f"       branch:       git switch -c {nome_del_branch(task)}")


def corsia_ricordata() -> str:
    codice, valore = git("config", "--local", "--get", CHIAVE_CORSIA)
    return valore if codice == 0 else ""


def main(argomenti: list[str]) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    solo_stato = "--stato" in argomenti
    scelta = next((a for a in argomenti if not a.startswith("--")), "")

    if scelta and scelta != "tutte":
        if scelta not in "012345" or len(scelta) != 1:
            print("Corsia non valida: un numero da 0 a 5, oppure `tutte`.")
            return 2
        git("config", "--local", CHIAVE_CORSIA, scelta)
    elif not scelta:
        scelta = corsia_ricordata()

    print("AdFlow Suite · allineamento")
    if not solo_stato:
        allinea_repository()
        if allinea_ambiente():
            allinea_database()
        allinea_frontend()

    tutte, aperti = leggi_tasks(TASKS.read_text("utf-8"))
    manca = stato_dei_task(tutte)
    corrente = sprint_corrente(tutte)
    corsie = [c for c in tutte if c.sprint == corrente]
    totale = [t for c in corsie for t in c.task]
    print(
        f"\nSprint {corrente or '1'}: "
        f"{sum(t.fatto for t in totale)}/{len(totale)} task su main."
    )

    mie = [c for c in corsie if scelta.isdigit() and c.numero == int(scelta)]
    for corsia in mie or corsie:
        stampa_corsia(corsia, manca, esteso=bool(mie))
    anticipo = (
        pronti_in_anticipo(tutte, manca, corrente, int(scelta))
        if scelta.isdigit()
        else []
    )
    if anticipo:
        print("\nGià pronti negli sprint successivi, per la tua corsia:")
        for task in anticipo:
            print(f"  →  {task.id} {task.titolo}")
            print(f"       branch:       git switch -c {nome_del_branch(task)}")
    if not mie and scelta != "tutte":
        print(
            "\nPer vedere solo la tua corsia, con cosa leggere e il branch da aprire:"
        )
        print("  uv run python allinea.py <numero della corsia>")
    if aperti:
        print("\nFollow-up ancora aperti:")
        for riga in aperti:
            print(f"  {riga}")
    if not solo_stato:
        pr_aperte()

    pronti = [t for c in mie for t in c.task if not t.fatto and not manca[t.id]]
    if pronti:
        print(
            f"\nProssimo passo: {pronti[0].id}. Regole in AGENTS.md, controllo prima della PR in docs/agenti/converge.md."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
