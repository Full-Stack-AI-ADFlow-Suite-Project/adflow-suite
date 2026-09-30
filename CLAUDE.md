# AdFlow Suite · istruzioni per gli agenti AI

Progetto sviluppato in team, con metodo spec-driven. Prima di fare qualsiasi cosa:

1. Leggi **`docs/constitution.md`**: regole non negoziabili, sicurezza, standard, e al §6 come si esegue un task.
2. Prendi **un solo task** da **`docs/tasks.md`**, libero e con i prerequisiti chiusi. Lavora su un branch `feature/<id>-<breve>`, mai su `main`.
3. Leggi solo le sezioni di **`docs/spec.md`** (cosa e perché, criteri `CA-xx`) e **`docs/plan.md`** (come: dati, API, job) che il task cita. Le decisioni stanno in **`docs/ADR.md`**.
4. Prima della PR esegui la checklist di **`docs/converge.md`** §1 e spunta il task.

Regole rapide:
- Fai solo il task. Tutto il resto diventa un nuovo task o una domanda.
- Se un'informazione manca o due documenti si contraddicono, fermati e chiedi: non inventare requisiti.
- Niente segreti nel codice, niente chiamate AI / social / email reali nei test, niente logica di business nei router o nei task del worker.
- Codice e messaggi in italiano per il dominio; commit in italiano all'imperativo con prefisso (`feat:`, `fix:`, `test:`, `docs:`, `refactor:`, `chore:`).
- Se cambia una decisione: nuova riga in `docs/ADR.md` e aggiornamento di spec/plan nella stessa PR.
