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
## Sprint 1 · Scheletro che cammina

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

## Sprint 2a · Profilo e Campagna

### Corsia 0 · Comune (tutto il team)

| ID | Task | Tocca | Leggi | Dipende da | Fatto quando | ☐ |
|---|---|---|---|---|---|---|
| T2a-01 | **Apertura**: firme e tabelle | `alembic/` | plan §6 | T1-07 | firme approvate | ☐ |
| T2a-07 | **Chiusura**: percorso | `tests/percorsi/` | converge §4 | tutti i task dello sprint | CA verdi | ☐ |

### Corsia 3 · Contenuti (Giovanni)

| ID | Task | Tocca | Leggi | Dipende da | Fatto quando | ☐ |
|---|---|---|---|---|---|---|
| T2a-31 | Foto d'archivio nel piano: limiti | `contenuti/piano.py` | spec R-27 | T2a-01 | CA-76 | ☐ |
| T2a-32 | Logo nelle cartoline: dallo snapshot | `contenuti/cartoline.py` | spec R-40 | T1-01 | CA-77 | ☐ |

## Sprint successivi (si dividono in task quando si arriva)

## Follow-up · issue #16–17

| Issue | Corsia | Task / fatto quando | Preparato |
|---|---|---|---|
| #16 | 0/1 | Limite dei tentativi | ☑ |
| #17 | 0 | Prova nello staging | ☐ |
"""


def _per_id(corsie) -> dict:
    return {task.id: task for corsia in corsie for task in corsia.task}


def test_legge_corsie_task_e_follow_up_aperti():
    corsie, aperti = allinea.leggi_tasks(PAGINA)

    assert [(c.sprint, c.numero, c.nome, c.chi) for c in corsie] == [
        ("1", 0, "Comune", "tutto il team"),
        ("1", 3, "Contenuti", "Giovanni"),
        ("2a", 0, "Comune", "tutto il team"),
        ("2a", 3, "Contenuti", "Giovanni"),
    ]
    assert [t.id for t in corsie[1].task] == ["T1-31", "T1-34"]
    assert corsie[0].task[0].titolo == "Struttura"
    assert corsie[1].task[1].titolo == "Job `genera_campagna` a tappe"
    assert corsie[1].task[1].dipende_da == ["T1-31", "T1-01"]
    assert aperti == ["#17 (corsia 0): Prova nello staging"]


def test_legge_le_sigle_con_la_lettera_e_la_colonna_tocca():
    corsie, _ = allinea.leggi_tasks(PAGINA)
    task = _per_id(corsie)

    assert [t.id for t in corsie[3].task] == ["T2a-31", "T2a-32"]
    assert task["T2a-31"].tocca == "`contenuti/piano.py`"
    assert task["T2a-31"].leggi == "spec R-27"
    assert task["T2a-31"].dipende_da == ["T2a-01"]
    assert task["T2a-31"].fatto_quando == "CA-76"
    assert task["T2a-01"].dipende_da == ["T1-07"]  # da uno sprint all'altro
    assert task["T1-31"].tocca == ""  # la tabella dello sprint 1 non ha la colonna


def test_un_task_e_pronto_quando_le_dipendenze_sono_fatte():
    corsie, _ = allinea.leggi_tasks(PAGINA)
    manca = allinea.stato_dei_task(corsie)

    assert "T1-01" not in manca  # già fatto
    assert manca["T1-31"] == []  # pronto
    assert manca["T1-34"] == ["T1-31"]
    assert manca["T2a-01"] == ["T1-07"]
    assert manca["T2a-32"] == []


def test_la_chiusura_aspetta_solo_i_task_del_suo_sprint():
    corsie, _ = allinea.leggi_tasks(PAGINA)
    manca = allinea.stato_dei_task(corsie)

    assert manca["T1-07"] == ["T1-31", "T1-34"]
    assert manca["T2a-07"] == ["T2a-01", "T2a-31", "T2a-32"]


def test_lo_sprint_corrente_e_il_primo_con_un_task_da_fare():
    corsie, _ = allinea.leggi_tasks(PAGINA)
    assert allinea.sprint_corrente(corsie) == "1"

    for corsia in corsie:
        if corsia.sprint == "1":
            for task in corsia.task:
                task.fatto = True
    assert allinea.sprint_corrente(corsie) == "2a"

    for corsia in corsie:
        for task in corsia.task:
            task.fatto = True
    assert allinea.sprint_corrente(corsie) == "2a"  # tutto fatto: resta l'ultimo


def test_dei_prossimi_sprint_si_vedono_i_task_gia_pronti_della_corsia():
    corsie, _ = allinea.leggi_tasks(PAGINA)
    manca = allinea.stato_dei_task(corsie)

    pronti = allinea.pronti_in_anticipo(corsie, manca, "1", 3)
    assert [t.id for t in pronti] == ["T2a-32"]  # T2a-31 aspetta l'apertura
    assert allinea.pronti_in_anticipo(corsie, manca, "1", 0) == []
    assert allinea.pronti_in_anticipo(corsie, manca, "2a", 3) == []


def test_nome_del_branch_dal_titolo():
    corsie, _ = allinea.leggi_tasks(PAGINA)
    task = _per_id(corsie)
    assert allinea.nome_del_branch(task["T1-31"]) == "feature/T1-31-adattatore-ai"
    assert allinea.nome_del_branch(task["T1-34"]) == "feature/T1-34-job-genera-campagna"
    assert allinea.nome_del_branch(task["T2a-31"]) == "feature/T2a-31-foto-d-archivio"


def test_la_pagina_vera_si_legge_per_intero():
    """Ogni riga di task di tasks.md deve finire in una corsia, con dipendenze note."""
    testo = (RADICE / "docs" / "agenti" / "tasks.md").read_text("utf-8")
    corsie, _ = allinea.leggi_tasks(testo)

    sprint = list(dict.fromkeys(c.sprint for c in corsie))
    assert sprint == ["1", "2a", "2b", "3"]
    for uno in sprint:
        assert [c.numero for c in corsie if c.sprint == uno] == [0, 1, 2, 3, 4, 5]
    letti = [t.id for c in corsie for t in c.task]
    scritti = re.findall(r"^\| (T\d[ab]?-\d\d) \|", testo, flags=re.MULTILINE)
    assert letti == scritti
    assert len(letti) == len(set(letti))
    for corsia in corsie:
        for task in corsia.task:
            assert task.id.startswith(f"T{corsia.sprint}-{corsia.numero}")
            assert task.titolo and task.leggi and task.fatto_quando
            assert task.tutti or set(task.dipende_da) <= set(letti)
            # dallo sprint 2a ogni task dice quali file tocca
            assert task.tocca or corsia.sprint == "1"
    assert set(allinea.stato_dei_task(corsie)) <= set(letti)


def test_ogni_sprint_si_apre_e_si_chiude_con_la_corsia_0():
    """Dallo sprint 2a: `-01` apre e dipende dalla chiusura precedente, `-07` chiude."""
    testo = (RADICE / "docs" / "agenti" / "tasks.md").read_text("utf-8")
    corsie, _ = allinea.leggi_tasks(testo)
    task = _per_id(corsie)

    for sprint, precedente in [("2a", "1"), ("2b", "2a"), ("3", "2b")]:
        assert task[f"T{sprint}-01"].dipende_da == [f"T{precedente}-07"]
        assert task[f"T{sprint}-07"].tutti
