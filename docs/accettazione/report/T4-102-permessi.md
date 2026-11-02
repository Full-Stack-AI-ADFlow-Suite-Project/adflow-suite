# T4-102 · Permessi e superficie HTTP

Copre §5.2 e §5.4 punti 1–5 di `accettazione-post-mvp.md` e la costituzione §3.
Test in `backend/tests/accettazione/`: `permessi/test_matrice.py` più i sei file
di attacco. Comando: da `backend/`, `uv run pytest tests/accettazione -q`.

Esito: **80 passed, 3 xfailed** (i tre xfail sono RL-015, RL-018 e il test di
T4-101 che resta nel conteggio). Le 57 operazioni × 5 ruoli della matrice sono
**tutte conformi** all'atteso di costituzione e spec: nessun blocco assoluto su
questa superficie.

## 1. Matrice dei permessi (57 operazioni × 5 ruoli)

L'atteso viene da costituzione §3 («401 senza sessione, 403 ruolo, 404 per
risorse di un altro artigiano; l'admin passa dove passa l'operatore») e da
`spec.md` (R-29, R-45…R-50, §4), **non** dal codice; il file
`tests/accettazione/permessi/matrice.py` è la matrice leggibile, con una riga
per ogni operazione e il suo perché. `test_matrice.py` legge `app.openapi()`:
se un'operazione non ha la sua riga il test fallisce, e se la matrice ha righe
che lo schema non ha più, pure.

Ruoli: **an** = anonimo, **aA** = artigiano A (proprietario delle risorse),
**aB** = artigiano B (l'altra bottega), **op** = operatore, **ad** = admin.
`ammesso` = 2xx/409/422 (il permesso c'è; 409 e 422 sono stato o corpo della
sonda, non un rifiuto). Ogni cella è stata provata in isolamento, con un mondo
fresco (due botteghe con profilo, campagna in revisione con post e foto,
archivio, chiamata AI).

| Operazione | an | aA | aB | op | ad |
|---|---|---|---|---|---|
| GET /api/health | 200 | 200 | 200 | 200 | 200 |
| GET /api/consorzio | 200 | 200 | 200 | 200 | 200 |
| GET /api/foto/{id}/pubblica (firma valida) | 200 | 200 | 200 | 200 | 200 |
| POST /api/auth/login | 200 | 200 | 200 | 200 | 200 |
| POST /api/auth/logout | 204 | 204 | 204 | 204 | 204 |
| GET /api/auth/me | 401 | 200 | 200 | 200 | 200 |
| GET /api/campagne | 401 | 200 | 200 | 200 | 200 |
| POST /api/campagne | 401 | 422 | 422 | 403 | 403 |
| GET /api/campagne/{id} | 401 | 200 | 404 | 200 | 200 |
| PATCH /api/campagne/{id} | 401 | 409 | 404 | 403 | 403 |
| GET /api/campagne/{id}/calendario | 401 | 409 | 404 | 409 | 409 |
| POST /api/campagne/{id}/gruppi | 401 | 409 | 404 | 403 | 403 |
| PUT /api/campagne/{id}/gruppi/{gruppo_id} | 401 | 409 | 404 | 403 | 403 |
| DELETE /api/campagne/{id}/gruppi/{gruppo_id} | 401 | 409 | 404 | 403 | 403 |
| POST /api/campagne/{id}/foto | 401 | 409 | 404 | 403 | 403 |
| DELETE /api/foto/{id} | 401 | 409 | 404 | 403 | 403 |
| POST /api/campagne/{id}/invia | 401 | 409 | 404 | 403 | 403 |
| GET /api/foto/{id}/file | 401 | 200 | 404 | 200 | 200 |
| POST /api/campagne/{id}/richiesta | 401 | 403 | 403 | 422 | 422 |
| POST /api/campagne/{id}/richiesta/foto | 401 | 409 | 404 | 403 | 403 |
| POST /api/campagne/{id}/richiesta/invia | 401 | 409 | 404 | 403 | 403 |
| GET /api/profilo | 401 | 200 | 200 | 403 | 403 |
| PUT /api/profilo | 401 | 422 | 422 | 403 | 403 |
| GET /api/canali | 401 | 200 | 200 | 403 | 403 |
| GET /api/archivio (congelata) | 401 | 200 | 200 | 403 | 403 |
| POST /api/archivio/gruppi (congelata) | 401 | 422 | 422 | 403 | 403 |
| POST /api/archivio/foto (congelata) | 401 | 422 | 404 | 403 | 403 |
| DELETE /api/archivio/foto/{id} (congelata) | 401 | 204 | 404 | 403 | 403 |
| DELETE /api/archivio/gruppi/{id} (congelata) | 401 | 204 | 404 | 403 | 403 |
| GET /api/archivio-foto | 401 | 200 | 200 | 422 | 422 |
| GET /api/calendario | 401 | 200 | 200 | 200 | 200 |
| GET /api/da-approvare | 401 | 403 | 403 | 200 | 200 |
| GET /api/artigiani | 401 | 403 | 403 | 200 | 200 |
| POST /api/artigiani | 401 | 403 | 403 | 422 | 422 |
| GET /api/artigiani/{utente_id} | 401 | 403 | 403 | 200 | 200 |
| GET /api/campagne/{campagna_id}/post | 401 | 403 | 403 | 200 | 200 |
| POST /api/campagne/{campagna_id}/approva | 401 | 403 | 403 | 200 | 200 |
| POST /api/campagne/{campagna_id}/respingi | 401 | 403 | 403 | 422 | 422 |
| POST /api/campagne/{campagna_id}/sospendi | 401 | 403 | 403 | 200 | 200 |
| POST /api/campagne/{campagna_id}/riattiva | 401 | 403 | 403 | 409 | 409 |
| POST /api/campagne/{campagna_id}/annulla | 401 | 403 | 403 | 409 | 409 |
| POST /api/campagne/{campagna_id}/nota | 401 | 403 | 403 | 422 | 422 |
| POST /api/campagne/{campagna_id}/togli-canale | 401 | 403 | 403 | 422 | 422 |
| POST /api/campagne/{id}/riprova | 401 | 403 | 403 | 409 | 409 |
| POST /api/post/{post_id}/modifica | 401 | 403 | 403 | 422 | 422 |
| POST /api/post/{post_id}/controllato | 401 | 403 | 403 | 422 | 422 |
| POST /api/post/{post_id}/rigenera | 401 | 403 | 403 | 422 | 422 |
| POST /api/post/{post_id}/rigenera-immagine | 401 | 403 | 403 | 409 | 409 |
| POST /api/post/{post_id}/riprogramma | 401 | 403 | 403 | 422 | 422 |
| POST /api/post/{post_id}/sposta | 401 | 403 | 403 | 422 | 422 |
| POST /api/post/{post_id}/annulla | 401 | 403 | 403 | 422 | 422 |
| POST /api/post/{post_id}/cambia-foto | 401 | 403 | 403 | 422 | 422 |
| GET /api/post/{post_id}/foto-possibili | 401 | 403 | 403 | 200 | 200 |
| GET /api/storico-ai | 401 | 403 | 403 | 200 | 200 |
| GET /api/storico-ai/numeri | 401 | 403 | 403 | 200 | 200 |
| GET /api/storico-ai/{id} | 401 | 403 | 403 | 200 | 200 |
| POST /api/storico-ai/{id}/voto | 401 | 403 | 403 | 422 | 422 |

**Nessuna differenza dall'atteso.** Il risultato più importante: su tutte le
operazioni con un id, l'artigiano B riceve **404** e mai i dati di A; l'admin
si comporta come l'operatore ovunque e come l'artigiano mai. Il test
`test_la_cella_della_matrice` è verde per tutte e 57 le operazioni.

Nota (scelta consapevole): `POST /api/auth/logout` risponde 204 anche senza
sessione (no-op che cancella il cookie e non rivela nulla); la costituzione
chiede 401 per le richieste che *controllano* i permessi, e il logout non ne
controlla. Il test lo dichiara nella matrice.

## 2. Intestazioni di sicurezza (R-01 → RL-015, confermato)

`test_intestazioni.py`: su `/api/health`, `/api/consorzio` e `/api/campagne`
**mancano tutte e cinque** le intestazioni attese — CSP, HSTS,
`X-Content-Type-Options`, `Referrer-Policy`, `X-Frame-Options` — tranne
`X-Request-ID`, che c'è. L'unica difesa presente è `nosniff` sui file delle
foto (verde, con il suo file vero su disco). Il test dell'atteso è in
`xfail(strict=True)` con RL-015.

## 3. Origine delle richieste (R-02 → RL-016, smentito)

`test_origine.py` avvia un **server Uvicorn vero in produzione**
(`AMBIENTE=produzione`, con `ProtezioneCSRF` attiva) e manda richieste TCP:
- `Origin: https://attaccante.example.test` su `POST /api/campagne` → **403**
  con «Origine della richiesta non consentita.»;
- sottodominio dello stesso sito (`https://malevolo.app.example.test`) → **403**;
- nessuna `Origin` → **403** (i client non-browser devono dichiararla);
- `Origin` uguale a `http://127.0.0.1:<porta>` → passa il controllo e arriva
  l'**401** della sessione mancante;
- letture (`GET /api/health`) con origine esterna → 200, non toccate.

L'ipotesi R-02 («nessun controllo di Origin o Sec-Fetch-Site; protegge solo
SameSite=Lax») **non regge in produzione**: dal T3-09 (`ProtezioneCSRF`)
esiste la seconda difesa, per tutti i metodi POST/PUT/PATCH/DELETE. Resta vero
che in **sviluppo** (`AMBIENTE=sviluppo`) il controllo è disattivato e che
`Sec-Fetch-Site` non viene usato: sono note, non difetti. Rilievo RL-016,
esito `smentito`.

## 4. Caricamenti ostili (§5.4 punto 4 → tutti verdi)

`test_upload_ostili.py`:
- PNG **1 × 100 000** → 422 (il lato corto si controlla al caricamento);
- file **troncato** → 422;
- **HEIC rinominato .jpg** → 422 (tipo reale dai magic bytes, non l'estensione);
- JPEG valido **oltre i 10 MB** → 422 sul peso;

e due casi che entrano, documentati:
- **poliglotta JPEG+HTML** (JPEG valido con `<script>` in coda) → 201: è una
  foto vera nei limiti, il **nome lo genera il server** (il nome originale con
  `.html.jpg` non arriva mai al disco) e il file esce come `image/jpeg` con
  `nosniff`, quindi non è interpretabile come pagina;
- **metadati oltre 1 MB con GPS** (18 segmenti commento + EXIF GPS) → 201:
  R-13 non pone limiti all'EXIF. La copia sistemata servita dall'indirizzo
  pubblico **non ha nessun metadato né GPS**; l'originale resta intatto
  (costituzione §1.3).

Nessun difetto: i controlli di costituzione §3 (tipo reale, peso, dimensioni,
nome generato) sono tutti presenti.

## 5. Indirizzo pubblico delle foto (§5.4 punto 5 → tutti verdi)

`test_foto_pubblica_firma.py`: firma **scaduta**, **alterata**, **di un'altra
foto** (e l'id cambiato con la firma di A), **tagliata o vuota**, **id
inesistente**, **canale sconosciuto** → sempre **404**, senza distinguere il
motivo. Il test misura 10 richieste per variante e controlla che i tempi dei
404 restino dello stesso ordine di grandezza (nessun controllo è 10 volte più
lento degli altri): la proprietà è verificata, i valori puntuali non sono
conservati nel report perché il test li ricava a ogni esecuzione.

## 6. Letture trasversali (R-17 → RL-020, smentito)

`test_bola_nuovi_endpoint.py`, con due botteghe complete:
- `GET /api/post/{post_A}/foto-possibili` (operatore) non contiene **nessuna**
  foto di B;
- `POST /api/post/{post_A}/cambia-foto` con una foto di B → **422** (fuori elenco);
- `GET /api/archivio-foto?artigiano=A` chiamato **da B** → 200 ma solo le foto
  di B (il parametro è ignorato per l'artigiano);
- `GET /api/campagne?artigiano=A` chiamato **da B** → solo le campagne di B;
- `GET /api/calendario` di B → nessun post di A;
- `GET /api/storico-ai` e `GET /api/storico-ai/{id}` da artigiano → 403.

R-17 («va provato che non escano mai foto di un'altra bottega») **non trova
falla**: tutti gli endpoint della corsia 9 rispettano il confine della bottega.
Rilievo RL-020, esito `smentito`.

## 7. Limite delle azioni AI (R-15 → RL-018, confermato)

`test_limite_azioni_ai.py`: con l'operatore autenticato, 20 rigenerazioni di
testo in pochi secondi (20 post diversi, ognuno la prima volta) passano
**tutte** (200, nessun 429). Il ciclo per post di R-03 (max 3) non è un limite
di frequenza e il limite esistente (`core/limite_login.py`) vale solo per il
login. Rilievo RL-018, test in `xfail(strict=True)`.

## 8. Storico AI (R-16 → RL-019, confermato)

`chiamata_ai.richiesta` (JSONB) e `chiamata_ai.risposta` (Text) conservano
prompt e risposte, profilo della bottega compreso (migrazione 013); non esiste
nel codice nessuna regola di conservazione o pulizia della tabella, che cresce
a ogni chiamata. Visibile agli operatori, come da R-50. È una lacuna di
conservazione (GDPR, §5.5) più che un difetto di codice: RL-019, confermato.

## 9. Rotte congelate (R-12 → RL-017, confermato)

Le cinque operazioni `/api/archivio…` (2 GET/POST di elenco e creazione,
2 DELETE, più la lettura) sono montate e raggiungibili dagli artigiani: la
matrice le prova senza modificarle (D-06). Un artigiano **non** può toccare
l'archivio di un altro (404), quindi la superficie congelata non apre falla;
resta il fatto che codice congelato è esposto a internet: RL-017, `roadmap`.

## Conclusioni

- Matrice dei permessi esaustiva e **tutta conforme**: nessun blocco assoluto
  (nessun artigiano vede o modifica dati di un altro).
- R-01 confermato (intestazioni di sicurezza assenti), R-02 smentito (il
  controllo di Origin esiste in produzione), R-12 confermato (rotte congelate
  montate), R-15 confermato (nessun limite sulle azioni AI), R-16 confermato
  (storico senza conservazione), R-17 smentito (nessun BOLA sugli endpoint
  della corsia 9).
- Rilievi aggiunti al registro: RL-015, RL-016, RL-017, RL-018, RL-019, RL-020.
