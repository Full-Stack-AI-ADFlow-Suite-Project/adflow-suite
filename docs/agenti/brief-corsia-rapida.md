# Brief · Corsie 11, 12 e 13 · Corsia rapida (T5-111…T5-136)

Per chi fa un task delle corsie rapide. Decisione: ADR-121. Leggi prima `constitution.md`, poi le regole qui sotto e **solo** la sezione del tuo task. I rilievi sono in `docs/accettazione/rilievi.md`, i report in `docs/accettazione/report/`. Dove il codice è diverso da come è descritto qui, fermati e chiedi.

**Che cosa è.** Tre sviluppatori, 5 ore ciascuno con l'AI. Si correggono i difetti trovati dalla simulazione (sintesi §4), in ordine di gravità, senza rompere il percorso della demo. Il codice è sbloccato solo per questi task.

**Le corse.**

| Corsia | Chi | Lavoro | Ore |
|---|---|---|---|
| 11 | Sviluppatore A | Blocco assoluto RL-025 e prova finale del percorso | 5 |
| 12 | Sviluppatore B | Corse tra operatori, guasti ordinati, limite delle azioni AI | 5 |
| 13 | Sviluppatore C | Immagini AI, foto della demo, dipendenze, intestazioni, input estremi, contrasto | 5 |

**Regole per tutti.**

- **Partenza.** `uv run python allinea.py 11` (o 12, o 13) stampa i tuoi task e il branch da aprire. I task della corsia si fanno in ordine.
- **Una PR per task**, piccola. Controlli di converge §1 verdi. La rivede un altro dei tre, entro 15 minuti; unisce chi ha i permessi di farlo.
- **Tempo.** Ogni task ha un tetto di ore. A tetto raggiunto: se è verde si apre la PR con ciò che c'è, altrimenti si scrive qui sotto il punto a cui si è arrivati e si passa al task dopo. Nessun task sfora prendendo tempo agli altri.
- **I test `xfail` sono il contratto.** Il task toglie il marcatore del suo rilievo e il test deve passare. Con `strict=False` il test passa anche senza correzione vera: va tolto il marcatore e il comando del test va rilanciato **50 volte**, tutte verdi.
- **La riga del registro resta.** In `rilievi.md` non si cancella nulla: la correzione si annota nella PR.
- **Costituzione.** I service non fanno `commit` (§2.6): la transazione la apre il job o il router. Gli stati cambiano solo nel modulo proprietario. Tra moduli solo `service`, e la funzione nuova si scrive in plan §6.
- **Un solo task crea una migrazione**: T5-111 (la 014). Se un altro task ne ha bisogno, chiede.
- **AI e Meta veri** solo a mano, solo in T5-131 e T5-112, con il tetto di spesa scritto nel task. Mai nei test.
- **Non è in questa corsia**: lockfile e separazione delle dipendenze (RL-002), rilascio e staging (C6), carico e allarmi (C9), privacy (C12), CI (C13), token cifrati e storage condiviso (C16).

**File che si incrociano.**

| File | Chi lo tocca | Regola |
|---|---|---|
| `backend/app/main.py` | T5-123 (gestore degli errori), T5-134 (middleware) | Ciascuno il suo blocco, poi `git merge origin/main` |
| `backend/app/moduli/campagne/service.py` | T5-121 (`campagna_bloccata`) | Solo la funzione nuova |
| `backend/app/core/config.py`, `.env.example` | T5-124 (variabili nuove) | Solo lui |
| `backend/requirements.txt` | T5-133 | Solo lui |

---

## T5-111 · Pubblicazione al massimo una volta (RL-025)

**Tetto**: 3,5 ore · **Corsia**: 11 · **Rilievo**: RL-025, blocco assoluto

**Il difetto.** `tick_pubblicazione` (`worker.py`) tiene tutto in una transazione. Il tentativo è scritto ma non confermato quando parte la chiamata al social: se il processo muore dopo la risposta di Meta, il tentativo sparisce e il tick dopo ripubblica.

**La decisione (ADR-121).** Si preferisce un post non uscito a un post uscito due volte. Dopo un esito sconosciuto **non si ripubblica mai da soli**.

**Come.**
1. Migrazione `014`: colonna `chiamata_il` (`timestamptz`, nullable) su `pubblicazione`.
2. Due fasi in `pubblicazione/service.py`, con una transazione per fase aperta da `worker.py` (i service non committano):
   - **Prima fase**: applica le scadenze, registra i tentativi dei post dovuti, torna gli id. Con commit.
   - **Seconda fase, per ogni tentativo e in una transazione sua**: scrive `chiamata_il`, fa commit, chiama il social, registra l'esito e fa commit. Se ti serve dividerla in due funzioni, dividila.
3. Un esito ricevuto, anche temporaneo, azzera `chiamata_il`: il retry di oggi resta com'è.
4. Un tentativo `in_corso` con `chiamata_il` valorizzato e nessun esito vuol dire che il processo è morto a metà: il post diventa `fallito`, l'errore dice «Esito della pubblicazione sconosciuto: controlla la pagina prima di riprogrammare», parte la notifica `post_fallito`. Il social **non** si chiama.
5. `pubblica_dovuti(db, adesso)` resta chiamabile: la usano molti test.
6. La riga «Congelato per l'MVP» dentro `_pubblica_post` riguarda le foto multiple: non si estende, si sposta intatta se serve.

**Test.**
- `invarianti/test_07_pubblicazione_idempotente.py`: via il marcatore. Il test simula il processo morto con un savepoint: va riscritto sulle due fasi, con il social chiamato una volta sola e il post `fallito`.
- Nuovi casi: errore temporaneo che riprova ancora; morte tra commit di `chiamata_il` e chiamata al social (non si pubblica, si segnala).
- `concorrenza/test_pubblicazione.py` e `tests/moduli/pubblicazione/` restano verdi.

**Limite noto, da scrivere nella PR.** Un timeout di Meta dopo che il post è uscito resta un errore temporaneo (`guasti/test_dopo_meta.py`): si chiude solo con una chiave di idempotenza che Meta non offre.

**Fatto quando**: RL-025 non è più `xfail`; `alembic downgrade -1` e `upgrade head` funzionano; suite verde.

## T5-112 · Prova finale del percorso

**Tetto**: 1,5 ore · **Corsia**: 11 · **Dipende da**: tutti gli altri task dello sprint

Il percorso di `converge.md` §4, punti 1–6 e 9, su `main` e da database vuoto, con AI vera e Meta sulla pagina di prova. Il tetto di spesa AI è **5 €**. In `docs/accettazione/report/T5-112-percorso.md`: esito per punto, costo letto dallo Storico AI, ciò che si è rotto. Nessun token, id o cookie nel report.

Se un punto è rotto: il task che l'ha rotto lo corregge o la sua PR si annulla con `git revert`. La demo vale più della correzione.

**Fatto quando**: report scritto e nessun punto rotto.

---

## T5-121 · Approva e respingi atomiche (RL-021, RL-022)

**Tetto**: 1,5 ore · **Corsia**: 12

**Il difetto.** `revisione.approva()` e `decisioni.respingi()` leggono la campagna senza bloccarla: due operatori passano insieme il controllo dello stato.

**Come.** In `campagne/service.py` la funzione `campagna_bloccata(db, id)`: come `campagna()`, con `with_for_update()`. Si scrive in plan §6. La usano `approva()` e `respingi()` al posto di `campagna()`. Il secondo operatore aspetta il primo, poi trova lo stato cambiato e prende il 409 che esiste già.

**Test.** `concorrenza/test_approvazione.py` e `test_interventi.py::test_approva_e_respingi_insieme`: via il marcatore, 50 ripetizioni verdi.

**Fatto quando**: i due test senza marcatore e 50 volte verdi; suite verde.

## T5-122 · Una foto una volta e interventi atomici (RL-023, RL-024)

**Tetto**: 1,5 ore · **Corsia**: 12 · **Dipende da**: T5-121

**Il difetto.** `interventi.cambia_foto()` legge le versioni correnti senza blocco, e due cambi portano la stessa foto su due post dello stesso canale. `accendi_intervento()` legge il post senza blocco, e due rigenerazioni partono insieme.

**Come.**
- `cambia_foto()`: prima di `foto_possibili()` blocca la campagna con `campagne.campagna_bloccata()`. Il secondo cambio trova la foto già usata e prende il 422 che esiste già.
- `accendi_intervento()`: legge il post con `with_for_update()`, così `puo_rigenerare()` vede l'intervento del primo.
- Ordine dei blocchi: sempre prima la campagna, poi il post. Altrimenti è un deadlock.

**Test.** `concorrenza/test_interventi.py::test_cambia_foto_insieme_sulla_stessa_foto` e `::test_rigenerazioni_insieme_col_limite_a_tre`: via il marcatore, 50 ripetizioni verdi.

**Fatto quando**: i due test senza marcatore e 50 volte verdi; suite verde.

## T5-123 · Guasti ordinati (RL-028, RL-029)

**Tetto**: 1 ora · **Corsia**: 12

**Come.**
- `main.py`: gestore per `sqlalchemy.exc.OperationalError` che risponde 503 con `{"detail": "Servizio momentaneamente non disponibile. Riprova tra poco."}` e `Retry-After`.
- Upload: `OSError` con `errno.ENOSPC` diventa un 503 con un messaggio chiaro, nel punto dove l'archivio scrive il file. Nessuna foto a metà nel database.

**Test.** `guasti/test_database_giu.py` e `guasti/test_disco_pieno.py`: via il marcatore.

**Fatto quando**: i due test senza marcatore; suite verde.

## T5-124 · Limite delle azioni AI (RL-018)

**Tetto**: 1 ora · **Corsia**: 12

**Come.** Rigenera testo, Rigenera immagine e invio della campagna hanno un limite per utente: `azioni_ai_limite` (default 20) in `azioni_ai_finestra_secondi` (default 60). Si riusa la tabella e la prenotazione di `core/limite_login.py`, con un tipo suo: `prenota()` oggi legge i limiti del login, va resa parametrica senza cambiare il comportamento del login. Oltre il limite 429 con `Retry-After` e «Troppe richieste. Riprova tra poco.».

Attenzione: il test fa 20 richieste e vuole almeno un 429, quindi nel test il limite si abbassa con `leggi_impostazioni`. Il default deve lasciare lavorare un operatore vero: una demo non deve mai incontrarlo.

**Test.** `test_limite_azioni_ai.py`: via il marcatore. I test del limite del login restano verdi.

**Fatto quando**: il test senza marcatore; variabili in `.env.example`; suite verde.

---

## T5-131 · Immagini AI che escono (RL-037)

**Tetto**: 1 ora · **Corsia**: 13 · **Il primo di tutti: la demo dipende da questo**

**Il difetto.** Con il modello in `.env` la tappa immagini si ferma: «L'AI non ha restituito nessuna immagine». La campagna resta `in_generazione`.

**Ipotesi da verificare, non un fatto.** `adapters/ai/litellm.py` usa `litellm.image_generation` e legge `data[0].b64_json`. `gemini-2.5-flash-image` via OpenRouter potrebbe rispondere come modello di chat, con l'immagine altrove.

**Come.** In ordine:
1. Stampa la forma della risposta in una prova a mano, senza salvarla né committarla.
2. Se basta un altro modello, cambia `AI_MODELLO_IMMAGINI` e il valore d'esempio in `.env.example`.
3. Altrimenti correggi solo `genera_immagine` e `_leggi_immagine`. La forma di `ImmagineAI` non cambia.

Prova a mano con `uv run python -m app.cli prova-ai --campagna <id>` su un database dedicato, mai `adflow`. Tetto di spesa: **2 €**, letto dallo Storico AI.

**Test.** Con risposte finte di `litellm` in `tests/adapters/`: nessuna chiamata vera.

**Fatto quando**: una campagna senza foto sufficienti arriva a `in_revisione` con l'immagine AI; `docs/accettazione/report/T4-107-ai-vera.md` ha il nuovo esito in fondo, con il costo.

## T5-132 · Foto della demo e passi non scritti (RL-012, RL-013, RL-014)

**Tetto**: 0,5 ore · **Corsia**: 13

**Come.** Nel README del backend: i comandi per creare `adflow` e `adflow_test`; il nome `adflow_test` e la porta 5432 come vincolo; dove sta la cartella delle foto della demo e come si usa `python -m app.cli demo --foto CARTELLA`. La cartella va copiata in un posto condiviso dal team, **non in git**: chi la ha lo dice nella PR. Se nessuno la trova, fermati e dillo subito: il percorso della demo dipende da lei.

**Fatto quando**: un clone nuovo arriva alla demo seguendo il README.

## T5-133 · Dipendenze (RL-001, RL-004, RL-005)

**Tetto**: 1 ora · **Corsia**: 13

**Come.** In `backend/requirements.txt`: `pillow` da 12.3.0 a 13.0.0 o superiore; `httpx` dichiarato con la versione già installata; `filelock` alla prima versione senza vulnerabilità. È un salto di versione maggiore di una libreria che apre le foto: controlla le note di rilascio e prova a mano un upload e una sistemazione.

**Test.** Suite verde, e `uvx pip-audit -r backend/requirements.txt` senza risultati alti o critici sul runtime. L'esito va nella PR, con nome, motivo e licenza.

**Fatto quando**: pip-audit pulito sul runtime, oppure l'elenco di ciò che resta con il motivo; suite verde.

## T5-134 · Intestazioni di sicurezza (RL-015)

**Tetto**: 1 ora · **Corsia**: 13

**Come.** Un middleware nuovo in `core/intestazioni_sicurezza.py`, aggiunto in `main.py`, sulle risposte di `/api`: `Content-Security-Policy: default-src 'none'; frame-ancestors 'none'`, `Strict-Transport-Security: max-age=31536000`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`, `X-Frame-Options: DENY`. Solo su `/api`: una CSP così rompe `/docs`. Le foto si devono ancora vedere nel frontend: controllalo nel browser. Stesse intestazioni nell'esempio Nginx di `docs/sicurezza-accesso.md`.

**Test.** `test_intestazioni.py`: via il marcatore.

**Fatto quando**: il test senza marcatore; frontend provato a mano con le foto visibili; suite verde.

## T5-135 · Input estremi (RL-026)

**Tetto**: 1 ora · **Corsia**: 13

**Il difetto.** Id oltre `int4`, un `tipo` non ammesso nello storico AI e il byte NUL in un nome arrivano al database e fanno 500.

**Come.** Un tipo condiviso in `core/` per gli id di percorso (`Annotated[int, Path(ge=1, le=2147483647)]`) nei router, un `Literal` o un controllo su `tipo` nello storico AI, il rifiuto del NUL con un validatore comune negli schemi di testo. Risposta 422 con la frase in italiano. Non serve toccare i router congelati di `archivio`: se il test lo chiede, chiedi.

**Test.** `test_input_estremi.py` e il caso del NUL in `test_prompt_injection.py`: via il marcatore.

**Fatto quando**: i test senza marcatore; suite verde.

## T5-136 · Contrasto (RL-035)

**Tetto**: 0,5 ore · **Corsia**: 13

**Come.** Le quattro violazioni serie di axe di `T4-106-frontend.md` §2: contrasto su Ingresso, Calendario ed elenco artigiani, e il link riconoscibile solo dal colore. Si toccano i valori in `tema.ts` e `index.css`, non la struttura delle pagine. Le scelte di `brief-interfaccia.md` §4 restano: si scuriscono i toni, non si cambia la palette.

**Test.** `npm run test:e2e` con zero violazioni serie, `npm run lint`, `npm run build`.

**Fatto quando**: axe senza violazioni serie sulle tre pagine; se non c'è tempo, è il primo task da saltare.
