# Rapporto QA · T3-08 Sistemazione definitiva (parte 2)

## 1. Inventario approvato e interventi eseguiti

| Punto | Dove | Intervento e motivazione |
|---|---|---|
| 1 | `docs/agenti/plan.md` | Rimossa la colonna "Scritta in" dalla tabella dei contratti in §6 e rimosse le note d'apertura sulle firme degli sprint 2a/2b (`T2a-01`, `T2b-01`). Allineato il §5 (adattatore social Instagram) a quanto realizzato in `T3-42` (`backend/app/adapters/social/meta.py`: controllo del contenitore con due nuovi tentativi a pochi secondi e poi errore `temporaneo`). Aggiunta `OPENROUTER_API_KEY` in §1. |
| 2 | `backend/tests/percorsi/` | Rinominati i 4 file con riferimento agli sprint nel nome: `test_percorso_sprint1.py` → `test_percorso_base.py`, `test_percorso_sprint2a.py` → `test_percorso_profilo_e_bozza.py`, `test_percorso_sprint2b.py` → `test_percorso_revisione.py`, `test_revisione_sprint2b_ca.py` → `test_revisione_ca.py`. Aggiornate docstring, nomi di funzione (`test_percorso_base_completo`, `test_percorso_profilo_e_bozza_completo`, `test_percorso_revisione_completo`) e import in `test_ca116_percorso_corsia9.py` e `test_percorso_corsia6.py`. |
| 3 | `backend/tests/test_perimetro_mvp.py` | Raccolti in un unico file i test "non esiste più" del perimetro MVP: `test_prosegui_non_esiste_piu` (da `tests/moduli/revisione/test_router.py`), `test_la_stella_non_esiste_piu` e `test_una_stella_gia_salvata_non_conta_piu` (da `tests/moduli/campagne/test_foto_gruppi.py`), `test_una_stella_gia_salvata_non_e_piu_una_regola` (da `tests/moduli/contenuti/test_generazione.py`), `test_archivio_e_cartolina_non_sono_riempitivi_del_piano` (da `tests/moduli/contenuti/test_piano.py`), più `test_il_logo_non_esiste_piu` per verificare l'assenza degli endpoint del logo dal profilo. |
| 4 | `backend/app/moduli/campagne/service.py` | Rimosso il riferimento "dalla 2a" nella docstring di `foto_per_id()`. Mantenuta `campagne_di()` (chiamata da `contenuti/interventi.py`, `contenuti/storico.py` e `revisione/service.py`) e aggiornata la sua docstring con tutti i chiamanti reali. |
| 5 | `frontend/src/components/Guscio.tsx` | Verificato: mostra già solo le voci dell'MVP (In lavorazione, Nuovo artigiano, Storico AI per l'operatore; Le mie campagne, Nuova campagna, Profilo, Archivio foto per l'artigiano). |
| 6 | `frontend/src/api/esempi/` | Rimossi in `campagne.ts` e `revisione.ts` la campagna `11` in stato `piano_da_rivedere` e il riempitivo `cartolina` dai dati di esempio. |
| 7 | `frontend/tests/` | Già archiviata in `docs/archivio/frontend-tests/` con spiegazione in `docs/archivio/LEGGIMI.md`. |
| 8 | Configurazione e dipendenze | Verificata corrispondenza 1-a-1 tra i campi di `backend/app/core/config.py` (`Impostazioni`) e `backend/.env.example`. Rimossa da `backend/requirements.txt` la dipendenza `cryptography==50.0.2` (nessun import nel codice del progetto). |
| 9 | Codice morto | Scansione AST su `backend/app` e `backend/tests`: rimossi gli import inutilizzati in 17 file Python (lasciando intatti i file con dicitura `Congelato per l'MVP, ADR-114`). |
| 10 | Commenti sugli sprint passati | Rimossi i commenti con riferimenti a `sprint 1/2a/2b`, `T1-*`, `T2a-*`, `T2b-*` da 43 file attivi di `backend/app`, `backend/tests` e `frontend/src`. Restano esclusivamente il codice congelato (`Congelato per l'MVP, ADR-114`) e i dati di prova di `backend/tests/test_allinea.py`. |
| 11 | `docs/agenti/` → `docs/archivio/` | Spostati `brief-ai.md`, `brief-meta.md` e `brief-sistemazione.md` in `docs/archivio/`; aggiornati `docs/archivio/LEGGIMI.md`, `backend/README.md`, `AGENTS.md` e `docs/agenti/tasks.md`. |
| §2 | Decisioni concordate | Mantenuto il termine "corsia" in `allinea.py`, `docs/agenti/tasks.md`, `backend/tests/test_allinea.py` e `.vscode/tasks.json`; rimosso l'hook deprecato `mirrors-prettier` da `.pre-commit-config.yaml`. |

## 2. Numero dei test prima e dopo

- **Prima di T3-08**: `1996 passed`
- **Dopo T3-08**: `1997 passed` (`+1` per l'aggiunta di `test_il_logo_non_esiste_piu` in `backend/tests/test_perimetro_mvp.py`)
- **Test spostati in `backend/tests/test_perimetro_mvp.py`**:
  1. `test_prosegui_non_esiste_piu` (da `backend/tests/moduli/revisione/test_router.py`)
  2. `test_la_stella_non_esiste_piu` (da `backend/tests/moduli/campagne/test_foto_gruppi.py`)
  3. `test_una_stella_gia_salvata_non_conta_piu` (da `backend/tests/moduli/campagne/test_foto_gruppi.py`)
  4. `test_una_stella_gia_salvata_non_e_piu_una_regola` (da `backend/tests/moduli/contenuti/test_generazione.py`)
  5. `test_archivio_e_cartolina_non_sono_riempitivi_del_piano` (da `backend/tests/moduli/contenuti/test_piano.py`)

## 3. Verifica invarianza schema OpenAPI e controlli converge §1

- `git diff --no-index /tmp/openapi-prima.json /tmp/openapi-dopo.json` → **0 differenze** (7103 righe identiche).
- `uv run alembic upgrade head` → `013 (head)`
- `uv run pytest` → `1997 passed`
- `uv run pytest tests/test_confini.py` → `10 passed`
- `uv run black --check .` → `203 files would be left unchanged`
- `npm run lint` → `0 errors, 0 warnings`
- `npm run build` → `built in 1.02s`
