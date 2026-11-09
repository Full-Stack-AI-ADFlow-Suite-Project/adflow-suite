# Corsia del ritocco · piano e task

Aperta il 9 novembre 2026. È il piano per scrivere il codice delle decisioni prese dal 7 al 9 novembre: il perché, le misure e gli schemi sono in [`ritocco-locale-supportato-ai.md`](ritocco-locale-supportato-ai.md) (citata qui come **nota**, con il numero di sezione). Dove nota e piano non tornano, vale il piano; dove il piano e il codice non tornano, vale il codice, e si segnala.

Le sigle `RT-` non sono lette da `allinea.py` (come le `P-` della corsia della presentazione) e non vanno confuse con le regole `R-` dello spec.

Rivisto il 9 novembre 2026 dopo il confronto con il codice: archivio dei file derivati (RT-06), Playwright già presente (RT-10), percorsi dei file, livello `revisione/interventi.py` (RT-28), dipendenze di RT-26 e RT-33, PR per ondata.

---

## 1. Regole della corsia

1. **Branch.** `feature/ritocco-foto` è la base della corsia (la punta dei documenti, PR #190); ogni ondata (§5) lavora su un suo branch `ritocco/ondata-a`, `ritocco/ondata-b`… ognuno preso dalla punta del precedente. Ogni task è uno o più commit, in italiano all'imperativo (`feat:`, `fix:`, `test:`, `docs:`, `refactor:`, `chore:`).
2. **PR a catena, una per ondata.** A fine ondata si spinge il branch e si apre una PR con base il branch dell'ondata precedente (la A ha base `feature/ritocco-foto`), così i workflow girano a ogni ondata (partono su ogni `pull_request`, qualunque sia la base). **Le PR intermedie non si uniscono da sole.** La PR verso `main` si apre solo a corsia completa (decisione del 9 novembre), come bozza, dal branch dell'ultima ondata.
3. **Ogni task chiude verde.** Alla fine di ogni task: da `backend/` `uv run alembic upgrade head`, `uv run pytest`, `uv run black --check .`; da `frontend/` `npm run lint`, `npm run build` e, da RT-09, `npm test`; da RT-10 anche i test end-to-end.
4. **Il codice congelato si tocca** (decisione del 9 novembre), ma solo dove il task lo dice e in modo chirurgico: il commento "Congelato per l'MVP, ADR-114" si aggiorna in quel punto e la modifica si elenca nella PR.
5. **Nessuna chiamata reale ad AI, Meta o email nei test.** L'AI vera si usa solo in RT-32, a mano.
6. **Le foto reali non entrano nel repository** (README della PR #189). I test usano immagini sintetiche generate in codice.
7. **I confini dei moduli restano** (`tests/test_confini.py`): un modulo importa solo `service` o `schemas` dei moduli che vengono prima (accesso → notifiche → artigiani → campagne → contenuti → revisione → pubblicazione); gli adapter non importano mai i moduli.
8. **Da scrivere nella PR** (AGENTS.md): dipendenze nuove (backend e frontend, con motivo e licenza), migrazioni Alembic, `contenuti/domain.py`, codice congelato toccato, CI cambiata, **adapter dell'archivio esteso** (RT-06) e **cambio di uscita di tutte le foto** da RT-04 (fine dell'autocontrasto) fino a RT-25.

## 2. Dove va il codice

| Cosa | Dove | Perché lì |
|---|---|---|
| Colore, catalogo, misure, candidati, esecutore, diagnosi, varianti, render | `backend/app/moduli/campagne/` (file nuovi: `colore.py`, `ritocco_catalogo.py`, `preanalisi.py`, `esecutore.py`, `diagnosi.py`, `varianti.py`), esposti da `campagne/service.py` | `campagne` possiede `Foto` e l'archivio; viene prima di `contenuti`, `revisione` e `pubblicazione`, che lo possono chiamare |
| Copia per l'AI | preparata da `campagne`, passata all'adapter come byte in `FotoAI` | l'adapter non importa i moduli: così non decodifica più e non serve duplicare il colore |
| Schema e prompt | `adapters/ai/schemi.py`, `adapters/ai/prompts/analisi_v4.md`, `adapters/ai/litellm.py`, `adapters/ai/finto.py` | come oggi; i codici sono copie confrontate da un test con il catalogo |
| File derivati (render) | `adapters/archivio/` (`base.py`, `disco.py`, `finto.py`): metodi nuovi per i derivati, in `derivate/` sotto la radice | l'adapter di oggi rifiuta i separatori di percorso (`valida_nome_file`) e sceglie lui il nome in `salva()`: un percorso `derivate/<foto>/<chiave>.jpg` non si può scrivere senza estenderlo |
| Scelta dell'operatore e render approvato | `versione_post_foto.ritocco`, `versione_post_foto.render` (modelli di `contenuti`) | viaggiano con la versione del post (nota 8.6 A) |
| Intervento `RITOCCA_FOTO` | `contenuti/domain.py`, `contenuti/interventi.py`, `revisione/interventi.py` (livello intermedio, come `cambia_foto`), rotta in `revisione/router.py` | come `CAMBIA_FOTO`: rotta → `revisione.interventi` → `contenuti` |
| Render all'approvazione | `revisione/service.py::approva` → `contenuti/service.py` → `campagne/service.py` | l'ordine dei moduli lo permette |
| Pubblicazione dal file | `pubblicazione/service.py` (blocco congelato), `campagne/service.py::url_foto_pubblica`, `campagne/foto_pubblica.py` (`calcola_mac`, `componi_firma`, `verifica_firma`, `genera_url_pubblico`), `campagne/router.py` (`/foto/{id}/pubblica`, non congelata) | l'URL firmato porta la chiave del render: `campagne` serve il file senza leggere `contenuti` |
| Nessuna modifica a `core/` | – | non serve |

## 3. Strategia dei test

| Livello | Strumento | Che cosa prova |
|---|---|---|
| Unità, immagini | pytest + numpy, immagini sintetiche (`tests/immagini.py`, RT-01) | colore, misure, candidati, geometria, finestra, luce, privacy: **asserzioni numeriche** (ΔE, medie, errore degli angoli in % del lato), mai i byte di un JPEG (cambiano con la versione dell'encoder) |
| Proprietà | hypothesis (già in `requirements-accettazione.txt`; da RT-01 **anche in CI**) | finestra sempre dentro la foto e nell'intervallo 4:5–1,91:1; soggetto e testo mai tagliati; l'esecutore non solleva eccezioni con comandi validi; L2 non solleva eccezioni con risposte AI casuali |
| Contratto | pytest | codici dello schema = catalogo; ogni codice compare nel prompt; prompt statico (cache); il finto dà risposte valide |
| Integrazione | pytest con DB di test, AI finta, archivio finto, Meta finto | generazione → varianti salvate; intervento → versione; approvazione → render; pubblicazione → stessi byte del render approvato |
| Accettazione | `tests/accettazione/` (`invarianti/test_03_originale_intatto.py`, `invarianti/test_02_niente_si_cancella.py`, `invarianti/test_07_pubblicazione_idempotente.py`, `test_bola_nuovi_endpoint.py`, `test_foto_pubblica_firma.py`) | originale intatto (§1.3), niente si cancella (§1.2), BOLA sulle rotte nuove, firma dell'URL pubblico |
| Componenti | Vitest + Testing Library + MSW (RT-09) | card con tre varianti, stati spenti, privacy, riepilogo in Approva, chiamate API |
| End-to-end | Playwright, **già presente** in `frontend/e2e/` (T4-106, `percorso-demo.spec.ts`, DB `adflow_e2e`); RT-10 lo porta in CI e vi aggiunge il percorso del ritocco | il percorso dell'operatore nel browser vero, fino alla pubblicazione finta |
| Prova reale | `cli.py prova-ritocco` (RT-32), a mano, fuori da pytest | token, cache, costo, precisione su foto reali |

Regressione delle foto buone: un insieme sintetico di "foto buone" (esposizione e colori normali, nessun difetto) deve uscire dalla Standard con ΔE medio < 1 e lo stesso rapporto. Vale come test fisso di ogni task che tocca l'esecutore.

## 4. Scelte di default (approvate il 9 novembre)

| # | Scelta | Motivo |
|---|---|---|
| D1 | L'artigiano, nei post approvati, vede la foto che esce (il render), non l'originale | coerenza con l'operatore |
| D2 | Il render di una versione approvata o pubblicata non si cancella mai; le anteprime non approvate stanno in una cache su disco con potatura | costituzione §1.2 "niente si cancella" |
| D3 | Il parametro `proporzione` di `sistema_foto_buffer` (oggi irraggiungibile) resta com'è, tradotto nel comando | modifica chirurgica, fuori perimetro |
| D4 | numpy entra in RT-01 (serve ai test e alle misure); OpenCV in RT-11 | ogni dipendenza entra con il primo task che la usa |
| D5 | La taratura sulle foto reali (RT-34) sta **dopo** la corsia | la corsia si chiude senza aspettare il consenso dei titolari; le soglie partono prudenti (decisione del 9 novembre) |
| D6 | Finché L2 non c'è (prima di RT-25), Standard = Originale e Spinta è spenta | ogni task chiude con un prodotto coerente |
| D7 | Rilevatore dei volti: cascate di Haar incluse in OpenCV; uno migliore si valuta in RT-34 | nessun modello da scaricare per ora |
| D8 | I test sui volti usano un rilevatore finto iniettato; il rilevatore vero si prova in RT-32 | nessuna foto con volti nel repository |

---

## 5. I task

**Ondate** (a ogni fine ondata, controlli verdi e PR intermedia verso il branch della corsia, regola 2):

| Ondata | Task | Che cosa si ha alla fine |
|---|---|---|
| A · Fondamenta | RT-00, RT-01, RT-02, RT-03, RT-04, RT-05 | documenti, strumenti di test, colore sRGB, copia per l'AI, esecutore a passi fissi, migrazioni |
| B · Render e pubblicazione | RT-06, RT-07, RT-08, RT-09, RT-10 | render salvati, pubblicazione dal file, anteprima reale, test dei componenti ed end-to-end in CI |
| C · Analisi locale | RT-11, RT-12, RT-13, RT-14, RT-15, RT-16, RT-17, RT-18 | OpenCV, catalogo, misure, candidati e i passi dell'esecutore |
| D · AI e varianti | RT-19, RT-20, RT-21, RT-22, RT-23, RT-24, RT-25, RT-26, RT-27 | preparazione dell'analisi, schema, prompt, diagnosi, varianti, generazione |
| E · Operatore e prova | RT-28, RT-29, RT-30, RT-31, RT-32, RT-33 | intervento, privacy, card, strumento di prova, prova della corsia |

| ID | Task | Leggi | Dipende da | Fatto quando | ☐ |
|---|---|---|---|---|---|
| RT-00 | **Preparazione della corsia**: ADR nuovo con le decisioni dal 7 al 9 novembre; spec R-42 e R-21; plan (rotte e job nuovi, §6, §7); questo file | nota §0, §5–§12 | — | documenti coerenti tra loro; comandi verdi | ☑ |
| RT-01 | **Strumenti di test per le immagini**, numpy, hypothesis in CI | nota §12.1; §3 qui | RT-00 | `tests/immagini.py` con i suoi test; hypothesis eseguito in CI | ☑ |
| RT-02 | **Colore sRGB** | nota §12.1 | RT-01 | i casi di 12.1 verdi; sistemazione con sRGB | ☑ |
| RT-03 | **Copia per l'AI preparata dal modulo** | nota §6.1, §7.2 | RT-02 | l'adapter non legge più l'archivio; l'AI riceve sRGB | ☑ |
| RT-04 | **Esecutore a passi fissi**, fine dell'autocontrasto per canale | nota §7.5, §12.4 | RT-02 | `sistema_foto_buffer` passa dall'esecutore; foto buone invariate | ☑ |
| RT-05 | **Migrazioni**: `versione_post_foto.ritocco`, `versione_post_foto.render`, `chiamata_ai.token_in_cache` | nota §8.6, §12.3 | RT-00 | upgrade e downgrade puliti | ☑ |
| RT-06 | **Render salvati**: adapter dell'archivio esteso ai file derivati, chiave, cache delle anteprime | nota §10.11, §12.5 | RT-04 | render idempotente; originale intatto; §1.2 rispettata; nome derivato validato | ☑ |
| RT-07 | **Render all'approvazione e pubblicazione dal file** (blocco congelato) | nota §7.6 | RT-05, RT-06 | Meta finto riceve i byte del render approvato; URL Instagram con la chiave | ☑ |
| RT-08 | **Anteprima reale per l'operatore** (e per l'artigiano, D1) | nota §6.2 a, §8.2 | RT-06 | la card mostra il render; BOLA verde | ☑ |
| RT-09 | **Test dei componenti**: Vitest, Testing Library, MSW, in CI | §3 qui | RT-08 | `npm test` in CI con i primi test della card | ☑ |
| RT-10 | **Test end-to-end in CI**: workflow per il Playwright già presente, dati di prova del ritocco | §3 qui | RT-08 | `percorso-demo` e un percorso del ritocco verdi in CI | ☑ |
| RT-11 | **OpenCV** e regola "Pillow unico decoder" | nota §2.2 | RT-01 | dipendenza in `requirements.txt`; la regola fallisce su `cv2.imread` | ☐ |
| RT-12 | **Catalogo del ritocco** | nota §12.2, §12.5 | RT-00 | codici, fasce, parametri e versioni in un solo file, con i test di coerenza | ☐ |
| RT-13 | **Misure e fasce** | nota §7.2, §9.5 | RT-11, RT-12 | ogni misura provata su un'immagine sintetica con valore noto | ☐ |
| RT-14 | **Candidati e segni** | nota §7.2, §9.6 | RT-13 | quadrilatero sintetico trovato con errore < 1% del lato | ☐ |
| RT-15 | **Geometria**: rotazioni, prospettiva | nota §7.5 passi 3, 5 | RT-04, RT-14 | rettangolo inclinato raddrizzato entro 0,5° | ☐ |
| RT-16 | **Finestra e barre** | nota §7.5 passo 6, §12.5 | RT-15 | proprietà della finestra verdi | ☐ |
| RT-17 | **Luce e nitidezza** | nota §10.7, §12.5 | RT-13, RT-16 | dosi entro i tetti; zona morta sulle foto buone | ☐ |
| RT-18 | **Privacy**: sfocatura delle zone | nota §7.5 passo 4 | RT-04 | zona illeggibile, resto invariato | ☐ |
| RT-19 | **Preparazione dell'analisi**: una decodifica per copia AI, contesto e `locale` | nota §7.2, §10.3, §12.2 | RT-03, RT-14 | una sola decodifica per foto; contesto solo con le fasce non normali | ☐ |
| RT-20 | **Schema compatto** | nota §12.2 | RT-12 | contratto schema ⇄ catalogo; validatori morbidi | ☐ |
| RT-21 | **Prompt `analisi_v4`** e ordine dei messaggi | nota §9.3, §9.4, §12.2, §12.3 | RT-19, RT-20 | ogni codice nel prompt; prompt statico; prefisso sopra soglia | ☐ |
| RT-22 | **Token in cache e costo** | nota §12.3 | RT-05, RT-21 | `token_in_cache` salvato; costo di riserva corretto | ☐ |
| RT-23 | **Provider finto aggiornato** | nota §6.2 g, §12.2 | RT-20 | risposte compatte configurabili; punteggio intero | ☐ |
| RT-24 | **Diagnosi** (doppia chiave) | nota §7.4, §10.7, §12.2 | RT-13, RT-20 | una riga di test per ogni riga della tabella 10.7 | ☐ |
| RT-25 | **Varianti** come comandi | nota §12.5 | RT-16, RT-17, RT-18, RT-24 | tre comandi per foto; Spinta spenta se uguale alla Standard | ☐ |
| RT-26 | **Integrazione nella generazione** e render Standard nel worker | nota §7.1–§7.4 | RT-06, RT-21, RT-23, RT-25 | campagna finta generata con varianti e render Standard; tempo di 20 foto misurato | ☐ |
| RT-27 | **Ricalcolo locale** per le foto già analizzate (comando, senza AI) | nota §10.12 | RT-25 | foto v3 con varianti; nessuna chiamata AI | ☐ |
| RT-28 | **Intervento `RITOCCA_FOTO`** (backend) | nota §8.5, §12.4 | RT-07, RT-26 | versioni, stati, altro canale, BOLA verdi | ☐ |
| RT-29 | **Privacy in Approva** (backend) | nota §8.4, §12.4 | RT-28 | Approva chiede la conferma con zone da decidere | ☐ |
| RT-30 | **Card con tre varianti** (frontend) | nota §12.4 | RT-09, RT-28 | test dei componenti verdi | ☐ |
| RT-31 | **Riepilogo privacy in Approva** (frontend) | nota §8.4 | RT-09, RT-29 | test dei componenti verdi | ☐ |
| RT-32 | **Strumento di prova `prova-ritocco`** | nota §9.10 | RT-26 | gira con il finto in pytest; rapporto e foglio di confronto | ☐ |
| RT-33 | **Prova della corsia** e documentazione | tutto | RT-10, RT-27…RT-32 | end-to-end completo verde; percorso a mano; README; descrizione della PR | ☐ |
| RT-34 | *Dopo la corsia:* **taratura sulle foto reali** | nota §9.10 | RT-33, consenso dei titolari | soglie ritarate con il rapporto di RT-32 | ☐ |

---

## 6. Il dettaglio dei task

### RT-00 · Preparazione della corsia

- **ADR nuovo** in `docs/ADR.md`, che è la versione corta (ADR-122): una riga nuova in fondo alla sua sezione, una frase per decisione con il perché; le alternative scartate stanno nella nota. `docs/archivio/` non si tocca. Le decisioni: ritocco a ciclo aperto (diagnosi AI, esecuzione locale); una sola chiamata AI con schema compatto; tre varianti per l'operatore; privacy proposta; intervallo unico; ritaglio anche in intervallo; raddrizzamento; sRGB; render salvato all'approvazione; codice congelato toccato in modo chirurgico; dipendenze nuove; corsia con PR finale.
- **Spec:** R-42 (ritaglio anche dentro l'intervallo, raddrizzamento entro una tolleranza, tre varianti, sRGB, render approvato) e R-21 se serve; §2.2 (la sistemazione non è una tappa: la variante Standard si rende alla fine della generazione); §2.3 (Ritocca tra gli interventi). La versione completa in `docs/archivio/` non si tocca.
- **Plan:** rotte nuove con il loro stato, job, funzioni tra moduli (§6), fixture dei test (§7).
- **Fatto quando:** documenti coerenti tra loro e con questo piano; comandi verdi.

### RT-01 · Strumenti di test per le immagini, numpy, hypothesis in CI

- `backend/requirements.txt`: `numpy` (BSD-3), motivo: misure sulle foto e test numerici.
- `.github/workflows/backend.yml`: installa anche `backend/requirements-accettazione.txt`, così i test di proprietà girano in CI (oggi si saltano).
- `backend/tests/immagini.py`:
  - generatore di profili ICC v2 a matrice (Display P3 e sRGB) dai primari pubblici, con adattamento Bradford a D50 e curva sRGB (il metodo della nota 12.1);
  - immagini sintetiche: tinta unita, gradiente, colore con dominante, rettangolo inclinato su sfondo, linee inclinate di un angolo dato, immagine sfocata e nitida, JPEG di qualità data, EXIF con orientamento e flash, PNG con `iCCP`, WEBP con ICC, JPEG CMYK;
  - `delta_e(a, b)` (CIE76 in Lab, numpy) e `media_lab(img, riquadro)`.
- **Test:** il profilo sRGB generato riconverte i colori senza cambiarli (±1); ogni generatore produce ciò che dichiara.
- **Fatto quando:** test verdi in locale e in CI, con hypothesis presente.

### RT-02 · Colore sRGB

- `campagne/colore.py`: `apri_in_srgb(dati: bytes, lato_max: int | None) -> Image`, con decodifica Pillow e i limiti di oggi (36 MP), `draft()` per i JPEG quando c'è `lato_max`, `exif_transpose`, conversione ICC → sRGB (relativo colorimetrico, compensazione del punto nero), modi particolari, profilo rotto → avviso nel log e nessuna eccezione. Più `profilo_srgb_bytes()` per incorporare sRGB nel JPEG in uscita.
- `sistemazione_foto.py` (test in `tests/moduli/campagne/test_sistemazione_foto.py`): usa `apri_in_srgb` al posto di `Image.open` + `exif_transpose` + `convert`; il JPEG porta il profilo sRGB; EXIF e GPS restano tolti.
- **Collegamenti:** `campagne/immagini.py` (i controlli al caricamento restano com'erano); `test_sistemazione_foto.py` adattato.
- **Test:** pomodoro P3 → (239, 35, 17) ±2; neutri invariati; foto senza profilo invariata; profilo rotto senza eccezione; PNG con `iCCP`; WEBP con ICC; CMYK; il JPEG in uscita ha il profilo sRGB e nessun EXIF.

### RT-03 · Copia per l'AI preparata dal modulo

- `adapters/ai/base.py::FotoAI`: campo `immagine: bytes | None` (JPEG pronto); `litellm.py::_foto_per_ai` usa quei byte (base64) e non legge più l'archivio; con `immagine` vuota l'errore resta `richiesta` come oggi.
- `campagne/service.py::copia_per_ai(foto_id) -> bytes` (sRGB, 1024 px, q85); `contenuti/generazione.py::_gruppo_ai` la riempie.
- Lo storico (`chiamata_ai.richiesta`) continua a registrare `"<foto {id}>"`, mai i byte.
- **Test:** l'adapter con byte (nessun accesso all'archivio); generazione con AI finta; il JPEG per l'AI è sRGB.

### RT-04 · Esecutore a passi fissi, fine dell'autocontrasto per canale

- `campagne/esecutore.py`: `Comando` (dataclass: `ruota`, `raddrizza`, `finestra`, `barre`, `luce`, `nitidezza`, `versione`) e `esegui(dati, comando, zone_privacy) -> bytes` con i dieci passi della nota 7.5. I passi non ancora scritti sono vuoti e fanno nulla: si riempiono in RT-15…RT-18.
- `comando_originale(foto)`: le regole di oggi di R-42 (rapporto, soggetto, centro, bordi sfocati) **senza autocontrasto**.
- `sistema_foto_buffer` diventa un involucro che costruisce `comando_originale` (firma e `proporzione` invariate, D3).
- **Effetto da scrivere nella PR:** da questo task fino a RT-25 (D6) l'uscita di ogni foto pubblicata non ha più l'autocontrasto di oggi; il criterio "foto buone invariate" si misura rispetto all'originale ridimensionato, non rispetto all'uscita di oggi.
- **Test:** ordine dei passi; nessun metadato; profilo sRGB; lato corto 1080; le regole di rapporto di oggi (test esistenti adattati); proprietà con hypothesis (qualunque dimensione valida → rapporto nell'intervallo, nessuna eccezione); foto buone con ΔE < 1.

### RT-05 · Migrazioni

- Alembic: `versione_post_foto.ritocco` (JSONB, nullabile), `versione_post_foto.render` (testo, nullabile), `chiamata_ai.token_in_cache` (intero, nullabile). Modelli aggiornati.
- **Test:** `alembic upgrade head` e `downgrade -1` puliti su un DB con dati; i modelli leggono righe vecchie con i campi vuoti.

### RT-06 · Render salvati

- `campagne/service.py`: `rendi(foto_id, comando, zone) -> chiave` (crea il file solo se manca), `leggi_render(foto_id, chiave) -> bytes`, `chiave_render(...)` = sha256 del comando canonico + zone + versione dell'esecutore + `foto.file`.
- **Adapter dell'archivio** (`adapters/archivio/base.py`, `disco.py`, `finto.py`): metodi nuovi per i derivati, `salva_derivato(foto_id: int, chiave: str, contenuto: bytes)`, `leggi_derivato`, `esiste_derivato`, `elimina_derivato`. Il file sta in `derivate/<foto_id>/<chiave>.jpg` sotto la radice; `foto_id` deve essere un intero positivo e `chiave` esattamente 64 caratteri esadecimali minuscoli, altrimenti `ValueError`; il percorso risolto deve restare dentro `derivate/` (stessa difesa di `_valida_e_risolvi_percorso`). I metodi di oggi (`salva`, `leggi`, `elimina`, `esiste`, `valida_nome_file`) non cambiano. Mai sopra l'originale (§1.3). Cambio da elencare nella PR.
- Anteprime non approvate: cache su disco con potatura per età (D2); i render approvati non si potano mai.
- **Test:** adapter su disco e finto: salva/leggi/esiste/elimina dei derivati; chiave non esadecimale, di lunghezza sbagliata o con `..`, `foto_id` negativo o testuale → `ValueError`; il derivato non sovrascrive mai un originale; due chiamate uguali, un file; chiavi diverse per comandi diversi; hash dell'originale invariato (estende `test_03_originale_intatto.py`); un render approvato sopravvive alla potatura (estende `test_02_niente_si_cancella.py`).

### RT-07 · Render all'approvazione e pubblicazione dal file

- `contenuti/service.py`: `rendi_foto_approvate(db, campagna_id)`, che per ogni `VersionePostFoto` approvata rende la variante scelta (`ritocco`, o Standard) con la privacy e salva la chiave in `render`. Va chiamata da `revisione/service.py::approva` dopo `approva_post`, e in ogni punto in cui una versione nasce approvata (interventi dopo l'approvazione, R-16).
- `pubblicazione/service.py` (blocco congelato, righe ~132–137): `foto_sistemata(...)` diventa la lettura del render del legame; se manca (post approvati prima della corsia), si rende e si salva in quel momento. Il limite di una foto per post resta; il commento di congelamento si aggiorna.
- `campagne/foto_pubblica.py` (`calcola_mac`, `componi_firma`, `verifica_firma`, `genera_url_pubblico`) e `campagne/service.py::url_foto_pubblica`: la firma copre foto, canale, chiave del render e scadenza; `GET /foto/{id}/pubblica?chiave=…` (non congelata) serve il file salvato. Con la chiave assente, le URL già emesse continuano a servire la foto sistemata al volo come oggi, finché non scadono.
- **Test:** pubblicazione con Meta finto → byte uguali al render approvato (hash); URL firmato con chiave alterata → 404 (estende `test_foto_pubblica_firma.py`); pubblicazione idempotente (`test_07`) verde; post approvato senza render → reso al volo.

### RT-08 · Anteprima reale

- Rotta autenticata `GET /post/{post_id}/foto/anteprima?variante=standard|spinta|originale` (router di `revisione`, permessi come la vista della campagna): rende o legge dalla cache e risponde con un JPEG. Per l'artigiano, solo sui post approvati e solo la variante scelta (D1).
- Vista del post (`revisione/schemas.py`, `revisione/service.py`): `foto.anteprima_url`, `foto.varianti` (disponibili, uguali, scelta), `foto.zone_privacy` (numero, decise o no), `foto.avvisi`. Fino a RT-25 c'è solo Originale (D6).
- `frontend/src/pages/operatore/campagna/PostCard.tsx`: l'immagine viene da `anteprima_url` (oggi `/api/foto/{id}/file`, cioè l'originale); il commento "come esce" torna vero. Calendario dell'artigiano: render dei post approvati.
- **Test:** rotta per ogni ruolo (BOLA in `test_bola_nuovi_endpoint.py`); un artigiano non vede le anteprime di un post non approvato; tipo e dimensioni del JPEG.

### RT-09 · Test dei componenti

- Dipendenze di sviluppo in `frontend/package.json`, da elencare nella PR: `vitest` (MIT), `@testing-library/react` (MIT), `@testing-library/user-event` (MIT), `@testing-library/jest-dom` (MIT), `jsdom` (MIT), `msw` (MIT).
- `vitest.config.ts`, setup con `MantineProvider` e MSW, script `npm test`; `.github/workflows/frontend.yml` lo esegue.
- Primi test: la card mostra l'immagine di `anteprima_url`, con testo alternativo; stato di caricamento e di errore dell'immagine.
- **Fatto quando:** `npm test` verde in locale e in CI.

### RT-10 · Test end-to-end in CI

- **Esiste già** (T4-106): `frontend/e2e/percorso-demo.spec.ts`, `frontend/e2e/prepara-backend.sh` (DB dedicato `adflow_e2e`, migrazioni e seed), `frontend/playwright.config.ts` (Chromium, un worker, due `webServer`), script `npm run test:e2e`, `@playwright/test` e `@axe-core/playwright` già in `package.json`. **Nessuna dipendenza nuova.** La CI non lo esegue ancora.
- Workflow CI nuovo (`e2e.yml`) con Postgres, `prepara-backend.sh`, backend, worker se serve, frontend, `npx playwright install --with-deps chromium`; il test `percorso-demo` esistente deve passare prima di aggiungere altro. Variabili e porte come nella configurazione di oggi; se in CI serve cambiarle, si cambiano lì e si segnala.
- Dati per il ritocco: foto sintetiche (una P3, una storta, una buia, una buona) caricate dal seed di `prepara-backend.sh` con AI finta e archivio su disco; se la generazione richiede il worker, il test lo avvia.
- Primo percorso nuovo: accesso dell'operatore → Vedi campagna → la foto del post è il render (risposta JPEG dalla rotta di anteprima, lato corto 1080).
- **Fatto quando:** `percorso-demo` e il percorso del ritocco verdi in locale e in CI.

### RT-11 · OpenCV e regola del decoder

- `backend/requirements.txt`: `opencv-python-headless` (Apache-2.0; le wheel includono librerie di terzi, tra cui FFmpeg con licenza LGPL: la nota va riportata), motivo: candidati e geometria. Mai `opencv-python`.
- Regola nel probe di sicurezza (`scripts/esegui_valutazione_sicurezza.py`) o in un test: in `app/` niente `cv2.imread`, `cv2.imdecode`, `cv2.VideoCapture`. Pillow decodifica, OpenCV riceve array.
- **Test:** la regola fallisce su un sorgente di prova che usa `cv2.imdecode`; l'import di `cv2` funziona in CI.

### RT-12 · Catalogo del ritocco

- `campagne/ritocco_catalogo.py`: i codici `Nota` e `RuoloZona` (nota 12.2) con significato ed effetto; le fasce con le soglie (nota 9.5); i parametri di Standard e Spinta (nota 12.5) con valori di partenza prudenti; le versioni (`locale-1`, `diagnosi-1`, `ritocco-1`).
- **Test:** ogni codice ha un effetto dichiarato; Spinta ≥ Standard su ogni parametro; nessuna soglia fuori dal suo dominio.

### RT-13 · Misure e fasce

- `campagne/preanalisi.py::misura(img) -> dict`: nitidezza (varianza del Laplaciano, normalizzata per dimensione), luminanza mediana e percentili, luci bruciate, ombre chiuse, dominante (a*, b*), caduta di luce ai bordi, angolo delle linee dominanti (Hough), qualità JPEG dalle tabelle di quantizzazione; fatti EXIF (flash, ISO, zoom digitale, fotocamera, software). `fasce(misure) -> dict`, solo le fasce non normali.
- Le misure si fanno sulla copia di lavoro (~2048 px).
- **Test:** per ogni misura un'immagine sintetica con valore noto (sfocata contro nitida, buia contro normale, tinta calda, linee a 3°, JPEG q30 contro q95, EXIF con flash).

### RT-14 · Candidati e segni

- `preanalisi.py::candidati(img)`: volti (cascate di Haar frontale e di profilo, soppressione dei doppioni, riquadri normalizzati, affidabilità; rilevatore iniettabile per i test, D8) e quadrilateri (Canny, `findContours`, `approxPolyDP`, convessità, area ≥ 5%, al massimo 3, angoli affinati con `cornerSubPix`), con i codici `V1…`, `Q1…`.
- `disegna_segni(copia_ai, candidati)`: riquadri sottili con l'etichetta. Si accende con un'impostazione, spenta finché RT-34 non decide (nota 9.6).
- **Test:** rettangolo inclinato sintetico trovato con errore degli angoli < 1% del lato; nessun quadrilatero su un gradiente; codici stabili; con il rilevatore finto, i volti diventano `V1`, `V2` nell'ordine atteso.

### RT-15 · Geometria

- Passo 3 (codici `ruota_*`) e passo 5 (rotazione fine dall'angolo misurato; prospettiva dal candidato Q, con omografia via numpy o `cv2.getPerspectiveTransform` e `Image.transform(PERSPECTIVE)` con i **coefficienti inversi**; ritaglio dei bordi vuoti). Mappa delle coordinate tra i passi, perché soggetto e zone seguano la foto.
- Controlli: deformazione entro il parametro della variante; se un controllo fallisce, il passo si salta (non il comando).
- **Test:** rettangolo inclinato → lati paralleli entro 0,5°; test esplicito sull'inversione dei coefficienti; punti mappati correttamente; deformazione oltre soglia → passo saltato.

### RT-16 · Finestra e barre

- Passo 6: la finestra del comando (rapporto più vicino nell'intervallo; contiene soggetto e zone `tieni` con il margine; evita le zone `togli`; centrata su `centro`; limite di ingrandimento della variante); barre sfocate o neutre quando serve (la logica di oggi, spostata qui); passo 7 (lato corto 1080).
- La finestra la **calcola** `varianti.py` (RT-25); l'esecutore la **applica**. In questo task si scrive la funzione di calcolo con i suoi test.
- **Test (proprietà):** la finestra è sempre dentro la foto, ha un rapporto nell'intervallo, contiene soggetto e `tieni`, non supera l'ingrandimento ammesso; con `non_tagliare` resta solo il taglio dovuto al rapporto.

### RT-17 · Luce e nitidezza

- Passi 8 e 9: esposizione (curva sulla luminanza con la crominanza conservata), bianco (guadagni dalla zona `neutro`, oppure media dei grigi sul soggetto solo in Spinta), ombre (maschera di luminanza), flash (compensazione radiale della caduta ai bordi), nitidezza (`UnsharpMask` lieve o media). Misure nella regione del soggetto, portata nel riferimento corrente. Dosi e tetti dal catalogo.
- **Test:** immagine buia → mediana verso l'obiettivo, entro il tetto; zona neutra tinta → corretta entro la tolleranza; foto buona → ΔE < 1 (zona morta); nitidezza spenta con compressione forte.

### RT-18 · Privacy

- Passo 4: sfocatura forte (o pixelatura) delle zone attive, con un margine del 15% e un raggio proporzionale alla zona, nel riferimento dell'originale, prima della geometria.
- **Test:** nella zona la varianza scende sotto soglia (testo sintetico illeggibile); fuori dalla zona i pixel restano uguali; la zona segue la foto dopo raddrizzamento e finestra.

### RT-19 · Preparazione dell'analisi

- `campagne/service.py::prepara_analisi(foto_ids) -> {foto_id: {"immagine", "contesto", "locale"}}`: una decodifica per foto (`apri_in_srgb` con `draft`), copia AI (1024, q85, segni se accesi), misure, fasce, candidati; `locale` come nella nota 10.3; contesto in testo semplice ("Foto 51: scura, nitidezza bassa; candidati V1 V2"), solo le fasce non normali.
- `generazione.py`: usa `prepara_analisi` al posto di `copia_per_ai` (RT-03).
- **Test:** una sola decodifica per foto (spia su `apri_in_srgb`); una foto pulita ha il contesto vuoto; il contesto resta sotto ~80 caratteri in media sulle foto sintetiche; un errore su una foto non ferma le altre (quella foto va senza contesto).

### RT-20 · Schema compatto

- `adapters/ai/schemi.py`: `Nota`, `RuoloZona` (copie del catalogo), `Zona`, `Ritocco`, `AnalisiFoto` con `soggetto_box: list[int] | None` e `ritocco: Ritocco | None` (nota 12.2); validatori morbidi (quattro interi in 0–100, riquadro dentro la foto, `centro`, `volti` nel formato "Vn ruolo", liste troncate, note in conflitto scartate).
- `litellm.py::analizza_gruppo`: riconverte `soggetto_box` nel dizionario 0–1 di oggi (chi legge `analisi_ai` non cambia); deriva `persone_riconoscibili` e `marchi_visibili`; consegna `ritocco` così com'è a L2.
- **Test:** contratto (le copie uguali al catalogo, come per `TipoFoto`); ogni validatore con valori buoni e cattivi; una risposta con `ritocco` malformato non è un errore (vale `None`).

### RT-21 · Prompt `analisi_v4` e ordine dei messaggi

- `adapters/ai/prompts/analisi_v4.md`: v3 più le sezioni nuove, nella forma dei codici (nota 9.4 e 12.2); circa 900 token in più; nessun segnaposto. `analisi_v3.md` resta.
- `litellm.py`: `versione_prompt="analisi_v4"`; messaggi nell'ordine C3 (sistema, poi descrizione del gruppo, poi per ogni foto riga, contesto e immagine).
- **Test:** ogni codice e ogni ruolo compaiono nel prompt; il prompt non contiene parentesi graffe di segnaposto né date; il prefisso (prompt più schema) è sopra 1.024 token stimati (caratteri/4); due chiamate con gruppi diversi hanno lo stesso messaggio di sistema byte per byte; ordine dei messaggi.

### RT-22 · Token in cache e costo

- `litellm.py::_uso`: legge `usage.prompt_tokens_details.cached_tokens` in `UsoAI.token_in_cache`; il costo di riserva usa il prezzo in cache per quei token (configurazione nuova `AI_PREZZO_INGRESSO_CACHE_MILIONE` in `backend/.env.example`); `chiamata_ai.token_in_cache` salvato. Da verificare se `litellm.completion_cost` li conta già: se sì, nessuna doppia correzione.
- Storico AI (pagina dell'operatore): i token in cache accanto a quelli in ingresso.
- **Test:** risposte finte con e senza `cached_tokens`; costo atteso nei due casi; campo salvato.

### RT-23 · Provider finto aggiornato

- `adapters/ai/finto.py::analizza_gruppo`: risposte nel formato compatto, `ritocco` configurabile per foto (come `_analisi` oggi), punteggio intero da 1 a 5 (oggi 0.8, nota 6.2 g), `soggetto_box` nel formato riconvertito.
- **Test:** il finto passa lo stesso schema e gli stessi validatori del vero; i test esistenti che dipendevano da 0.8 sono adattati.

### RT-24 · Diagnosi

- `campagne/diagnosi.py::diagnosi(ai, locale) -> dict` (nota 10.7 e 10.8 nel formato della 12.2): doppia chiave, zone privacy (volti non citati = `cliente`; `staff` e `no` esclusi; zone `volto` e scritte private aggiunte), avvisi, scarti.
- **Test:** una riga di test per ogni riga della tabella 10.7 (AI sì / misura sì → applicata; una sola → scarto registrato); proprietà: nessuna eccezione con risposte e misure casuali.

### RT-25 · Varianti

- `campagne/varianti.py::varianti(foto, diagnosi) -> {"originale", "standard", "spinta"}`: comandi nel formato della nota 12.5, con finestra (RT-16), raddrizzamento, luce, nitidezza; uguaglianze calcolate (Spinta uguale a Standard, Standard uguale a Originale); il tutto salvato in `foto.analisi_ai["ritocco"]`.
- **Test:** tabelle di casi (foto buona → Standard uguale a Originale; foto buia con doppia chiave → esposizione solo in Standard e Spinta; superficie Q1 → raddrizza); proprietà (comandi sempre eseguibili dall'esecutore).

### RT-26 · Integrazione nella generazione

- `generazione.py::_analizza`: `prepara_analisi` → AI → `diagnosi` → `varianti` → `aggiorna_foto` con `locale` e `ritocco`; `_CAMPI_ANALISI` esteso; un errore di L1 o L2 su una foto lascia l'analisi di oggi e la variante Originale (nessuna generazione interrotta).
- Alla fine della generazione si rende la Standard delle foto usate dai post (cache delle anteprime), così la card si apre pronta.
- **Tempo misurato qui, non solo in RT-32:** un test con 20 foto sintetiche (AI finta) registra il tempo di L1 + L2 + render Standard e lo confronta con il limite di 30 minuti oltre il quale `ferma_generazione` mette la campagna in `generazione_fallita`; se il margine è sotto il 5×, i render Standard si spostano in un job separato dopo la generazione.
- Al piano arrivano gli stessi campi di oggi (`_valutazione` invariata, O9).
- **Test:** campagna finta generata con varianti salvate e render Standard pronti; errore in L1 → generazione completa, foto in Originale; il piano riceve gli stessi campi di prima (test su `_valutazione`).

### RT-27 · Ricalcolo locale

- Comando `python -m app.cli ricalcola-ritocco [--campagna ID]`: per le foto con analisi v3 (senza `ritocco`) calcola misure e varianti senza AI e senza candidati (nessuna risposta AI li cita: niente raddrizzamento né privacy proposta). È idempotente.
- **Test:** foto v3 → varianti presenti; nessuna chiamata registrata in `chiamata_ai`; una seconda esecuzione non cambia niente.

### RT-28 · Intervento `RITOCCA_FOTO`

- `contenuti/domain.py`: `RITOCCA_FOTO` in `INTERVENTI_AMMESSI` negli stessi stati di `CAMBIA_FOTO`.
- `contenuti/interventi.py::ritocca_foto(db, post_id, variante, privacy, utente, adesso)`: versione nuova con testo e hashtag della precedente, `tipo_intervento="ritocca_foto"`, `legame.ritocco` impostato; applicata a tutti i post della campagna con la stessa foto (se uno non lo ammette, la risposta lo dice); dopo l'approvazione la versione nasce approvata e si rende (RT-07). Nessuna AI.
- `revisione/interventi.py::ritocca_foto(...)`: livello intermedio come `cambia_foto` (riga 88), che chiama `contenuti.ritocca_foto`. Prima di inserire il codice si controlla che né la rotta né la funzione cadano in un blocco "Congelato per l'MVP, ADR-114" (il router ne ha tre, alle righe ~121, ~149, ~178, e `revisione/interventi.py` uno alla ~169: `controllato`, `nota`, `togli-canale`); se cadono, si segnala nella PR.
- Rotta `POST /post/{post_id}/ritocca-foto` in `revisione/router.py` (accanto a `cambia-foto`), con schema in `revisione/schemas.py`; `interventi` della vista lo elenca.
- **Test:** stati ammessi e vietati; versione con autore; altro canale; dopo l'approvazione render nuovo; BOLA; il validatore dei testi non cambia esito.

### RT-29 · Privacy in Approva

- Vista della campagna: riepilogo delle zone da decidere (foto, numero).
- `revisione/service.py::approva`: se ci sono zone da decidere, serve `conferma_privacy` nel corpo (altrimenti 422 con il riepilogo); con `oscura_tutte` attiva tutte le zone (versioni `ritocca_foto` nella stessa transazione) e poi approva.
- **Test:** approva senza conferma → 422; con conferma e senza oscurare → approvata con le zone spente; con `oscura_tutte` → render con le zone sfocate; nessuna zona → Approva come oggi.

### RT-30 · Card con tre varianti

- `pages/operatore/campagna/PostCard.tsx` e un componente nuovo, per esempio `RitoccoFoto.tsx` in `pages/operatore/vedi-campagna/post/` (accanto a `CambiaFoto.tsx`): `SegmentedControl` (Originale, Standard, Spinta) con gli stati spenti; interruttore "Oscura N zone"; etichette e avvisi con i collegamenti a Cambia foto e a Chiedi all'artigiano; "vale anche per il post …"; immagine in caricamento durante il cambio; chiamata a `ritocca-foto`, poi la vista si ricarica.
- `frontend/src/api/interventi.ts`: `ritoccaFoto(postId, variante, privacy)`.
- **Test (Vitest e MSW):** le tre varianti e gli stati spenti; un clic manda la chiamata giusta; "Nessuna modifica necessaria"; avviso privacy; accessibilità (ruoli ed etichette).

### RT-31 · Riepilogo privacy in Approva

- Dialogo di Approva (`pages/operatore/campagna/Decidi.tsx` o il componente di Approva): riepilogo "N foto con M zone da decidere", "Oscura tutte", "Rivedi" (porta alla prima foto), conferma esplicita.
- **Test (Vitest e MSW):** con zone → riepilogo e conferma richiesta; "Oscura tutte" manda `oscura_tutte`; senza zone il dialogo è quello di oggi.

### RT-32 · Strumento di prova `prova-ritocco`

- `python -m app.cli prova-ritocco --cartella PERCORSO [--verita FILE.json]`: carica le foto di una cartella (fuori dal repository) in una campagna di prova, la genera con il provider configurato e scrive:
  - un rapporto con token in ingresso, in uscita e in cache e il costo per gruppo;
  - con un file di verità, sovrapposizione dei riquadri, errore degli angoli, richiamo dei volti, accordo sulle note;
  - un foglio HTML di confronto con Originale, Standard e Spinta per ogni foto.
- Sul modello di `prova-prompt` (T3-925); con l'AI vera si lancia solo a mano.
- **Test:** con AI e archivio finti (come `test_prova_prompt.py`): il rapporto si genera e il foglio contiene tre immagini per foto.

### RT-33 · Prova della corsia

- Percorso end-to-end completo (Playwright): generazione finta → Standard nella card → Spinta → Originale → Oscura → Approva con la conferma → `pubblica-ora` con Meta finto → i byte pubblicati sono quelli del render approvato.
- Percorso a mano in locale, con screenshot per la PR: le stesse azioni, più una foto P3 vera se disponibile.
- `backend/README.md`: comandi nuovi (`ricalcola-ritocco`, `prova-ritocco`, test end-to-end), prove a mano.
- Spec e plan riallineati a ciò che è stato scritto; la nota segnata come chiusa per le parti fatte.
- Descrizione della PR con tutto ciò che chiede AGENTS.md (regola 8 qui).
- **Fatto quando:** tutti i controlli verdi, compresi i test end-to-end; screenshot nella PR.

### RT-34 · Taratura sulle foto reali (dopo la corsia)

- Con il consenso dei titolari (README della PR #189): `prova-ritocco` sulle foto raccolte, con la verità scritta a mano su un sottoinsieme.
- Si decide: soglie e parametri del catalogo, segni accesi o spenti, rilevatore dei volti, costo reale contro la stima (+5–12%).
- **Fatto quando:** catalogo aggiornato con il rapporto della prova; costo medio entro la stima o decisione presa sulla `descrizione` (nota 12.2).

---

## 7. Rischi

| Rischio | Dove si vede | Che cosa si fa |
|---|---|---|
| Precisione delle coordinate dell'AI | RT-32, RT-34 | i candidati di OpenCV riducono il problema; finestre con margine |
| Volti mancati dal rilevatore e dall'AI | RT-14, RT-34 | richiamo misurato in prova; resta Cambia foto; zone sempre proposte all'operatore |
| Tempo del worker con 20 foto | RT-19, RT-26 | `draft()`, una decodifica, misure su ~2048 px; da misurare in RT-32 |
| Determinismo dei render tra versioni delle librerie | RT-06 | versioni fissate in `requirements.txt`; `versione_esecutore` nella chiave |
| Test end-to-end instabili | RT-10, RT-33 | un solo browser, dati sintetici, attese su risposte di rete e non su tempi fissi |
| Costo oltre la stima | RT-34 | leva della `descrizione` (nota 12.2), decisa dalla persona |
| Foto HEIC dall'iPhone | RT-33 | da verificare con un iPhone vero; oggi i magic bytes la rifiutano |
