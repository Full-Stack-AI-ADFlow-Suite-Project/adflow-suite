# T4-104 · Invarianti e proprietà

Copre §4.3 e la parte «qualità dei test» di §6 di `accettazione-post-mvp.md`:
gli 11 invarianti della costituzione attaccati uno per uno, le macchine a stati
con `hypothesis`, il fuzzing dallo schema con `schemathesis` e le mutazioni con
`mutmut`. Nessuna correzione: solo prove e rilievi.

## 1. Gli 11 invarianti, uno per file (`tests/accettazione/invarianti/`)

| Invariante | Attacco di §4.3 | Esito |
|---|---|---|
| §1.1 solo post approvati | approva con un post `da_rivedere`; tick su un post non approvato; doppia approvazione in parallelo (→ T4-103) | **verde**: 409 e nessun post approvato; il tick non chiama il social |
| §1.2 niente si cancella | le 4 DELETE solo su foto/gruppi, mai su foto usate; nessun DELETE su tabelle con storico | **verde**: solo 4 rotte DELETE nello schema; foto usata → 409; righe intatte |
| §1.3 originale intatto | hash prima/dopo sistemazione, cambio foto, pubblicazione | **verde**: hash identico in tutti i passaggi |
| §1.4 snapshot del profilo | profilo cambiato dopo l'invio poi Rigenera testo | **verde**: la rigenerazione usa ancora il nome vecchio; snapshot invariato |
| §1.5 margine e niente AI | intervento a 15:01 e 14:59; campagna sospesa; Rigenera testo/immagine dopo l'approvazione | **verde**: 15:01 passa, 14:59 → 409; sospesa passa; dopo l'approvazione 409 e **zero** chiamate AI |
| §1.6 modifica con blocco | parola vietata, prezzo fuori dai dati, testo di partenza ostile | **verde**: 422 e nessuna versione; l'ostile non pubblica nulla |
| §1.7 pubblicazione idempotente | ripubblicazione dopo un `ok`; processo morto dopo la risposta di Meta (D-07); due worker (→ T4-103) | **rosso su D-07**: RL-025 (doppia pubblicazione); il resto verde |
| §1.8 stati solo dei proprietari | `ast` su tutte le assegnazioni a `.stato` in `app/` | **verde**: solo `campagne.cambia_stato`, `contenuti.service` e lo stato del tentativo di pubblicazione |
| §1.9 una foto una volta | stessa foto su due post dello stesso canale (sequenza) | **verde in sequenza**, rosso in parallelo (RL-023, T4-103) |
| §1.10 post chiesti per canale | campagna senza foto, 2 canali, generazione | **verde**: 4 post per canale, tutti con immagine AI |
| §1.11 numero dei post | modifica, rigenera, sposta, respingi, togli canale | **verde**: nessuna azione toglie righe; il canale tolto scarta i suoi post (restano, §1.2) |

Dettaglio del difetto §1.7 (RL-025): `_registra_tentativo` crea la riga
`pubblicazione` **nella stessa transazione** del commit. Se il processo muore
dopo che il social ha risposto e prima del commit, la riga sparisce con il
rollback e il tick successivo ripubblica: nel test il social finto riceve
**due** chiamate per lo stesso post. È il caso D-07, e nella §8 è un blocco
assoluto (lo stesso post pubblicato due volte su Meta). Correzione proposta,
non applicata: committare il tentativo in una transazione separata prima della
chiamata al social, come chiede la costituzione §1.7.

## 2. Macchine a stati (`tests/accettazione/proprieta/`)

Due `RuleBasedStateMachine` con gli invarianti come `@invariant`:

- **campagna**: crea, approva, respingi, sospendi, riattiva. Invarianti: stato
  tra quelli ammessi; una campagna attiva non ha post `da_approvare`; una
  respinta ha tutti i post `scartato`; il numero dei post non cala.
- **post**: modifica (testo casuale), rigenera, cambia foto, sposta. Invarianti:
  stato ammesso; le versioni non calano mai (§1.2); nessuna versione vuota
  (§1.6); numeri di versione progressivi.

Le macchine si saltano se `hypothesis` non è installato (sta in
`requirements-accettazione.txt`, MPL-2.0, e non in `requirements.txt`).

**Corsa lunga.** `hypothesis` con 10 000 sequenze è stato lanciato in **10
corse da 1 000 sequenze per macchina**, ognuna in un processo nuovo con il
database ripulito. Motivo documentato: una sola corsa da 10 000 esempi resta
in un'unica transazione lunga e PostgreSQL esaurisce i lock condivisi
(`OutOfMemory: out of shared memory`), poi tutto il resto della corsa va in
errore — è un limite dello strumento in questa configurazione, non del codice.
Risultato delle 10 corse: **nessun controesempio** (vedi
`T4-104-hypothesis-lungo.txt`).

Comando:

```bash
# da backend/, con le dipendenze dei test di accettazione
ACCETTAZIONE_SEQUENZE=1000 uv run --with-requirements requirements-accettazione.txt pytest tests/accettazione/proprieta -q
```

## 3. schemathesis: il fuzzing dallo schema (RL-026, RL-027)

`uvx schemathesis run http://127.0.0.1:8903/openapi.json --header "Cookie:
adflow_sessione=<token>" --exclude-path /api/auth/logout --max-examples 15
--workers 1`, su un server in locale con database dedicato
`adflow_accettazione` (poi rimosso) e provider finti, con i due ruoli
(operatore e artigiano, cookie di sessione veri).

Esiti:
- **nessuna violazione del contratto sui tipi nei corpi validi**;
- **39 risposte 500** (RL-026), in due classi riproducibili a mano:
  - **id oltre `int4`**: `/api/foto/99999999999999/file`,
    `/api/campagne/99999999999999/calendario`,
    `/api/campagne/143479337444/riprova` → `InternalError` del database e 500.
    Atteso: 404 (l'id non esiste);
  - **`GET /api/storico-ai?tipo=<valore non ammesso>`** → `InternalError` sul
    confronto con la colonna enum; atteso 422;
- **risposte fuori schema (RL-027)**: il 422 di business
  `{"detail": "Dati non validi."}` (una stringa) non rispetta lo schema
  generato da FastAPI (`detail` è un array di `ValidationError`), e i codici
  401/403/404/409 del prodotto non sono dichiarati nelle risposte: un client
  generato dai tipi non conosce gli errori. Schemathesis lo segnala come
  ST103/ST108;
- l'avviso «Authentication failed: N operations returned only 401/403» è un
  **falso allarme dello strumento**: le operazioni restituiscono 401/403 perché
  il ruolo non le ammette (matrice T4-102), non perché la sessione sia scaduta;
  durante la corsa le letture autenticate rispondono 2xx e `/api/auth/me` dà
  200. La rotta `/api/auth/logout` va esclusa, perché il fuzzing la chiama e
  chiude davvero la sessione.

I due difetti (RL-026) restano documentati dai test in
`tests/accettazione/test_input_estremi.py`, `xfail(strict=True)`.

## 4. mutmut: le mutazioni (registro dei mutanti)

Mutazioni sui quattro file indicati dalla §6: `contenuti/domain.py`,
`campagne/domain.py`, `contenuti/validatore.py`, `campagne/foto_pubblica.py`.
Configurazione in `backend/setup.cfg` (`[mutmut]`), con `--max-children 1`
obbligatorio (le prove condividono `adflow_test`: il parallelismo renderebbe
inaffidabili i risultati) e la selezione dei test mirata (validatore, piano,
foto pubblica, API della bozza).

Comando: da `backend/`, `uv run --with mutmut mutmut run --max-children 1`.

**Risultato: 396 mutanti, 323 uccisi, 56 sopravvissuti, 17 «senza test/altro».**
Tasso di uccisione 81,6 %. I sopravvissuti, per funzione:

| File · funzione | Sopravvissuti | Analisi |
|---|---|---|
| `campagne/foto_pubblica.py · genera_url_pubblico` | 17 | i test della selezione non chiamano mai la funzione **senza** l'argomento `canale` (mutare il valore predefinito non fa fallire nulla) e non verificano tutte le varianti di `url_base`; comportamento corretto, copertura dei test incompleta |
| `campagne/foto_pubblica.py · verifica_firma` | 16 | variazione dei limiti (`foto_id <= 0` → `<= 1`, formati di firma) non coperta: nessun test usa l'id 1 con una firma valida né le varianti di formato intermedie |
| `campagne/foto_pubblica.py · _segreto_firma`, `calcola_mac` | 6 | rami di ripiego e lunghezze del MAC non esercitati |
| `contenuti/validatore.py · _importi` | 7 | le varianti dei pattern degli importi sono coperte solo in parte (i casi con `€` prima/dopo e con spazi) |
| `contenuti/validatore.py · termini_da_non_dire` | 6 | le formule («non parlare di…», «evita di…») non sono tutte provate |
| `contenuti/validatore.py · _schema`, `_testi` | 4 | rami di normalizzazione dei testi |

Lettura dei sopravvissuti:

- **Nessuno è un errore di comportamento**: il codice è corretto nei casi
  provati dal resto della suite; i sopravvissuti sono **buchi di copertura
  della selezione mirata** (funzioni coperte solo indirettamente) e, in minima
  parte, **mutanti equivalenti** (cambiamenti che non alterano l'uscita).
- Un caso che merita un test (ed è un rilievo di qualità, RL-030): la
  `verifica_firma` non viene mai provata con `foto_id = 1`, e
  `genera_url_pubblico` mai senza `canale`: sono proprio i due mutanti
  sopravvissuti più semplici da uccidere con due righe di test.
- Le mutazioni su `domain.py` (contenuti e campagne) sono state uccise tutte:
  i test funzionali dei due moduli le tengono.

Limite dichiarato: la selezione mirata (4 file di test) non è la suite intera;
con la suite completa alcuni dei 56 sopravvissuti cadrebbero. La corsa
completa richiede ore e non è stata fatta in questa sessione.

## 5. Rilievi aggiunti

- **RL-025** (Alta, blocco assoluto): doppia pubblicazione dopo un processo
  morto dopo la risposta di Meta (D-07).
- **RL-026** (Media): input estremi → 500 invece di 404/422.
- **RL-027** (Bassa): contratto OpenAPI incompleto e 422 di business fuori
  schema.
- **RL-030** (Bassa): mutanti sopravvissuti in `foto_pubblica` (default di
  `genera_url_pubblico`, id 1 in `verifica_firma`) e nei pattern del
  `validatore`: buchi di copertura dei test, da chiudere con due casi in più.
