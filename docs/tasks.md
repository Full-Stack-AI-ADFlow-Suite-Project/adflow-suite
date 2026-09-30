# Tasks · AdFlow Suite

Checklist ordinata dei lavori. Come si prende ed esegue un task: [`constitution.md`](constitution.md) §6. Come si verifica: [`converge.md`](converge.md).

- **Un task = un branch = una PR** (`feature/<id>-<breve>`), circa mezza giornata di lavoro.
- Si prende solo un task con **tutti i prerequisiti chiusi** (colonna "Dipende da").
- Chi lo prende scrive il nome in "Assegnato a"; chi lo chiude cambia ☐ in ☑ nella stessa PR.
- "Fatto quando" + i criteri `CA-xx` di [`spec.md`](spec.md) §9 sono la definizione di fatto del task.
- Solo lo **sprint corrente** è diviso in micro-task; gli altri si dettagliano quando si arriva.
- Gli sprint non hanno date fisse: il ritmo si decide dopo lo sprint 1.

**Si parte da zero** nel repository del team (ADR-45): oggi ci sono solo lo scheletro di FastAPI e il template Vite.

---

## Task di analisi (senza codice)

Producono decisioni scritte (spec, plan, ADR), non codice.

| ID | Task | Serve prima di | Assegnato a | Fatto quando | Stato |
|---|---|---|---|---|---|
| A-01 | **AI e immagini, prompt**: che cosa fa il ritocco (luce, colori, ritaglio, sfondo?), con quali modelli e costi; prompt di analisi foto, generazione post, rigenerazione "da zero" e "da proposta"; formato della risposta dell'AI | in parallelo allo sprint 1; pronto per il 2b (prompt di rigenerazione) e il 3 (ritocco) | | spec §4 (2.1b) e plan §8 aggiornati, nuova ADR, prompt di esempio in `docs/` | ☐ |
| A-02 | **Campi del profilo**: confermare con un artigiano o un operatore reale quali campi dei passi 1–9 servono davvero | sprint 2a | | elenco confermato in spec §3 e plan §3; ADR se cambia qualcosa | ☐ |
| A-03 | **Libreria calendario** per Vedi campagna e dashboard artigiano | sprint 3 | | scelta con motivazione in plan §1 e ADR | ☐ |
| A-04 | **Pagine statiche mancanti**: Vedi campagna, elenco artigiani, metriche (come `AdFlow-operatore-artigiano.html`) | Vedi campagna: sprint 2b · elenco: sprint 3 · metriche: sprint 4 | | pagine in `docs/architettura/`, citate in spec §5.2 | ☐ |

---

## Sprint 1 · Scheletro che cammina (sul modello finale)

**Obiettivo:** un percorso completo e sottile, dal login alla pubblicazione simulata, usando già le forme definitive (canali[], fotografia del profilo, approvazione in blocco). Il profilo lo riempie un seed: le schermate della scheda arrivano nel 2a.

**Fuori dallo sprint 1:** scheda bottega e Bentornato (2a), rimanda / respingi / rigenera / scadenza / email (2b), ritocco foto, anagrafica, account social reali (3), metriche (4).

| ID | Task | Area | Dipende da | Assegnato a | Fatto quando | Stato |
|---|---|---|---|---|---|---|
| T1-01 | **Struttura del backend**: cartelle `app/` come da costituzione §4, `config.py` (pydantic-settings), `db.py`, `main.py` con `GET /api/health`, pytest con fixture sul database `adflow_test`, `.env.example` e README aggiornati | backend | — | | `uvicorn app.main:app` parte; il test di `/api/health` è verde | ☐ |
| T1-02 | **Alembic** e prima migrazione: `utente`, `sessione` | dati | T1-01 | | `alembic upgrade head` su un database vuoto e `downgrade base` funzionano | ☐ |
| T1-03 | **`domain.py`**: ruoli, stati e transizioni di campagna e post, valori ammessi, `verifica_transizione()` | backend | T1-01 | | test unitari: ogni transizione ammessa passa, ogni altra solleva errore | ☐ |
| T1-04 | **Autenticazione**: scrypt, login / logout / me, cookie httpOnly, sessione salvata come hash, dipendenza "richiede ruolo", comando CLI per creare utenti | backend | T1-02 | | CA-01, CA-02, CA-03 | ☐ |
| T1-05 | **Tabelle `profilo_bottega`, `campagna`, `foto`** nella forma definitiva (plan §3) + **seed demo**: un artigiano con profilo completo, un operatore, un admin | dati | T1-02, T1-03 | | migrazione applicata; `cli seed` crea i tre utenti e il profilo | ☐ |
| T1-06 | **Tabelle `post`, `versione_post`, `approvazione`, `decisione_campagna`, `pubblicazione`** (indice unico: un solo `ok` per post) | dati | T1-05 | | migrazione applicata; test: un secondo `ok` sullo stesso post fallisce | ☐ |
| T1-07 | **API campagne**: crea bozza, elenco, dettaglio, con vincoli (anticipo 3 giorni, durata ≤ 92 giorni, una bozza, periodi non sovrapposti) e permessi | backend | T1-04, T1-05 | | CA-04, CA-09, CA-10, CA-11, CA-12 | ☐ |
| T1-08 | **Adattatore archivio + API foto**: caricamento con controllo tecnico, gruppi con descrizione, eliminazione, lettura del file | backend | T1-07 | | CA-13; i nomi dei file li genera il server | ☐ |
| T1-09 | **Worker Procrastinate**: app, avvio, `coda.py` per accodare dall'API | backend | T1-02 | | un job di prova accodato dall'API viene eseguito dal worker in un test | ☐ |
| T1-10 | **Invio della campagna**: controlli, copia di canali / frequenza / obiettivo, `profilo_snapshot`, stato inviata, accodamento di `genera_campagna` | backend | T1-08, T1-09 | | CA-14, CA-15 | ☐ |
| T1-11 | **Adattatore AI**: interfaccia, provider **finto** (risposte fisse e configurabili, anche errori), provider LiteLLM collegato ma mai usato nei test, versione del prompt | backend | T1-01 | | test del provider finto; nessuna chiamata di rete nei test | ☐ |
| T1-12 | **Calcolo degli slot** (funzione pura): frequenza × settimane, limite foto × 2, canali alternati, niente slot nel passato (+15 min), orari preferiti | backend | T1-03 | | CA-17 come test unitario, più casi limite (1 foto, 1 settimana, un solo canale) | ☐ |
| T1-13 | **Validatore a regole**: lunghezza per canale, numero di hashtag, parole vietate e "cose da non dire", niente prezzi o premi inventati | backend | T1-03 | | test unitari per ogni regola | ☐ |
| T1-14 | **Job `genera_campagna`**: analisi (finta), slot, generazione, validazione con 3 riscritture poi `da_rivedere`, campagna in revisione; 3 esecuzioni poi `generazione_fallita`; API **Riprova** | backend | T1-06, T1-10, T1-11, T1-12, T1-13 | | CA-17, CA-18, CA-19, CA-20 | ☐ |
| T1-15 | **API revisione minima**: post della campagna con versione corrente e storico; **approva in blocco** (righe `approvazione` e `decisione_campagna`) | backend | T1-14 | | CA-21, CA-22 | ☐ |
| T1-16 | **Adattatore social simulato + `tick_pubblicazione`**: tentativo registrato prima di pubblicare, errori temporanei (3) e definitivi, campagna conclusa | backend | T1-06, T1-09 | | CA-36, CA-37, CA-38, CA-39 | ☐ |
| T1-17 | **Frontend base**: Mantine, `api.ts` (client e tipi), `auth.tsx`, pagina di login, instradamento per ruolo, proxy `/api` di Vite | frontend | T1-04 | | login e logout funzionano dal browser; `npm run build` e `npm run lint` puliti | ☐ |
| T1-18 | **Frontend artigiano minimo**: crea bozza, carica foto a gruppi con descrizione, invia, vede lo stato della campagna (la scheda completa arriva nel 2a) | frontend | T1-17, T1-10 | | percorso a mano descritto in converge §2 per lo sprint 1 | ☐ |
| T1-19 | **Frontend operatore minimo**: campagne da approvare, Vedi campagna in elenco (post, versione, "da rivedere"), Approva, Riprova | frontend | T1-17, T1-15 | | percorso a mano descritto in converge §2 per lo sprint 1 | ☐ |
| T1-20 | **Test del percorso completo** (API): login → bozza → foto → invio → worker finto → approva → tick → pubblicato → conclusa; chiusura dello sprint secondo converge §2 | test | T1-15, T1-16 | | test verde; tutti i CA dello sprint 1 verdi in converge §4 | ☐ |

**Si possono fare in parallelo:** dopo T1-01 → T1-02, T1-03, T1-11 insieme; dopo T1-03 → T1-12 e T1-13 insieme; il frontend (T1-17) parte appena il contratto di login (T1-04) è stabile. `models.py` e le migrazioni (T1-02, T1-05, T1-06) si fanno in ordine, da una persona alla volta.


---

## Sprint 2a · Scheda bottega *(da dettagliare)*

Pagina unica profilo + nuova campagna a partire da `architettura/AdFlow-scheda-bottega.html` (ADR-15). Richiede A-02.
- API `GET` / `PUT /profilo` con valori ammessi e obbligatori (ADR-21); `PATCH /campagne/{id}` in bozza.
- Schermate passi 1–12, Bentornato con "Va bene così" / "Modifica", ripresa della bozza (ADR-16, ADR-25).
- Eventi ricorrenti come lista nel profilo (ADR-18); foto a gruppi nella scheda (ADR-22, ADR-28).
- Criteri: CA-05, CA-06, CA-07, CA-08, CA-16.

## Sprint 2b · Revisione in blocco e motivi del No *(da dettagliare)*

Richiede A-01 (prompt di rigenerazione) e A-04 (statico di Vedi campagna).
- Rimanda (ADR-32); respingi con motivo `foto` / `altro` e foto segnate (ADR-33, ADR-40).
- `notifica`, adattatore email con catcher locale, job `invia_notifica` (ADR-37).
- Scadenza della campagna all'inizio nel tick (ADR-34).
- Rigenera il testo da zero o da un testo proposto, stessa foto, max 3; job `rigenera_post` (ADR-42, ADR-43).
- Nessuna modifica in campagna attiva; sospendi / riattiva / annulla (ADR-44).
- Vedi campagna: storico versioni e badge "da rivedere"; vista artigiano con regola di visibilità; motivo nel Bentornato.
- Criteri: CA-23 … CA-32.

## Sprint 3 · Ritocco foto, pagine operatore e affidabilità *(da dettagliare)*

Richiede A-01 (ritocco), A-03 (calendario), A-04 (statico elenco artigiani).
- `versione_foto`, ritocco AI in generazione, ritocca di nuovo e scegli foto (ADR-41 … ADR-43).
- Anagrafica artigiano, elenco artigiani e pagina artigiano (ADR-38, ADR-39).
- Account social simulato con collegamento e permesso scaduto → campagna sospesa (ADR-26).
- Vista calendario in Vedi campagna; promemoria 48 h; email di riepilogo all'artigiano.
- Criteri: CA-33, CA-34, CA-35, CA-40, CA-41, CA-42, CA-43.

## Sprint 4 · Monitoraggio e demo *(da dettagliare)*

Richiede A-04 (statico metriche).
- Metriche simulate e job giornaliero; pagina metriche operatore e dashboard artigiano; report settimanale.
- Test end-to-end nel browser; dati demo; prova con OpenAI reale.
- Criteri: CA-44, CA-45.
