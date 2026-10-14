# Brief · T3-08 Sistemazione definitiva, parte 2

Per l'agente o la persona che chiude T3-08. Leggi prima `constitution.md` e `perimetro-mvp.md`.

**Dove siamo.** La parte 1 è su `main`:
- `tasks.md` ha solo lo sprint 3; gli sprint chiusi sono in `docs/archivio/tasks-sprint-1-2.md`;
- `converge.md` ha i controlli, le prove a mano e il percorso della demo; i percorsi vecchi sono in `docs/archivio/converge-sprint-1-2.md`;
- `spec.md` raccoglie le regole e i CA fuori MVP nel §7;
- `plan.md` §1–§5 ha la colonna Stato;
- la procedura di sicurezza è riscritta;
- i test che portavano il nome di un task o di uno sprint sono rinominati;
- sono tolti i commenti superati nei file che nessuna PR aperta toccava.

Questa pagina dice **solo ciò che resta**: le parti che toccano file su cui c'erano PR aperte (#109, #110, #112, #113, #114, #119).

**Obiettivo.** Il repository descrive solo ciò che vale adesso. **Nessun cambio di comportamento.** A T3-08 chiuso, anche questa pagina va in `docs/archivio/`.

**Quando.** Quando i task di codice dello sprint sono su `main` (vedi "Dipende da" in `tasks.md`), entro il 29/10. Mentre il task è aperto non si aprono altre PR di codice: dillo al team prima di iniziare.

## Regole

1. **Stesso comportamento.** Stessi endpoint con le stesse risposte, stessi job, stesse pagine. Nessuna migrazione nuova o modificata.
2. **Il congelato resta.** Il codice segnato "Congelato per l'MVP, ADR-114" non si modifica, nemmeno nei commenti (per esempio `# Sprint 2b` in `notifiche/domain.py`).
3. **Inventario prima.** Per ogni punto qui sotto prepara l'elenco di ciò che cambia, con il motivo. **Mostralo alla persona e aspetta la conferma** prima di cancellare o spostare.
4. **Un commit per punto.** Tocca `core/` o i `domain.py`? Lo dici nella PR: la rivede il referente dei file comuni.

## 0. Prima di iniziare

1. Dalla radice: `uv run python allinea.py 0`; branch `feature/T3-08-sistemazione-parte-2`.
2. Comandi di converge §1 verdi. **Annota il numero dei test.**
3. Salva lo schema delle API da `backend/`: `uv run python -c "import json; from app.main import app; print(json.dumps(app.openapi(), sort_keys=True, indent=1))" > ../openapi-prima.json` (il file non va in git).

## 1. Che cosa resta

| # | Dove | Che cosa |
|---|---|---|
| 1 | `docs/agenti/plan.md` §6 e fondo | La tabella dei contratti senza la colonna "Scritta in"; via le note sulle firme degli sprint 2a e 2b (T2a-01, T2b-01): resta solo ciò che serve a chi usa le funzioni. Le sezioni aggiunte in fondo dai task (per esempio la risposta del calendario, la creazione dell'artigiano) vanno nel paragrafo giusto del §3. Il §5 social e `brief-meta.md` dicono due cose diverse sul contenitore di Instagram (controllo ogni minuto per 5 minuti, oppure due tentativi a pochi secondi): vale ciò che ha fatto T3-42, e l'altro documento si allinea |
| 2 | `backend/tests/percorsi/` | `test_percorso_sprint1.py`, `…sprint2a.py`, `…sprint2b.py` e `test_revisione_sprint2b_ca.py` rinominati per ciò che provano (es. `test_percorso_base.py`, `test_percorso_profilo_e_bozza.py`, `test_percorso_revisione.py`, `test_revisione_ca.py`), con docstring senza sprint e senza ID di task |
| 3 | Test "non esiste più" | `test_prosegui_non_esiste_piu` (revisione), `test_la_stella_non_esiste_piu` (campagne), quelli della stella in `test_generazione.py` e `test_piano.py`, quelli del logo in `test_profilo.py` e, se c'è ancora, `test_cartoline.py`: tutti in un solo `tests/test_perimetro_mvp.py` |
| 4 | `campagne/service.py` | Il commento "dalla 2a" di `foto_per_id()`. `campagne_di()` non ha chiamanti nel codice: si toglie, con la sua riga in plan §6 e il suo test in `test_canali_tolti_e_note.py`, oppure si scrive dove serve |
| 5 | `frontend/src/components/Guscio.tsx` | Le voci dell'operatore sono quelle dell'MVP (Da approvare, Nuovo artigiano): via "Artigiani" e "Metriche" disabilitate con "arriva con lo sprint 3/4" e il testo di riserva "lo sprint 2a" |
| 6 | `frontend/src/api/esempi/` | Dati di esempio dentro il perimetro: via la campagna in `piano_da_rivedere` con il piano debole e i resti di logo, stella e archivio, se T3-51 e T3-52 non li hanno già tolti |
| 7 | `frontend/tests/` | La PR #119 la riporta, con uno script Playwright e due screenshot. Due strade, da decidere con la persona: script con un comando `npm` e una riga nel README del frontend, e screenshot solo nelle PR; oppure in `docs/archivio/frontend-tests/`, come gli script dello sprint 2a |
| 8 | Configurazione | Ogni campo di `core/config.py` è in `.env.example` e viceversa (dopo T3-23, T3-31 e T3-42: `SOCIAL_PROVIDER`, `META_*`, `FOTO_URL_PUBBLICO`, `AI_MODELLO_IMMAGINI`; `COOKIE_SECURE` come riga commentata). Ogni riga di `requirements.txt` ha un import nel codice; le altre si tolgono, dicendolo nella PR |
| 9 | Codice morto | Ricerca degli oggetti mai usati nel backend (script con `ast`, oppure `uvx vulture app tests`, senza aggiungerlo a `requirements.txt`) e degli export mai importati nel frontend; ogni risultato verificato a mano. Il congelato resta |
| 10 | Commenti | `git grep -nE "sprint (1\|2a\|2b)\|T1-[0-9]\|T2a-\|T2b-\|\(2a\)\|\(2b\)" -- backend/app backend/tests frontend/src`: restano solo il codice congelato e i dati di prova di `tests/test_allinea.py` |
| 11 | `docs/agenti/` | `brief-ai.md` e `brief-meta.md` in `docs/archivio/` quando i loro task sono su `main`; `docs/archivio/LEGGIMI.md` aggiornato. Alla fine, anche questa pagina |

## 2. Da decidere con la persona, prima di toccare

- `allinea.py`, `tasks.md`, `tests/test_allinea.py` e `.vscode/tasks.json` chiamano le aree "corsie". Si può passare ad "area" in tutti e quattro insieme, oppure lasciare tutto com'è: non a metà.
- `.pre-commit-config.yaml` usa il mirror deprecato di prettier, che riformatta righe che il task non ha toccato. Si tiene, si fissa una versione di prettier con un hook locale (`npx prettier`) o si toglie l'hook dal frontend.

## 3. Controlli e PR

1. Comandi di converge §1 verdi; `tests/test_confini.py` verde.
2. Schema delle API identico: rifai il comando del §0 in `../openapi-dopo.json`, poi `git diff --no-index ../openapi-prima.json ../openapi-dopo.json` non mostra differenze.
3. Da un clone pulito: `allinea.py`, migrazioni da database vuoto, test, lint e build verdi; seed e percorso della demo (converge §4) a mano, senza errori.
4. PR: inventario approvato, file spostati e tolti con il motivo, numero dei test prima e dopo con l'elenco dei test tolti o spostati, schema delle API identico, casella di T3-08 spuntata. Revisione del referente dei file comuni; merge dell'admin.
