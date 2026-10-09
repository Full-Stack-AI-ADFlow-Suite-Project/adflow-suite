"""`allinea.py` legge docs/agenti/tasks.md: se la forma della pagina cambia, qui si vede."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import re
import sys

RADICE = Path(__file__).resolve().parents[2]


def _allinea():
    spec = spec_from_file_location("allinea", RADICE / "allinea.py")
    modulo = module_from_spec(spec)
    sys.modules["allinea"] = modulo  # serve a dataclass per risolvere i tipi
    spec.loader.exec_module(modulo)
    return modulo


allinea = _allinea()

PAGINA = """
### Corsia 0 · Comune (tutto il team)

| ID | Task | Leggi | Dipende da | Fatto quando | ☐ |
|---|---|---|---|---|---|
| T1-01 | **Struttura**: albero | plan §1 | — | app avviata | ☑ |
| T1-07 | **Chiusura**: percorso | converge §3 | tutti i task dello sprint | CA verdi | ☐ |

### Corsia 3 · Contenuti (Giovanni)

| ID | Task | Leggi | Dipende da | Fatto quando | ☐ |
|---|---|---|---|---|---|
| T1-31 | Adattatore AI: interfaccia | plan §5 | T1-01 | nessuna rete | ☐ |
| T1-34 | Job `genera_campagna` a tappe: usa lo snapshot | plan §4 | T1-31, T1-01 | CA-17 | ☐ |

## Follow-up · issue #16–17

| Issue | Corsia | Task / fatto quando | Preparato |
|---|---|---|---|
| #16 | 0/1 | Limite dei tentativi | ☑ |
| #17 | 0 | Prova nello staging | ☐ |
"""


def test_legge_corsie_task_e_follow_up_aperti():
    corsie, aperti = allinea.leggi_tasks(PAGINA)

    assert [(c.numero, c.nome, c.chi) for c in corsie] == [
        (0, "Comune", "tutto il team"),
        (3, "Contenuti", "Giovanni"),
    ]
    assert [t.id for t in corsie[1].task] == ["T1-31", "T1-34"]
    assert corsie[0].task[0].titolo == "Struttura"
    assert corsie[1].task[1].titolo == "Job `genera_campagna` a tappe"
    assert corsie[1].task[1].dipende_da == ["T1-31", "T1-01"]
    assert aperti == ["#17 (corsia 0): Prova nello staging"]


def test_un_task_e_pronto_quando_le_dipendenze_sono_fatte():
    corsie, _ = allinea.leggi_tasks(PAGINA)
    manca = allinea.stato_dei_task(corsie)

    assert "T1-01" not in manca  # già fatto
    assert manca["T1-31"] == []  # pronto
    assert manca["T1-34"] == ["T1-31"]
    assert manca["T1-07"] == ["T1-31", "T1-34"]  # aspetta tutti gli altri


def test_nome_del_branch_dal_titolo():
    corsie, _ = allinea.leggi_tasks(PAGINA)
    assert allinea.nome_del_branch(corsie[1].task[0]) == "feature/T1-31-adattatore-ai"
    assert (
        allinea.nome_del_branch(corsie[1].task[1])
        == "feature/T1-34-job-genera-campagna"
    )


def test_la_pagina_vera_si_legge_per_intero():
    """Ogni riga di task di tasks.md deve finire in una corsia, con dipendenze note."""
    testo = (RADICE / "docs" / "agenti" / "tasks.md").read_text("utf-8")
    corsie, _ = allinea.leggi_tasks(testo)

    assert [c.numero for c in corsie] == [0, 1, 2, 3, 4, 5]
    letti = [t.id for c in corsie for t in c.task]
    scritti = re.findall(r"^\| (T\d-\d\d) \|", testo, flags=re.MULTILINE)
    assert letti == scritti
    assert len(letti) == len(set(letti))
    for corsia in corsie:
        for task in corsia.task:
            assert task.titolo and task.leggi and task.fatto_quando
            assert task.tutti or set(task.dipende_da) <= set(letti)
    assert set(allinea.stato_dei_task(corsie)) <= set(letti)
