"""Tracciabilità requisito → CA → test (T4-101 della corsia 10).

Legge `docs/agenti/spec.md` — regole R-xx di §5, criteri CA-xx di §6, fuori
MVP di §7 — e i nomi dei test di `backend/tests`, e scrive
`docs/accettazione/report/T4-101-tracciabilita.md` con:

- la tabella CA → regole citate → test che lo coprono;
- i CA del perimetro senza test;
- i test_caNN che non hanno il loro CA nello spec;
- le regole R-xx del perimetro che nessun CA cita.

Lo «spec §6: il test porta l'ID nel nome» è il contratto usato qui: un test
`test_ca09_...` copre il CA-09. Il controllo a campione («il test verifica
davvero ciò che il CA dice») non è automatizzabile e sta nel report, a mano.

Solo libreria standard, come `allinea.py`. Si lancia dalla radice:

    uv run python docs/accettazione/strumenti/tracciabilita.py
"""

from __future__ import annotations

import re
import sys
from collections.abc import Iterator
from pathlib import Path

RADICE = Path(__file__).resolve().parents[3]
SPEC = RADICE / "docs" / "agenti" / "spec.md"
TESTS = RADICE / "backend" / "tests"
REPORT = RADICE / "docs" / "accettazione" / "report" / "T4-101-tracciabilita.md"
CAMPIONE = (
    RADICE / "docs" / "accettazione" / "report" / "T4-101-tracciabilita-campione.md"
)

RIGA_REGOLA = re.compile(r"^\| (R-\d+)(?: \([^)]*\))? \|(.+?)\|$", re.MULTILINE)
RIGA_CRITERIO = re.compile(r"^\| (CA-\d+) \|(.+?)\|$", re.MULTILINE)
NOME_TEST = re.compile(r"^\s*def (test_ca(\d+)_\w+)\(", re.MULTILINE)
REGOLE_CITATE = re.compile(r"\bR-\d+\b")


def sezioni(testo: str) -> dict[str, str]:
    """Le sezioni `## n. …` di spec.md, per numero."""
    risultato: dict[str, str] = {}
    for parte in re.split(r"^## ", testo, flags=re.MULTILINE)[1:]:
        numero = re.match(r"(\d+)\.", parte)
        if numero:
            risultato[numero.group(1)] = parte
    return risultato


def righe(sezione: str, schema: re.Pattern[str]) -> Iterator[tuple[str, str]]:
    for id, resto in schema.findall(sezione):
        yield id, resto.strip()


def test_per_ca() -> dict[str, list[str]]:
    """CA-xx → elenco di `percorso::nome` dei test che lo coprono."""
    mappa: dict[str, list[str]] = {}
    for file in sorted(TESTS.rglob("*.py")):
        testo = file.read_text("utf-8")
        for nome, numero in NOME_TEST.findall(testo):
            mappa.setdefault(f"CA-{int(numero):02d}", []).append(
                f"{file.relative_to(TESTS)}::{nome}"
            )
    return mappa


def tabella_ca(ca_perimetro, citazioni, test) -> list[str]:
    righe_out = ["| CA | Regole citate | Test |", "|---|---|---|"]
    for id, testo in ca_perimetro:
        regole = ", ".join(sorted(REGOLE_CITATE.findall(testo))) or "—"
        nomi = test.get(id, [])
        if len(nomi) <= 2:
            celle = "<br>".join(nomi) if nomi else "**nessuno**"
        else:
            celle = f"{len(nomi)} test: {nomi[0].split('::')[0]}"
        righe_out.append(f"| {id} | {regole} | {celle} |")
    return righe_out


def campione() -> list[str]:
    """La sezione manuale sta in un file a parte: lo script la include se c'è."""
    if CAMPIONE.exists():
        return CAMPIONE.read_text("utf-8").strip().splitlines()
    return ["(da compilare a mano in T4-101-tracciabilita-campione.md)"]


def main() -> int:
    testo_spec = SPEC.read_text("utf-8")
    parti = sezioni(testo_spec)
    regole_perimetro = list(righe(parti["5"], RIGA_REGOLA))
    ca_perimetro = list(righe(parti["6"], RIGA_CRITERIO))
    fuori = list(righe(parti["7"], RIGA_REGOLA)) + list(
        righe(parti["7"], RIGA_CRITERIO)
    )
    id_fuori = {id for id, _ in fuori}
    test = test_per_ca()

    # CA del perimetro senza test
    ca_senza_test = [id for id, _ in ca_perimetro if id not in test]
    # test_caNN il cui CA non è da nessuna parte nello spec
    id_spec = {id for id, _ in ca_perimetro} | id_fuori
    numero_test = re.compile(r"test_ca(\d+)")

    def ca_del_test(nome: str) -> str:
        return f"CA-{int(numero_test.search(nome).group(1)):02d}"

    test_senza_ca = sorted(
        nome
        for nomi in test.values()
        for nome in nomi
        if ca_del_test(nome) not in id_spec
    )
    # fuori MVP che hanno ancora il test in repository (il codice resta)
    fuori_con_test = sorted(id for id in id_fuori if id in test and id.startswith("CA"))
    # regole del perimetro che nessun CA del perimetro cita
    citati = {r for _, testo in ca_perimetro for r in REGOLE_CITATE.findall(testo)}
    regole_senza_ca = [id for id, _ in regole_perimetro if id not in citati]

    riga_ca_senza = [f"- {id}" for id in ca_senza_test] or ["— nessuno"]
    riga_test_senza = [f"- {nome}" for nome in test_senza_ca] or ["— nessuno"]
    riga_fuori = [f"- {id}" for id in fuori_con_test] or ["— nessuno"]
    riga_regole = [f"- {id}" for id in regole_senza_ca] or ["— nessuno"]
    righe_report = [
        "# T4-101 · Matrice di tracciabilità requisito → CA → test",
        "",
        "Generata da `docs/accettazione/strumenti/tracciabilita.py` (T4-101,",
        "corsia 10): legge `docs/agenti/spec.md` (§5 regole, §6 criteri,",
        "§7 fuori MVP) e i nomi dei test di `backend/tests`. Il contratto è",
        "quello di spec §6: il test porta l'ID nel nome (`test_ca09_...`).",
        "",
        f"- regole del perimetro (§5): **{len(regole_perimetro)}**;",
        f"- criteri del perimetro (§6): **{len(ca_perimetro)}**;",
        f"- fuori MVP (§7): **{len(id_fuori)}** tra regole e criteri;",
        f"- criteri coperti da almeno un test: **{sum(1 for id, _ in ca_perimetro if id in test)}"
        f" di {len(ca_perimetro)}**.",
        "",
        "## Tabella CA → regole citate → test",
        "",
        *tabella_ca(ca_perimetro, citati, test),
        "",
        "## CA del perimetro senza test",
        "",
        *riga_ca_senza,
        "",
        "## Test che non hanno il loro CA nello spec",
        "",
        *riga_test_senza,
        "",
        "## Fuori MVP con il test ancora nel repository",
        "",
        "Spec §7: dove il codice resta (gruppi `create_ai`, caroselli,",
        "archivio), il test resta. Gli altri CA di §7 non devono avere test.",
        "",
        *riga_fuori,
        "",
        "## Regole del perimetro che nessun CA cita",
        "",
        "Le regole di §5 che nessun criterio di §6 richiama nel testo: la",
        "copertura passa da altre regole citate oppure manca del tutto.",
        "",
        *riga_regole,
        "",
        "## Controllo a campione",
        "",
        *campione(),
        "",
    ]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(righe_report), "utf-8")
    print(f"Scritto {REPORT.relative_to(RADICE)}")
    print(f"CA senza test: {len(ca_senza_test)}; test senza CA: {len(test_senza_ca)}")
    print(f"Regole senza CA che le citi: {len(regole_senza_ca)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
