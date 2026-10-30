# Archivio

Materiale che non serve più al lavoro di tutti i giorni: **non fa testo** (ADR-114, ADR-115). Vale `docs/agenti/`, e lì vale prima di tutto `perimetro-mvp.md`. Si conserva per la storia del progetto e come fonte per i deliverable (proposta tecnica e pitch). Non si modifica.

| Cosa | Da dove viene | Perché è qui |
|---|---|---|
| `appunti/` | `docs/appunti/` | Note sul flusso e sull'architettura, punti aperti fino al 12/10 e diagrammi 01–10 di prima dell'MVP (sorgente, PNG e strumenti per rigenerarli). Dove non tornano con `perimetro-mvp.md` vale quella. Il suo `LEGGIMI.md` descrive com'era la cartella |
| `novita/` | `docs/novita/` | Note datate di alcune PR degli sprint 1 e 2a: descrivono il codice di allora |
| `brief-T3-01.md` | `docs/agenti/` | Brief di T3-01 (perimetro nel codice), task chiuso con la PR #108 |
| `brief-ai.md` | `docs/agenti/` | Brief dell'area AI (T3-31…T3-34), tutti i task su `main` |
| `brief-meta.md` | `docs/agenti/` | Brief dell'area Meta (T3-41…T3-43), tutti i task su `main` |
| `brief-sistemazione.md` | `docs/agenti/` | Brief di T3-08 (sistemazione definitiva, parte 2), chiuso |
| `tasks-sprint-1-2.md` | `docs/agenti/tasks.md` | Task degli sprint 1, 2a e 2b con le caselle com'erano, e i follow-up chiusi delle issue #16–19, #39–41 e #44–45 |
| `converge-sprint-1-2.md` | `docs/agenti/converge.md` | Percorsi a mano con cui si sono chiusi gli sprint 1, 2a e 2b |
| `frontend-tests/` | `frontend/tests/` | Tre script Playwright (due della pagina Profilo, lanciati a mano durante lo sprint 2a, e `nuovo-artigiano.cjs` della pagina Nuovo artigiano, che usa Playwright già installato e due server Vite con `VITE_USA_ESEMPI=0`): non sono in `package.json` né nei controlli delle PR e Playwright non è una dipendenza. Si possono riprendere come base per i test dell'interfaccia |

Fuori dall'archivio: le pagine statiche dell'MVP in `docs/pagine/`, il registro delle decisioni in `docs/ADR.md`, la procedura di sicurezza dell'accesso in `docs/sicurezza-accesso.md`.

Nei file archiviati i percorsi sono quelli di allora: `docs/appunti/pagine/` oggi è `docs/pagine/`, `docs/appunti/ADR.md` è `docs/ADR.md`, il resto di `docs/appunti/` è in `docs/archivio/appunti/`.
