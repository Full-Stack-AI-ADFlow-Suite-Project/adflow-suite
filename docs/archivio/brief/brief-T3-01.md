# Brief · T3-01 Perimetro nel codice

Per l'agente che esegue T3-01 (fase 4 della semplificazione). Leggi prima `constitution.md` e `perimetro-mvp.md`.

**Obiettivo.** Togliere dal codice ciò che `perimetro-mvp.md` segna *Togli* e che non ha un altro task, e segnare il codice congelato. Nessuna funzione nuova, nessun cambio di comportamento oltre a quelli scritti qui: il resto è dei task dello sprint 3 · MVP.

## 0. Prima di iniziare

1. T2b-07 è su `main`. Dalla radice: `uv run python allinea.py 0`.
2. Branch `feature/T3-01-perimetro-codice`.
3. Da `backend/`: `uv run alembic upgrade head`, `uv run pytest`, `uv run black --check .`; da `frontend/`: `npm run lint`, `npm run build`. Tutto verde. **Annota il numero dei test**: va nella PR.

## 1. Inventario (prima di cancellare)

Per ogni decisione qui sotto cerca nel repository (backend, frontend, test) funzioni, endpoint, schemi, componenti, dati di esempio e test collegati. I file elencati sono un punto di partenza, non l'elenco completo. **Mostra l'inventario alla persona e aspetta la conferma** prima di cancellare.

## 2. Togli (un commit per decisione, codice e test insieme, il messaggio cita ADR-114)

| Decisione | Cosa si toglie | Da dove partire |
|---|---|---|
| A3 · Piano debole e Prosegui | `POST /campagne/{id}/prosegui` e la sua funzione; il pulsante Prosegui; la generazione non si ferma più in `piano_da_rivedere`; la transizione `in_generazione → piano_da_rivedere`; il test di CA-49 | `revisione/router.py`, `revisione/service.py`, `contenuti/generazione.py`, `contenuti/piano.py`, `campagne/domain.py`, `frontend/src/pages/operatore/` |
| A7 · Logo | `PUT`, `GET`, `DELETE /profilo/logo`; `artigiani/logo.py`; il logo nelle cartoline; la sezione Logo del passo 7; i test di CA-77 e CA-78 e `frontend/tests/logo-anteprima.cjs` | `artigiani/router.py`, `artigiani/logo.py`, `artigiani/profilo_schemas.py`, `contenuti/cartoline.py`, `pages/artigiano/profilo/passo7/SezioneLogo.tsx`, `api/artigiani.ts`, `api/esempi/artigiani.ts` |
| A11 · Stella | `PUT /foto/{id}` `{da_usare}`; la regola R-23 nel controllo del piano e nell'analisi (`simile_a` che passa all'altra foto); la stella nel passo 11; i test di CA-51 e dell'issue #45 | `campagne/router.py`, `campagne/service.py`, `contenuti/piano.py`, `contenuti/generazione.py`, `pages/artigiano/campagna/Passo11.tsx`, `api/campagne.ts` |

Non togliere qui il minimo di 4 foto (lo fa T3-22) né le cartoline (le toglie T3-34, quando arrivano le immagini AI).

**Cosa non si tocca mai:** migrazioni e tabelle (colonne come `profilo_bottega.logo` e `foto.da_usare` restano, non si leggono più); i valori ammessi nei `domain.py` che il database può già contenere (`piano_da_rivedere`, `proseguita`, `cartolina`): restano, così le righe vecchie si leggono ancora.

## 3. Congela (nessuna modifica, solo il commento)

In testa ai file, o sopra le funzioni se il file contiene anche codice dell'MVP, il commento `# Congelato per l'MVP, ADR-114: non estendere.` (nel frontend `// Congelato per l'MVP, ADR-114: non estendere.`):

- A8 caroselli: la pubblicazione con più foto (`pubblicazione/service.py`);
- A10 archivio: `campagne/archivio.py`, `pages/artigiano/profilo/passo7/SezioneArchivio.tsx`;
- B4 e B5: nota interna, togli canale, spunta, sospendi, riattiva, annulla, riprogramma (`revisione/decisioni.py`, `revisione/sospensione.py`, `revisione/interventi.py`, `pages/operatore/vedi-campagna/decisioni/`);
- D4 notifiche: `notifiche/`, `adapters/email/`.

Nasconderli nell'interfaccia è compito di T3-51 e T3-52, non di questo task.

## 4. Controlli e PR

1. I comandi del §0 di nuovo verdi; `tests/test_confini.py` verde; `uv run python allinea.py tutte --stato` legge lo sprint 3 · MVP.
2. A mano: login, profilo, campagna, invio, generazione con l'AI finta, Vedi campagna, approvazione, pubblicazione simulata.
3. PR: le decisioni applicate (A3, A7, A11 e i file congelati), il numero dei test prima e dopo, i CA tolti (CA-49, CA-51, CA-77, CA-78). Revisione del referente dei file comuni, perché il task tocca `domain.py`; merge dell'admin.
