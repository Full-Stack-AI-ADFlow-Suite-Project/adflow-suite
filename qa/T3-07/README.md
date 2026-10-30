# Rapporto di Chiusura Sprint 3 · MVP (T3-07)

**Data:** 30 ottobre 2026
**Branch:** `feature/T3-07-chiusura` (unito su `main`)
**Riferimento:** [`docs/agenti/converge.md`](../../docs/agenti/converge.md) §1 e §4, [`docs/agenti/spec.md`](../../docs/agenti/spec.md) §6

---

## 1. Controlli automatici di `converge.md` §1

| Comando | Esito |
|---|---|
| `uv run alembic downgrade -1` + `uv run alembic upgrade head` | **PASS** (migrazioni `001` → `013 (head)` reversibili e pulite) |
| `uv run pytest` (su database PostgreSQL `adflow_test`) | **PASS** (**1.997 passed, 0 failed, 0 errors**) |
| `uv run pytest tests/test_confini.py` | **PASS** (**10 passed**) |
| `uv run pytest tests/test_perimetro_mvp.py` | **PASS** (**7 passed**) |
| `uv run python scripts/esegui_valutazione_sicurezza.py --security-only` | **PASS** (**34 passed**, SAST + DAST + integrità log JSONL) |
| `uv run black --check .` | **PASS** (`240 files would be left unchanged`) |
| `npm run lint` (da `frontend/`) | **PASS** (`0 warnings, 0 errors` su 96 file) |
| `npm run build` (da `frontend/`) | **PASS** (`tsc -b && vite build` completata senza errori) |

---

## 2. Copertura dei Criteri di Accettazione (`spec.md` §6)

Tutti i **96 criteri di accettazione attivi dell'MVP** (`CA-01`…`CA-116` in `docs/agenti/spec.md` §6; i 20 criteri fuori MVP sono raccolti in `spec.md` §7) hanno almeno un test automatico verde in `backend/tests/`:

- **Accesso, ruoli, sessioni e sicurezza** (`CA-01`…`CA-03`, `CA-61`…`CA-63`, `CA-79`): `tests/moduli/accesso/` e `tests/percorsi/test_percorso_base.py`
- **Profilo della bottega e fotografia all'invio** (`CA-05`…`CA-07`, `CA-14`…`CA-16`): `tests/moduli/artigiani/` e `tests/percorsi/test_percorso_profilo_e_bozza.py`
- **Bozza, gruppi foto, riepilogo e scelta immagini AI** (`CA-08`…`CA-13`, `CA-48`, `CA-54`, `CA-105`, `CA-109`): `tests/moduli/campagne/`
- **Generazione a tappe, piano, immagini AI, testi e gestione errori** (`CA-17`…`CA-20`, `CA-50`, `CA-57`…`CA-60`, `CA-68`, `CA-80`, `CA-82`, `CA-110`): `tests/moduli/contenuti/` e `tests/adapters/ai/`
- **Revisione, interventi sul post, inquadratura, richiesta all'artigiano e decisioni** (`CA-21`…`CA-32`, `CA-64`, `CA-66`, `CA-67`, `CA-69`…`CA-72`, `CA-84`…`CA-90`, `CA-106`…`CA-108`, `CA-111`, `CA-112`): `tests/moduli/revisione/`, `tests/moduli/contenuti/`, `tests/percorsi/test_percorso_revisione.py`, `tests/percorsi/test_percorso_corsia6.py`
- **Pubblicazione idempotente, sistemazione foto senza GPS e adattatore Meta** (`CA-36`…`CA-39`, `CA-81`, `CA-83`): `tests/moduli/pubblicazione/`, `tests/moduli/campagne/test_sistemazione_foto.py`, `tests/adapters/social/test_meta.py`
- **Archivio foto, elenchi campagne, stati leggibili e calendari** (`CA-56`, `CA-91`…`CA-104`): `tests/moduli/campagne/test_archivio.py`, `tests/moduli/contenuti/test_calendario.py`
- **Storico AI, numeri per versione del prompt, voti e percorso completo Corsia 9** (`CA-113`…`CA-116`): `tests/moduli/contenuti/test_storico_ai.py` e `tests/percorsi/test_ca116_percorso_corsia9.py`

---

## 3. Percorso della demo da database vuoto (`converge.md` §4) e Video di riserva

Il percorso completo in 9 passi di `converge.md` §4 è stato verificato sia nel browser a due finestre (operatore + artigiano, 49 schermate sequenziali in [`qa/corsia9/T3-927/`](../corsia9/T3-927/README.md)) sia con **AI vera (`AI_PROVIDER=litellm`) e pubblicazione reale sulla Pagina Facebook di prova (`SOCIAL_PROVIDER=meta`)** partendo da database vuoto con i dati del seed `T3-06` ([`qa/corsia9/T3-927/demo-reale-rapporto.md`](../corsia9/T3-927/demo-reale-rapporto.md)):

| Passo (`converge.md` §4) | Verifica effettuata | Esito | Evidenza |
|---|---|---|---|
| **1 · Nuovo artigiano** | Creazione da operatore, password provvisoria mostrata una sola volta (`CA-79`), secondo tentativo con stessa email → `409`, primo accesso al passo 1 del profilo | **PASS** | `01`–`03` in `qa/corsia9/T3-927/`, `demo-reale-rapporto.md` §1 |
| **2 · Invio campagna demo** | *Mosaici d'Arte*: conferma Bentornato, campagna di 7 giorni con inizio a +4 giorni, meno foto dei post chiesti, avviso al passo 12 sui post con immagine AI (`CA-54`), invio senza dichiarazione rifiutato (`422`), con dichiarazione → `inviata` (`CA-14`) | **PASS** | `04`–`10` in `qa/corsia9/T3-927/`, `demo-reale-rapporto.md` §2 |
| **3 · Generazione AI** | Avanzamento a 4 tappe, post chiesti per canale, selezione foto per punteggio, immagine AI 1:1 con dicitura sui post scoperti (`CA-17`, `CA-57`, `CA-80`), costo AI reale **`0,0781 $`** visibile in Vedi campagna (`CA-82`) | **PASS** | `10`, `11`, `18` in `qa/corsia9/T3-927/`, `demo-reale-rapporto.md` §3 |
| **4 · Revisione e Richiesta all'artigiano** | Modifica a mano, rigenerazione testo con AI, Rifai il post / Rigenera immagine, richiesta foto all'artigiano (`CA-86`), caricamento foto con dichiarazione nella finestra dell'artigiano (`CA-87`…`CA-90`), Cambia foto (`CA-71`), approvazione e calendario per giorno (`CA-56`) e settimana | **PASS** | `12`–`37` in `qa/corsia9/T3-927/`, `demo-reale-rapporto.md` §4 |
| **5 · Pubblicazione su Meta** | Con `OROLOGIO_GIORNI_AVANTI`, pubblicazione dal worker sulla Pagina Facebook di prova (`id 1343384632199586_122105993949518445` e `1343384632199586_122105994063518445`), un solo tentativo `ok` per post, foto `720×900` dritta e senza GPS (`CA-81`, `CA-83`), campagna `conclusa`; Instagram simulato secondo D1 | **PASS** | `43`–`46` in `qa/corsia9/T3-927/`, `demo-reale-rapporto.md` §5 |
| **6 · Interventi dopo l'approvazione** | Modifica di un post a > 15 min dall'uscita (`CA-84`), spostamento (`CA-72`), annullamento con nota (`CA-85`), sospensione con nota (l'artigiano legge «Pubblicazioni ferme» senza nota interna) e riattivazione (`CA-32`) | **PASS** | `38`–`42` in `qa/corsia9/T3-927/`, `demo-reale-rapporto.md` §6 |
| **7 · Controllo visivo e responsive** | Confronto tra app React e pagine statiche aggiornate (`docs/pagine/`) a 1280 px (desktop) e 375 px (telefono) per artigiano e operatore | **PASS** | `qa/corsia9/T3-901/`, `T3-902/`, `T3-926/`, `T3-927/` |
| **8 · Respinta campagna** | Seconda campagna respinta con motivo `foto`, nota e foto segnate; visualizzazione lato artigiano | **PASS** | `47`–`49` in `qa/corsia9/T3-927/` |
| **9 · Prove negative** | Inizio a +1 giorno (`422`), durata 3 giorni (`422`), file PDF (`422`), canale non collegato (`422`), artigiano su rotta operatore (`403` / redirect), rigenerazione su campagna attiva (`409`), intervento su post a < 15 min (`409`), upload artigiano dopo approvazione (`409`), approva con post da rivedere (`409`), email duplicata (`409`) | **PASS** | `tests/percorsi/test_prove_negative_corsia9.py` e `qa/corsia9/T3-927/README.md` |

### Video di riserva per il pitch

- **File:** [`qa/T3-07/demo-riserva.webm`](demo-riserva.webm)
- **Contenuto:** sequenza completa dei 49 passaggi del percorso della demo (`converge.md` §4, dall'accesso operatore/artigiano alla pubblicazione e conclusione della campagna), pronta per la riproduzione offline in aula durante il pitch del 6 novembre 2026.
