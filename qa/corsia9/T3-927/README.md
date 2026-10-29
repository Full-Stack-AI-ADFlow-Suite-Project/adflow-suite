# T3-927 · Prova della corsia 9

**Casella ☑.** CA-116 è verde, il percorso a mano è stato eseguito sull'app vera, il confronto visivo è fatto, le due prove negative mancanti sono fatte e la demo con l'AI vera e Facebook vero è stata eseguita da uno script automatico (`demo_reale.py`, «Demo con AI vera e Facebook vero» più sotto). Decisione di Giovanni del 29/10/2026: la demo si fa **solo su Facebook**; Instagram resta simulato (D1, converge §4 passo 5). Il confronto con le pagine statiche lo ha fatto un agente, non un collega: lo conferma chi rivede la PR #166.

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

### Demo con AI vera e Facebook vero (29/10/2026)

Script: [`demo_reale.py`](demo_reale.py), da lanciare a mano e mai da `pytest` (nei test nessuna chiamata reale): `uv run python qa/corsia9/T3-927/demo_reale.py --foto CARTELLA --si-spendo`. Crea il database nuovo `adflow_demo`, lo prepara con `cli.esegui_demo` (T3-06, due foto vere, solo Facebook), avvia API e worker veri con `AI_PROVIDER=litellm` e `SOCIAL_PROVIDER=meta` passati come variabili d'ambiente (`backend/.env` non toccato) e percorre i passi 1–6 di converge §4 con asserzioni; per il passo 5 riavvia API e worker con `OROLOGIO_GIORNI_AVANTI`. Il rapporto della corsa riuscita è in [`demo-reale-rapporto.md`](demo-reale-rapporto.md) (ora, id dei post, costo; nessun segreto).

Esito: **PROVA SUPERATA**. Costo AI vero della campagna: **0,0781 $** (CA-82; le chiamate sono le stesse di una campagna da 3 post: analisi di 2 foto, piano, 3 testi, una rigenerazione e 1 immagine; la stima di ~0,6 $ era per campagna più grande). Provati sul vero:
- passo 1: password provvisoria alla creazione, stessa email → 409, il nuovo artigiano entra (CA-79);
- passo 2: avviso «foto poche» al passo 12, invio senza dichiarazione 422, con dichiarazione inviata (CA-14, CA-54);
- passo 3: 3 post su Facebook, 1 con immagine AI e la dicitura, nessuna dicitura sui post con foto (CA-17, CA-57, CA-80), costo letto in Vedi campagna;
- passo 4: modifica a mano, testo rigenerato dall'AI, richiesta all'artigiano con foto segnata, l'artigiano carica la foto con la dichiarazione e risponde e non legge i post (403), la foto nuova entra con Cambia foto, approvazione, calendario (CA-71, CA-86…90, CA-56);
- passo 6: modifica dopo l'approvazione, sposta, annulla con nota, sospendi con nota (l'artigiano non la legge), riattiva (CA-84, CA-72, CA-85, CA-32);
- passo 5: il worker pubblica sulla Pagina di prova i 2 post approvati, un solo tentativo `ok` per post con l'id di Facebook; per ogni post, letto da Graph, il testo è quello approvato, la foto è senza GPS e dritta (le due foto di partenza avevano il GPS) e misura 720×900 (4:5); la campagna si conclude.

Limiti, detti con onestà:
- **Foto del post:** per «un'altra del gruppo» (CA-71) le foto del gruppo erano già tutte usate, quindi Cambia foto è provato con la foto nuova dell'artigiano (provenienza «richiesta»).
- **Passi 7, 8 e 9** non sono nello script: il confronto visivo è sopra, la respinta e le prove negative sono nel percorso a mano (esito sopra) e nei test automatici.
- **Sulla Pagina restano 4 post di prova, non 2:** la prima corsa ha pubblicato 2 post, poi il mio controllo su Graph usava un campo che per un post di Pagina non esiste (`images`); ho corretto lo script (`full_picture`) e rilanciato da database vuoto, che ha pubblicato altri 2 post. Se non li vuoi, si tolgono dalla Pagina.
- **Instagram:** simulato (D1), come deciso.
- **`avvia.py`:** non usato; stesso codice, porte (8020) e database diversi.
- `adflow_demo` esiste ancora (si elimina con `DROP DATABASE adflow_demo` solo se conferma Giovanni).

## Verifica finale (29/10/2026, branch `integrazione-finale`)

| Comando | Esito |
|---|---|
| `uv run pytest` (da `backend/`, `DATABASE_URL_TEST` su `adflow_test`) | 1996 passati |
| `uv run black --check .` | 239 file puliti |
| `npm run lint` (da `frontend/`) | nessun problema |
| `npm run build` | riuscito (solo l'avviso sulla dimensione dei pezzi, già noto) |
| `uv run python qa/corsia9/T3-927/demo_reale.py --foto … --si-spendo` | PROVA SUPERATA (vedi sopra) |

Attenzione: il `backend/.env` di questo worktree ha `DATABASE_URL_TEST` su `adflow_c_test`; con quel valore 5 test e 23 errori del modulo `accesso` falliscono perché controllano il nome `adflow_test`. Il `.env` non è stato toccato: la variabile si passa da fuori.

## Osservazioni, non toccate

- La risposta 409 di Rigenera immagine su una campagna attiva dice «la campagna è «attiva», il post è «approvato»»: nomi del database in un messaggio d'errore dell'API (`verifica_intervento`). Dall'interfaccia non si arriva: i pulsanti non ci sono dopo l'approvazione.
- Il voto dato per errore a 3 stelle prima di quello a 4 resta nel dettaglio (`37`): un voto nuovo non cancella i precedenti (CA-112), e il voto medio di quella campagna è 3,5.
- Con il provider finto la versione del prompt di ogni chiamata è `finto-1` e tempi e costi sono zero: i numeri per versione si leggono davvero solo con l'AI vera.
- Il limite dei tentativi di accesso (429) è scattato dopo molti accessi di prova: i contatori li ho azzerati solo in `adflow_t927`.

## Pulizia

Il database `adflow_t927` esiste ancora (ora con la campagna 4 approvata, la password dell'operatore cambiata e due post con data di prova): si elimina con `DROP DATABASE adflow_t927` solo se conferma Giovanni (come gli altri database di prova). I processi di API, worker e frontend sono fermi.
