# T3-927 · Prova della corsia 9

**Casella ☐ (non spuntata).** CA-116 è verde e il percorso a mano è stato eseguito davvero, con screenshot, sull'app vera (API, worker e frontend). Ma la demo di `converge.md` §4 è scritta con l'AI vera e Meta, e qui i due provider erano finti; il confronto visivo con le pagine statiche e due prove negative non sono state fatte. Il dettaglio è in fondo («Cosa manca»).

## (a) CA-116, test di percorso

File: `backend/tests/percorsi/test_ca116_percorso_corsia9.py` (un solo file nuovo). API vere, utenti del seed, job presi dalla coda, AI, social e archivio finti.

L'artigiano invia due campagne di una settimana della stessa bottega, con lo stesso periodo (la seconda ha una sola foto); `campagne_sovrapposte` compare nel dettaglio di tutte e due e il piano della seconda evita gli orari occupati. L'operatore, in revisione, fa «Rifai il post» su un post con foto (una foto della campagna al posto della vecchia, testo riscritto: versione `rigenera_totale`, un ciclo contato) e «Rigenera immagine» su un post con un'immagine AI (nuova immagine, stessa dicitura). Approva le due campagne. Lo storico dell'AI ha le chiamate di tutte e due le campagne (analisi, piano, testi; le immagini della seconda) e, dopo un voto di 4, i numeri della campagna (voto medio, immagini rigenerate, rigenerazioni del testo).

| Comando (da `backend/`, con `DATABASE_URL_TEST` su `adflow_test`) | Esito |
|---|---|
| `uv run pytest tests/percorsi/test_ca116_percorso_corsia9.py` | 1 passato |
| `uv run pytest` | 1990 passati (1989 della corsia + CA-116) |
| `uv run black --check .` | 237 file puliti |

Controllo che il test non sia vuoto: due copie temporanee con un'asserzione sbagliata (intervento in corso e voto medio) falliscono proprio su quelle righe; le copie sono state cancellate.

## (b) Percorso a mano in due finestre (operatore e artigiano)

**Come è stato eseguito, con precisione.** `uv run python avvia.py` così com'è non l'ho lanciato: il `backend/.env` del worktree ha `AI_PROVIDER=litellm` e `SOCIAL_PROVIDER=meta` (reali) e punta al database di sviluppo `adflow`, e la porta 8000 è occupata da un altro processo. Invece, senza toccare né `.env` né `adflow`:
- un database nuovo `adflow_t927` (migrazioni fino alla 013, e `downgrade -1` + `upgrade head` provati lì), seed degli utenti;
- API (`uvicorn`, porta 8010) e worker (Procrastinate) veri, con `DATABASE_URL`, `AI_PROVIDER=finto` e `SOCIAL_PROVIDER=finto` passati come variabili d'ambiente;
- frontend vero (Vite, porta 5232) con il proxy `/api` verso la 8010, avviato da uno script fuori dal repo;
- due finestre di Chromium (Playwright), una dell'operatore e una dell'artigiano, con la loro sessione. Per la pubblicazione API e worker sono stati riavviati con `OROLOGIO_GIORNI_AVANTI=12`.

Nessun `git push`, nessuna chiamata reale ad AI, Meta o email.

### Passi di converge §4 e di T3-927

| Passo | Esito | Immagini |
|---|---|---|
| 1 · l'operatore crea un artigiano, password provvisoria vista una volta (CA-79); la stessa email → 409; l'artigiano entra e arriva al passo 1 del profilo | eseguito | 01, 02, 03 |
| 2 · campagna di 7 giorni su Facebook e Instagram, inizio tra 4 giorni, «1 settimana» (7 giorni accettati dal server); gruppi di foto; passo 12 con i post con immagine AI (2 su 3 per canale nella seconda, CA-54); invio senza dichiarazione: pulsante spento e server 422; con la dichiarazione: inviata (CA-14) | eseguito | 04, 05, 06, 07, 08 |
| 2b · campagne sovrapposte: la seconda campagna della stessa bottega con lo stesso periodo, avviso «Nello stesso periodo hai già un'altra campagna…» al passo 12 | eseguito | 09, 10 |
| 3 · generazione col worker vero (AI finta): post chiesti per canale, immagini AI con la dicitura; costo in Vedi campagna (0,00 $ perché il provider è finto, quindi CA-82 non è provato qui) | eseguito, costo non significativo | 10, 11, 18 |
| 4 · l'operatore modifica un testo, rigenera un altro (vuoto → `totale`, visto dalla rete), cambia immagine con una foto della campagna e testo riscritto (**Rifai il post**), **Rigenera immagine** su un'immagine AI (3 per post), chiede all'artigiano una foto (CA-86); nella seconda finestra l'artigiano vede la richiesta, carica la foto con la dichiarazione e risponde (CA-87, CA-88, CA-90; non legge i post: 403); l'operatore usa la foto nuova (CA-71); approva (conferma inline); calendario per giorno (CA-56) | eseguito | 12–17, 18–21, 22–28, 29–32 |
| 4b · **Storico AI**: le chiamate di tutte e due le campagne (22), filtri per tipo e campagna, dettaglio con richiesta e prompt, voto da 1 a 5 con nota, numeri con «voto medio», «immagini rigenerate», «rigenerazioni del testo» | eseguito | 34–37 |
| 5 · pubblicazione: con l'orologio avanti di 12 giorni il worker pubblica i post approvati (il post annullato no) e le campagne si concludono | eseguito con il social **finto**: non si è visto un post su Facebook né su Instagram | 43, 44, 45, 46 |
| 6 · dopo l'approvazione: modifica a mano (versione dell'operatore), Cambia immagine senza quarta scelta né spunta, sposta, annulla con la nota, sospendi con nota (l'artigiano legge «Pubblicazioni ferme», non la nota) e riattiva (CA-84, CA-72, CA-85, CA-32) | eseguito | 38–42 |
| 8 · respinta: una campagna con foto non della bottega, «Respingi» con motivo foto, nota e foto segnate; l'artigiano rilegge nota e foto da rifare | eseguito | 47, 48, 49 |
| 9 · prove negative | vedi sotto | — |

Prove negative eseguite (tutte rifiutate come deve): inizio tra 1 giorno (422), durata di 3 giorni (422), un PDF come foto (422), canale non collegato (422), artigiano su una pagina dell'operatore (torna all'Ingresso), rigenerazione del testo e Rigenera immagine su una campagna attiva (409), Cambia immagine con «riscrivi il testo» dopo l'approvazione (422, «Dopo l'approvazione il testo non si riscrive con l'AI»), caricamento dell'artigiano dopo l'approvazione (409), nuovo artigiano con un'email già usata (409). Nessun errore di pagina né risposta 5xx in nessun passo.

Una campagna senza foto, tutta con immagini AI (A5), è stata inviata e generata per ripetere la finestra di Rigenera immagine (`19`): lo screenshot di prima aveva colto la spunta durante la sua animazione.

### Cosa manca per spuntare la casella

1. **AI vera e Meta.** La demo di converge §4 si fa con `AI_PROVIDER=litellm` e `SOCIAL_PROVIDER=meta`. Qui: AI e social finti. Mancano il costo AI vero (CA-82), i prompt v3 sulle immagini vere (T3-925, serve il tuo «sì») e i post visti su Facebook e Instagram con foto dritta, senza GPS e nel formato del canale (CA-81, CA-83).
2. **Confronto visivo (§4, punto 7).** Gli screenshot ci sono, ma il confronto con le pagine statiche aggiornate (T3-926, che attendono la rilettura) lo fa una persona (converge §3).
3. **Due prove negative non fatte:** modifica di un post che esce entro 15 minuti (serve un orologio puntato su quell'ora) e «approva con un post da rivedere» (l'AI finta non produce blocchi; è coperto dai test del backend).
4. **Non con `avvia.py`.** Stesso codice, ma porte e database diversi (sopra).

## Osservazioni, non toccate

- La risposta 409 di Rigenera immagine su una campagna attiva dice «la campagna è «attiva», il post è «approvato»»: nomi del database in un messaggio d'errore dell'API (`verifica_intervento`). Dall'interfaccia non si arriva: i pulsanti non ci sono dopo l'approvazione.
- Il voto dato per errore a 3 stelle prima di quello a 4 resta nel dettaglio (`37`): un voto nuovo non cancella i precedenti (CA-112), e il voto medio di quella campagna è 3,5.
- Con il provider finto la versione del prompt di ogni chiamata è `finto-1` e tempi e costi sono zero: i numeri per versione si leggono davvero solo con l'AI vera.
- Il limite dei tentativi di accesso (429) è scattato dopo molti accessi di prova: i contatori li ho azzerati solo in `adflow_t927`.

## Pulizia

Il database `adflow_t927` esiste ancora: si elimina con `DROP DATABASE adflow_t927` solo se conferma Giovanni (come gli altri database di prova). I processi di API, worker e frontend sono fermi.
