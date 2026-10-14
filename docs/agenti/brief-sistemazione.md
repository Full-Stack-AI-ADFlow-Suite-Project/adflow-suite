# Brief · T3-08 Sistemazione definitiva

Per l'agente o la persona che esegue T3-08. Leggi prima `constitution.md` e `perimetro-mvp.md`.

**Obiettivo.** Lasciare il repository come se fosse stato scritto oggi per l'MVP: i documenti di `docs/agenti/` descrivono solo ciò che vale adesso, il codice non porta resti degli sprint passati, i nomi sono coerenti, ciò che non serve non c'è. La storia non si perde: va in `docs/archivio/` o resta in git. **Nessun cambio di comportamento.**

**Quando.** Dopo che i task di codice dello sprint 3 sono su `main` (vedi "Dipende da" in `tasks.md`) e prima della chiusura (T3-07), entro il 29/10: il 30/10 il codice si blocca. Il task tocca molti file: mentre è aperto non si aprono altre PR di codice, e lo si dice al team prima di iniziare. Se non si fa in tempo, si fa dopo la consegna, prima di ripartire con la roadmap.

## Regole

1. **Stesso comportamento.** Stessi endpoint con le stesse risposte, stessi job, stesse pagine. Lo schema OpenAPI prima e dopo è identico (§5). Nessuna migrazione nuova o modificata: tabelle e colonne che non si leggono più restano (ADR-114).
2. **Il congelato resta.** Il codice segnato "Congelato per l'MVP, ADR-114" e i suoi test restano e non si estendono. Si possono sistemare solo nomi e commenti, senza toccare la logica.
3. **Inventario prima.** Per ogni blocco qui sotto prepara l'elenco di ciò che cambia, con il motivo. **Mostralo alla persona e aspetta la conferma** prima di cancellare o spostare.
4. **Un commit per blocco**, messaggio in italiano. Tocca composizione, `core/` e i `domain.py`: la PR la rivede il referente dei file comuni.
5. **Niente di nuovo.** Nessuna funzione e nessuna libreria nuova. Ciò che manca diventa un task o una voce della roadmap.

## 0. Prima di iniziare

1. Dalla radice: `uv run python allinea.py 0`; branch `feature/T3-08-sistemazione`.
2. Comandi di converge §1 tutti verdi. **Annota il numero dei test.**
3. Salva lo schema delle API: da `backend/`, `uv run python -c "import json; from app.main import app; print(json.dumps(app.openapi(), sort_keys=True, indent=1))" > ../openapi-prima.json` (il file non va in git).

## 1. Documenti di `docs/agenti/`

Ogni file deve descrivere lo stato di oggi. Gli ID delle regole (R-xx) e dei criteri (CA-xx) **non si rinumerano**: i test li portano nel nome.

| File | Cosa si fa |
|---|---|
| `tasks.md` | Gli sprint 1, 2a e 2b e i follow-up (#16–19, #39–41, #44–45) vanno in `docs/archivio/tasks-sprint-1-2.md`. In `tasks.md` restano le aree, le regole e i task dello sprint 3. Prima controlla che `allinea.py` e `tests/test_allinea.py` funzionino ancora |
| `spec.md` | Le regole e i CA *fuori MVP* (S = `–`) vanno in un'ultima sezione "Fuori MVP", con i loro ID, oppure in `docs/ROADMAP.md`. Le regole dell'MVP si riscrivono senza "dalla 2b", "sprint 3" e simili. In §6 la colonna S non serve più: tutto ciò che resta vale |
| `plan.md` | La colonna Sprint diventa Stato (MVP, congelato, roadmap); le righe roadmap di §3 e §4 vanno in fondo o in `ROADMAP.md`. Dalla storia delle migrazioni (§2) resta l'elenco 001–012 con una riga ciascuna. In §4 `genera_campagna` si descrive come lo fa il codice dopo T3-33 e T3-34. Via le note su aperture, firme con `NotImplementedError` e riallineamenti (T1-08, T1-09, T2a-01, T2b-01). In §6 resta la tabella dei contratti, senza la colonna "Scritta in" |
| `converge.md` | Il §3 e i percorsi degli sprint 2a e 2b vanno in archivio. Restano §1, §2 e il percorso della demo |
| `constitution.md` | L'albero del §2 uguale alle cartelle vere |
| `brief-ai.md`, `brief-meta.md` | In `docs/archivio/` quando i loro task sono su `main` |
| `perimetro-mvp.md` | Resta com'è: è la decisione |

E fuori da `docs/agenti/`: la sezione "Protezioni dell'accesso" del README va in `docs/sicurezza-accesso.md`; `docs/ROADMAP.md` riceve ciò che esce da spec e plan; la proposta tecnica si aggiorna se cita qualcosa che cambia.

## 2. Backend

| Cosa | Come |
|---|---|
| Test con il nome di uno sprint | `tests/percorsi/test_percorso_sprint1.py`, `…sprint2a.py`, `…sprint2b.py`, `test_revisione_sprint2b_ca.py`, `tests/moduli/campagne/test_funzioni_sprint2b.py`: rinominati per ciò che provano (es. `test_percorso_revisione.py`) |
| Test delle aperture e dei contratti | `test_t2a01_apertura.py`, `test_t2b01_apertura.py`, `test_t103_tabelle.py`, `test_t109_contratti.py`: i controlli che provano solo che una firma esiste si tolgono se un test di comportamento copre la stessa funzione; gli altri vanno nel file di test del modulo. Elenca nella PR ogni test tolto e il test che lo copre |
| Test che garantiscono le rimozioni | `test_prosegui_non_esiste_piu`, `test_la_stella_non_esiste_piu` e gli altri "non esiste più" si raccolgono in un solo `tests/test_perimetro_mvp.py` |
| Commenti e docstring | Via i rimandi a sprint e task ("dalla 2b", "T1-34", "sprint 3"); restano i rimandi a regole, CA e ADR |
| Contratti senza chiamanti | `campagne.service.campagne_di()` è usata solo dai test: si toglie, insieme alla sua riga in plan §6, oppure si dice dove serve. Stessa verifica per ogni funzione di plan §6 |
| Fabbriche | `tests/moduli/pubblicazione/fabbrica.py` e `revisione/fabbrica.py` sono vuote: si tengono (convenzione di constitution §2) con una riga che lo dice, oppure si tolgono aggiornando la costituzione. `__init__.py` in ogni cartella di test, come le altre. `campagna_con_piano_da_rivedere()` resta: serve per le righe vecchie |
| Configurazione | Ogni campo di `core/config.py` è letto da qualche parte ed è in `.env.example`, e viceversa |
| Dipendenze | Ogni riga di `requirements.txt` ha un import nel codice (Pillow, LiteLLM, la libreria HTTP di Meta…); quelle senza import si tolgono, dicendolo nella PR |
| Codice morto | Una ricerca degli oggetti mai usati (script con `ast`, oppure `uvx vulture app tests`, senza aggiungerlo a `requirements.txt`); ogni risultato si verifica a mano |

## 3. Frontend

| Cosa | Come |
|---|---|
| Dati di esempio (`src/api/esempi/`) | Con la forma delle API vere e dentro il perimetro: via la campagna in `piano_da_rivedere` con il piano debole, i resti di logo, stella e archivio, se T3-51 e T3-52 non li hanno già tolti |
| Barra laterale (`components/Guscio.tsx`) | Le voci dell'operatore sono quelle dell'MVP (Da approvare, Nuovo artigiano): via "Artigiani" e "Metriche" disabilitate con "arriva con lo sprint 3/4" |
| Export e file non usati | Uno script conta chi importa ogni file ed export di `src/`; i non usati si tolgono. Il codice congelato resta |
| Tipi | I tipi di `api/<modulo>.ts` rispecchiano lo `schemas.py` del modulo (constitution §4): via i campi che il backend non manda più |
| Commenti | Via i rimandi agli sprint; i percorsi delle pagine statiche sono `docs/pagine/…` |
| Pacchetto da 660 kB | Se serve, `React.lazy` per rotta: stesso comportamento, nessuna libreria nuova. Facoltativo |

## 4. Radice e strumenti

- `allinea.py` e `tasks.md` parlano ancora di "corsia": si può passare ad "area" in entrambi, insieme a `tests/test_allinea.py` e `.vscode/tasks.json`, oppure lasciare tutto com'è. Non a metà.
- `.pre-commit-config.yaml`: il mirror di prettier è deprecato. Si tiene e si dice nel README, oppure si sostituisce con un hook locale (`npx prettier`). Prima chiedi.
- `.github/workflows/`: stesse versioni di Python, Node e PostgreSQL che chiede il README.
- `.gitignore`: copre `.venv`, `backend/.env`, `backend/archivio_foto/`, `node_modules`, `dist`, `openapi-*.json`.
- README della radice, del backend e del frontend senza istruzioni superate.

## 5. Controlli e PR

1. Comandi di converge §1 verdi; `tests/test_confini.py` verde.
2. Schema delle API identico: rifai il comando del §0 in `../openapi-dopo.json`, poi `git diff --no-index ../openapi-prima.json ../openapi-dopo.json` non mostra differenze.
3. Nessun resto degli sprint fuori dall'archivio: `git grep -nE "sprint (1|2a|2b)|T1-[0-9]|T2a-|T2b-" -- docs/agenti backend/app frontend/src` trova solo righe motivate (per esempio le date degli sprint in `tasks.md`).
4. Da un clone pulito: `allinea.py`, migrazioni da database vuoto, test, lint e build verdi; seed e percorso della demo (converge §4) a mano con l'AI finta, senza errori.
5. PR: inventario approvato, file spostati e tolti con il motivo, numero dei test prima e dopo con l'elenco dei test tolti, schema delle API identico. Revisione del referente dei file comuni; merge dell'admin.
