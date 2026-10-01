# ADR · decisioni in vigore · AdFlow Suite

Una riga per decisione. Una decisione nuova è una riga nuova; quella che cambia si sposta in fondo, tra le sostituite. Le motivazioni stanno nelle note (`note-flusso.md` §10, `note-architettura.md` §1 e §3); il testo originale completo di ogni ADR è nella storia di git (il vecchio file ADR.md che stava in docs/, fino al 30/09/2026).

| ID | Data | Decisione |
|---|---|---|
| 01 | 25/09 | Monolite modulare (API) + worker separato, stesso codice Python (struttura interna: 49) |
| 02 | 25/09 | Python 3.11+, FastAPI, SQLAlchemy 2 + Alembic, PostgreSQL 16 |
| 03 | 25/09 | Coda e job pianificati con Procrastinate, dentro PostgreSQL |
| 04 | 25/09 | Frontend React + Vite + TypeScript, UI Mantine |
| 05 | 25/09 | Login con sessione lato server e cookie httpOnly |
| 06 | 25/09 | AI dietro adattatore, LiteLLM, primo provider OpenAI, provider finto |
| 07 | 25/09 | Social dietro adattatore, simulato nell'MVP |
| 08 | 25/09 | Un solo consorzio |
| 09 | 25/09 | Fase 1 locale, fase 2 Docker su server proprio |
| 10 | 25/09 | Monorepo `backend/`, `frontend/`, `docs/` |
| 11 | 25/09 | Test unitari + API su PostgreSQL reale; un solo end-to-end |
| 12 | 25/09 | Ogni rigenerazione o modifica crea una nuova versione; nulla si cancella |
| 13 | 25/09 | Pubblicazione idempotente: tentativo registrato prima della chiamata |
| 14 | 25/09 | Errore tecnico AI dopo 3 esecuzioni → `generazione_fallita`, Riprova dell'operatore |
| 16 | 26/09 | Ai rientri: Bentornato con "va bene così" / "modifica" (dal 47 in cima alla pagina Campagna) |
| 18 | 26/09 | Eventi ricorrenti come lista JSON nel profilo |
| 19 | 26/09 | La campagna ha un campo `descrizione` |
| 21 | 26/09 | Il profilo contiene esattamente i campi dei passi 1–9 (pagina Profilo) |
| 22 | 26/09 | Foto a gruppi: `gruppo_id` dal client, descrizione di gruppo obbligatoria all'invio |
| 23 | 26/09 | Canali, frequenza, obiettivo nel profilo, copiati all'invio; `canali[]` |
| 24 | 26/09 | All'invio `profilo_snapshot`; tutti i job della campagna usano quello |
| 25 | 26/09 | Una bozza per artigiano, campagne non sovrapposte, max 3 mesi |
| 26 | 26/09 | Account social fuori dalle pagine Profilo e Campagna; senza account alla pubblicazione → sospesa |
| 27 | 26/09 | Eventi e chiusure sono contesto per l'AI, non slot automatici |
| 28 | 26/09 | Controllo foto: JPG/PNG/WEBP, ≤ 10 MB, lato corto ≥ 1080 px |
| 29 | 26/09 | La generazione parte da sola all'invio |
| 30 | 28/09 | Approvazione in blocco della campagna: approva / rimanda / respingi |
| 32 | 28/09 | Rimanda = etichetta + nota, nessuno stato nuovo, nessuna email |
| 33 | 28/09 | Respingi = campagna `respinta`, email, si rifà da zero (integrata da 40) |
| 34 | 28/09 | Non approvata entro l'inizio → `scaduta`; promemoria 48 h prima |
| 35 | 28/09 | Anticipo minimo di 3 giorni, configurabile |
| 37 | 28/09 | Tabella `decisione_campagna`; notifiche ed email dallo sprint 2b |
| 38 | 28/09 | Anagrafica artigiano gestita solo dall'operatore |
| 39 | 28/09 | Dashboard operatore in 4 pagine, pulsante unico Vedi campagna |
| 40 | 30/09 | Respingi con motivo `foto` (con foto segnate) o `altro` |
| 41 | 30/09 | Ritocco AI delle foto in generazione, `versione_foto`, originale conservato |
| 42 | 30/09 | Sul post solo 3 interventi AI (ritocca, rigenera da zero, da proposta); niente modifica a mano |
| 43 | 30/09 | Cicli separati: 3 rigenerazioni del testo, 3 ritocchi per post |
| 44 | 30/09 | Nessuna modifica in campagna attiva o sospesa |
| 45 | 30/09 | Si riparte da zero nel repository del team; sprint 1 sul modello definitivo |
| 46 | 30/09 | Due canali di documentazione: appunti (fonte, `docs/appunti/`) e agenti (derivato, `docs/agenti/`) |
| 47 | 01/10 | Due pagine per l'artigiano: Profilo (passi 1–9) e Campagna (passi 10–11, riepilogo e invio) |
| 48 | 01/10 | Immagini create dall'AI su richiesta: spunta "Crea immagini con intelligenza artificiale" nella campagna, senza foto o in aggiunta; dettagli in A-05 |
| 49 | 01/10 | Backend ordinato per moduli di dominio: `accesso`, `notifiche`, `artigiani`, `campagne`, `contenuti`, `revisione`, `pubblicazione`, più `core` e `adapters` condivisi; un modulo usa solo i precedenti e solo dal loro `service`; resta un monolite con un database e una catena di migrazioni |
| 50 | 01/10 | Lavoro in sei corsie: 0 comune (tutto il team lavora e approva insieme: struttura, contratti, tabelle, stati, coda, seed, chiusura) e cinque personali in parallelo con revisione di gruppo (1 accesso e artigiani · Gianluca, 2 campagne · Silvia, 3 contenuti · Giovanni, 4 revisione e pubblicazione · Nilton, 5 frontend · Angelo). I due branch aperti sulla vecchia struttura a strati non si uniscono |
| 51 | 01/10 | Il repository riparte dai soli documenti: le cartelle `backend/` e `frontend/` dell'impalcatura iniziale si cancellano; il codice nasce con i task dello sprint 1 (T1-01 backend, T1-51 frontend) |

## Sostituite
| ID | Data | Decisione | Sostituita da |
|---|---|---|---|
| 15 | 26/09 | Profilo e nuova campagna in una sola pagina a passi | 47 |
| 17 | 26/09 | Profilo arricchito con i campi dell'intervista tipo | 21 |
| 20 | 26/09 | Foto a gruppi con descrizione duplicata per riga | 22 |
| 31 | 28/09 | In revisione sul post solo rigenera o modifica a mano | 42 |
| 36 | 28/09 | In campagna attiva modifica a mano già approvata | 44 |
