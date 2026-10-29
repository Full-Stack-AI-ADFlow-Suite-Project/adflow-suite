# T3-927 · Prova della corsia 9

**Casella ☐ (non spuntata).** CA-116 è verde, il percorso a mano è stato eseguito sull'app vera, il confronto visivo con le pagine statiche è fatto e le due prove negative mancanti sono fatte. Manca la demo di `converge.md` §4 con l'AI vera e Meta: Giovanni ha dato il «sì» il 29/10/2026, ma la demo non è partita perché manca il tunnel pubblico delle foto (dettaglio in fondo, «Cosa manca»). Giovanni non ha dichiarato accettabili i provider finti, quindi la casella resta vuota.

## (a) CA-116, test di percorso

File: `backend/tests/percorsi/test_ca116_percorso_corsia9.py` (un solo file nuovo). API vere, utenti del seed, job presi dalla coda, AI, social e archivio finti.

L'artigiano invia due campagne di una settimana della stessa bottega, con lo stesso periodo (la seconda ha una sola foto); `campagne_sovrapposte` compare nel dettaglio di tutte e due e il piano della seconda evita gli orari occupati. L'operatore, in revisione, fa «Rifai il post» su un post con foto (una foto della campagna al posto della vecchia, testo riscritto: versione `rigenera_totale`, un ciclo contato) e «Rigenera immagine» su un post con un'immagine AI (nuova immagine, stessa dicitura). Approva le due campagne. Lo storico dell'AI ha le chiamate di tutte e due le campagne (analisi, piano, testi; le immagini della seconda) e, dopo un voto di 4, i numeri della campagna (voto medio, immagini rigenerate, rigenerazioni del testo).

| Comando (da `backend/`, con `DATABASE_URL_TEST` su `adflow_test`) | Esito |
|---|---|
| `uv run pytest tests/percorsi/test_ca116_percorso_corsia9.py` | 1 passato |
| `uv run pytest` | vedi «Verifica finale» in fondo |
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
| 9 · prove negative | eseguito, comprese le due che mancavano (vedi sotto) | — |

Prove negative eseguite (tutte rifiutate come deve): inizio tra 1 giorno (422), durata di 3 giorni (422), un PDF come foto (422), canale non collegato (422), artigiano su una pagina dell'operatore (torna all'Ingresso), rigenerazione del testo e Rigenera immagine su una campagna attiva (409), Cambia immagine con «riscrivi il testo» dopo l'approvazione (422, «Dopo l'approvazione il testo non si riscrive con l'AI»), caricamento dell'artigiano dopo l'approvazione (409), nuovo artigiano con un'email già usata (409). Nessun errore di pagina né risposta 5xx in nessun passo.

Una campagna senza foto, tutta con immagini AI (A5), è stata inviata e generata per ripetere la finestra di Rigenera immagine (`19`): lo screenshot di prima aveva colto la spunta durante la sua animazione.

### Confronto visivo con le pagine statiche (converge §4, punto 7)

Fatto il 29/10/2026 da un agente (non da un collega: la persona che lo conferma è chi rivede la PR #166). Le pagine statiche aggiornate di T3-926 aperte in Chromium a 1280 px accanto agli screenshot di questa cartella (`10`, `11`, `34` e gli altri). Corrispondono: le cinque voci della barra dell'operatore (Da approvare, Artigiani, Calendario, Storico AI, Nuovo artigiano), i testi dei filtri e dei numeri dello Storico AI, le etichette degli stati, la barra di avanzamento a cinque passi, i pulsanti di Vedi campagna e il testo del 409. Differenze, tutte volute o già note:

| Dove | Pagina statica | App | Giudizio |
|---|---|---|---|
| Intestazione | Fascia «Pagina statica · MVP · ADR…», briciole di pane, pulsante «Vista Artigiano» | Nessuna | voluta: sono note per chi legge il prototipo |
| Barra, fondo | «Mappa Pagine» e «Laura Rossi / Operatore Consorzio» | «Esci» e «Operatore del consorzio» | voluta |
| Barra, Da approvare | Pallino con 4 | Nessun numero (il database di prova ha due campagne, il numero c'è nell'app solo quando ce ne sono) | da guardare con dati veri |
| Vedi campagna | Titolo = nome campagna; la decisione sta in una scheda sotto il riquadro di prova; avanzamento senza linee tra i passi; «Da rivedere» senza il pallino | Titolo «Vedi campagna» con il nome sotto; i pulsanti Approva, Chiedi, Respingi a destra della decisione; linee tra i passi; pallino davanti all'etichetta | il pallino è già in «Non simulato»; il resto è impaginazione: da dire ai revisori |
| Vedi campagna | Riquadro «Pagina statica interattiva · Prova» con selettore dello stato | Assente | voluta |
| Vedi campagna | Nessuna scheda «Il piano» | Scheda «Il piano» con l'ordine delle uscite e i conteggi | differenza di contenuto: da dire ai revisori |
| Storico AI | Dati di esempio (120 chiamate, 3,35 $, versioni `analisi_v2`…) e filtri in una scheda | Dati veri del database di prova (22 chiamate, 0 $, versione `finto-1`) e filtri senza scheda | i dati sono diversi per costruzione |
| Storico AI | Numeri in riquadri pieni | Numeri in riquadri con il bordo | colore, non testo |

### Prove negative che mancavano (passo 9)

- **Modifica di un post che esce entro 15 minuti.** A mano, su `adflow_t927`, con AI e social **finti**, API (porta 8010) e worker riavviati con `OROLOGIO_GIORNI_AVANTI=12`: la campagna 4 (in revisione, 3 post) è stata approvata; il post 19 era stato portato (solo in questo database) a «ora di prova + 10 minuti» e il post 20 a «+ 3 ore». Sul post 19: modifica, sposta, annulla e cambia foto rispondono tutti 409 «Il post esce tra meno di 15 minuti: non si tocca più.»; nessuna versione nuova, stato ancora `approvato`. Sul post 20 la modifica a mano riesce (200, versione `modifica_operatore`). API e worker sono stati fermati subito dopo, prima che il worker pubblicasse il post 19; nessuna chiamata reale. Per i 15 minuti non basta l'orologio in giorni interi: la data del post è stata scelta per cadere dentro la soglia.
- **Approva con un post da rivedere.** Test di percorso nuovo, `backend/tests/percorsi/test_prove_negative_corsia9.py` (API vere su `adflow_c_test`): con un post `da_rivedere` l'approvazione risponde 409, la campagna resta `in_revisione` e nessun post cambia stato. Lo stesso file ripete la prova dei 15 minuti con le API del test (4 interventi rifiutati, un post a più di 15 minuti modificabile). Non è stato fatto a mano perché l'AI finta non produce blocchi.

### Cosa manca per spuntare la casella

1. **AI vera e Meta: autorizzata, non eseguita.** Giovanni ha dato il «sì» (costo stimato ~0,6 $ per campagna; `SOCIAL_PROVIDER=meta` pubblica sulla pagina di prova vera). Prima di partire ho controllato la configurazione: in `backend/.env` `FOTO_URL_PUBBLICO` è ancora `https://esempio-tunnel.trycloudflare.com` (un segnaposto) e non c'è nessun tunnel acceso (né `cloudflared` né altro); `META_INSTAGRAM_ID` è vuoto (Instagram resta simulato, D1: si mostra solo Facebook); `OPENROUTER_API_KEY` è vuota mentre i modelli sono `openrouter/…` (c'è `OPENAI_API_KEY`: non so se basti). Senza un indirizzo pubblico per le foto Meta non può scaricarle e la pubblicazione fallirebbe: non ho lanciato una demo che costa e pubblica sapendo che si ferma a metà, e non posso cambiare `.env`. Servono: il tunnel acceso con il suo indirizzo (si può passare come variabile d'ambiente `FOTO_URL_PUBBLICO`), una conferma che la chiave AI è quella giusta, e la demo da database vuoto con i dati di T3-06. Restano da vedere il costo AI vero (CA-82) e i post su Facebook con foto dritta, senza GPS, nel formato del canale (CA-81, CA-83).
2. **Provider finti.** Giovanni non li ha dichiarati accettabili.
3. **Non con `avvia.py`.** Stesso codice, ma porte e database diversi (sopra).
4. Confronto visivo e prove negative: fatti (sopra); il confronto lo conferma chi rivede la PR.

## Verifica finale (29/10/2026, branch `integrazione-finale`)

| Comando | Esito |
|---|---|
| `uv run pytest` (da `backend/`, `DATABASE_URL_TEST` su `adflow_test`) | 1996 passati |
| `uv run black --check .` | 239 file puliti |
| `npm run lint` (da `frontend/`) | nessun problema |
| `npm run build` | riuscito (solo l'avviso sulla dimensione dei pezzi, già noto) |

Attenzione: il `backend/.env` di questo worktree ha `DATABASE_URL_TEST` su `adflow_c_test`; con quel valore 5 test e 23 errori del modulo `accesso` falliscono perché controllano il nome `adflow_test`. Il `.env` non è stato toccato: la variabile si passa da fuori.

## Osservazioni, non toccate

- La risposta 409 di Rigenera immagine su una campagna attiva dice «la campagna è «attiva», il post è «approvato»»: nomi del database in un messaggio d'errore dell'API (`verifica_intervento`). Dall'interfaccia non si arriva: i pulsanti non ci sono dopo l'approvazione.
- Il voto dato per errore a 3 stelle prima di quello a 4 resta nel dettaglio (`37`): un voto nuovo non cancella i precedenti (CA-112), e il voto medio di quella campagna è 3,5.
- Con il provider finto la versione del prompt di ogni chiamata è `finto-1` e tempi e costi sono zero: i numeri per versione si leggono davvero solo con l'AI vera.
- Il limite dei tentativi di accesso (429) è scattato dopo molti accessi di prova: i contatori li ho azzerati solo in `adflow_t927`.

## Pulizia

Il database `adflow_t927` esiste ancora (ora con la campagna 4 approvata, la password dell'operatore cambiata e due post con data di prova): si elimina con `DROP DATABASE adflow_t927` solo se conferma Giovanni (come gli altri database di prova). I processi di API, worker e frontend sono fermi.
