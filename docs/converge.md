# Converge · AdFlow Suite

Come si verifica che il codice **funzioni davvero** e rispetti [`spec.md`](spec.md). Un task o uno sprint è chiuso solo quando **converge**: tutti i controlli qui sotto sono verdi.

---

## 1. Convergenza di un task (prima di aprire la PR)

Da eseguire sul proprio branch, con `main` appena portato dentro.

**Comandi**
```bash
# backend (da backend/, ambiente virtuale attivo, PostgreSQL acceso)
alembic upgrade head
pytest
black --check .

# frontend (da frontend/)
npm run lint
npm run build
```

**Checklist nella descrizione della PR**
- [ ] Il "Fatto quando" del task in `tasks.md` è vero.
- [ ] Ogni `CA-xx` citato dal task ha un test che passa, ed è segnato in §4 qui sotto.
- [ ] Tutti i comandi sopra sono verdi.
- [ ] Nessun principio di `constitution.md` §1–3 violato (niente logica nei router, niente segreti, permessi controllati sul server, niente chiamate AI/social/email reali nei test).
- [ ] Se il task tocca il database: la migrazione sale e scende (`alembic downgrade -1` e di nuovo `upgrade head`).
- [ ] Se il task tocca l'interfaccia: controllo visivo (§5) con screenshot nella PR.
- [ ] `.env.example`, README e documenti aggiornati se servono; casella del task spuntata in `tasks.md`.

## 2. Convergenza di uno sprint

Uno sprint è chiuso quando:
1. tutti i suoi task in `tasks.md` sono ☑ e uniti a `main`;
2. su `main` appena scaricato, da un database vuoto, i comandi del §1 sono verdi;
3. tutti i `CA-xx` dello sprint sono ☑ nella mappa del §4;
4. il **percorso a mano** dello sprint funziona su un PC diverso da quello di chi l'ha scritto;
5. il controllo visivo (§5) è fatto per le schermate dello sprint;
6. **retrospettiva breve**: ciò che è emerso diventa una modifica a spec, plan o ADR (nuova riga), o un task nuovo. Poi si dettaglia lo sprint successivo in `tasks.md`.

### Percorso a mano · sprint 1
1. Database vuoto → `alembic upgrade head` → comando seed (artigiano, operatore, admin).
2. Avviare API, worker e frontend.
3. Entrare come **artigiano**: creare una bozza che inizia tra 4 giorni e dura 2 settimane; caricare 3 foto in 2 gruppi, con descrizione; inviare.
4. Vedere la campagna passare a "in generazione" e poi "in revisione" (AI finta).
5. Entrare come **operatore**: aprire Vedi campagna, controllare numero di post, canali alternati, foto usate al massimo 2 volte; approvare.
6. Portare avanti l'orologio (o impostare una data di test) e verificare che il tick pubblichi i post (social simulato) e che la campagna finisca "conclusa".
7. Prove negative: data di inizio tra 1 giorno, file PDF come foto, artigiano che apre la pagina operatore.

*I percorsi degli sprint 2a, 2b, 3 e 4 si scrivono quando si dettaglia lo sprint.*

## 3. Livelli di test (ADR-11)

| Livello | Cosa copre | Dove |
|---|---|---|
| **Unitari** | `domain.py` (transizioni), calcolo slot, validatore, lettura della risposta AI | `backend/tests/unit/` |
| **Servizi** | generazione, pubblicazione (ok, errore temporaneo × 3, errore definitivo, tentativo in corso), scadenze, chiusura campagna, cicli | `backend/tests/services/` |
| **API** | autenticazione, permessi (401 / 403 / 404), validazione input (422), stati (409), percorso completo | `backend/tests/api/` |
| **Adattatori** | provider AI finto e LiteLLM con risposta simulata, **senza rete**; social simulato; email verso catcher | `backend/tests/adapters/` |
| **End-to-end** | uno solo, a fine progetto: browser → pubblicazione simulata (CA-45) | sprint 4 |

Regole: PostgreSQL reale (`adflow_test`), ogni test parte da un database pulito, l'ora "adesso" si inietta (niente test che dipendono dall'orologio vero).

## 4. Mappa criteri → test

Si compila man mano: nella colonna "Test" il percorso del test (file::nome), nella colonna "Stato" ☑ quando è verde su `main`.

| CA | Sprint | Livello | Test | Stato |
|---|---|---|---|---|
| CA-01 | 1 | API | | ☐ |
| CA-02 | 1 | API | | ☐ |
| CA-03 | 1 | API | | ☐ |
| CA-04 | 1 | API | | ☐ |
| CA-05 | 2a | API + visivo | | ☐ |
| CA-06 | 2a | API + visivo | | ☐ |
| CA-07 | 2a | API | | ☐ |
| CA-08 | 2a | API + visivo | | ☐ |
| CA-09 | 1 | API | | ☐ |
| CA-10 | 1 | API | | ☐ |
| CA-11 | 1 | API | | ☐ |
| CA-12 | 1 | API | | ☐ |
| CA-13 | 1 | API | | ☐ |
| CA-14 | 1 | API | | ☐ |
| CA-15 | 1 | API | | ☐ |
| CA-16 | 2a | servizi | | ☐ |
| CA-17 | 1 | unitario + servizi | | ☐ |
| CA-18 | 1 | servizi | | ☐ |
| CA-19 | 1 | servizi + API | | ☐ |
| CA-20 | 1 | servizi | | ☐ |
| CA-21 | 1 | API | | ☐ |
| CA-22 | 1 | API | | ☐ |
| CA-23 | 2b | API | | ☐ |
| CA-24 | 2b | API | | ☐ |
| CA-25 | 2b | API + adattatore email | | ☐ |
| CA-26 | 2b | servizi | | ☐ |
| CA-27 | 2b | API + servizi | | ☐ |
| CA-28 | 2b | API | | ☐ |
| CA-29 | 2b | API | | ☐ |
| CA-30 | 2b | servizi | | ☐ |
| CA-31 | 2b | API + visivo | | ☐ |
| CA-32 | 2b | servizi | | ☐ |
| CA-33 | 3 | servizi | | ☐ |
| CA-34 | 3 | servizi | | ☐ |
| CA-35 | 3 | API | | ☐ |
| CA-36 | 1 | servizi | | ☐ |
| CA-37 | 1 | servizi | | ☐ |
| CA-38 | 1 | servizi | | ☐ |
| CA-39 | 1 | servizi | | ☐ |
| CA-40 | 3 | servizi | | ☐ |
| CA-41 | 3 | API + visivo | | ☐ |
| CA-42 | 3 | servizi | | ☐ |
| CA-43 | 3 | visivo | | ☐ |
| CA-44 | 4 | servizi | | ☐ |
| CA-45 | 4 | end-to-end | | ☐ |

Più i test degli **invarianti** della costituzione §1, che non hanno un CA proprio: nessuna versione cancellata, originale della foto sempre presente, stati cambiati solo da `verifica_transizione()`.

## 5. Controllo visivo

Le pagine statiche in `docs/architettura/` sono il riferimento per l'interfaccia.

| Pagina statica | Schermate reali | Sprint |
|---|---|---|
| `AdFlow-scheda-bottega.html` | scheda passi 1–12, Bentornato | 2a (messaggio di respinta: 2b) |
| Vedi campagna *(da fare, tasks.md A-04)* | Vedi campagna, interventi sui post, decisioni | 2b |
| `AdFlow-operatore-artigiano.html` | pagina artigiano dell'operatore | 3 |
| Elenco artigiani, metriche *(da fare, A-04)* | elenco artigiani, metriche | 3, 4 |

**Come si fa:** statico e pagina reale aperti affiancati, stessa larghezza (desktop e 375 px). Si controllano campi e ordine, testi ed etichette, obbligatori evidenziati, stati vuoti ed errori, stati della campagna. Le differenze volute si scrivono nella PR; quelle non volute si correggono. Screenshot di entrambe nella PR.

Nello sprint 1 le schermate sono minime e non hanno uno statico: basta il percorso a mano del §2.

## 6. Quando non converge

- **Un test fallisce su un comportamento scritto in spec** → si corregge il codice.
- **La spec è ambigua o sbagliata** → ci si ferma, si corregge la spec (con ADR se cambia una decisione) in una PR a parte, poi si riprende.
- **Il task era troppo grande** → si divide in `tasks.md` e si chiude solo la parte che converge.
