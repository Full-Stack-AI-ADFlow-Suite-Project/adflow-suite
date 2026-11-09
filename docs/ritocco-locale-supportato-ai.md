# Ritocco locale supportato dall'AI · note di lavoro

Worktree: `ritocco-locale-supportato-ai` · branch `worktree-ritocco-locale-supportato-ai` · aperto il 7 novembre 2026.
Aggiornata il 9 novembre 2026 sul branch `ccr-5fa1049d-405z9r` (sezioni 0 e 5–11).
Questo file raccoglie la conversazione che ha portato al lavoro, la valutazione finale, il piano d'azione e un esempio di prompt con output strutturato. È una nota di lavoro, non documentazione di prodotto. Dove un'affermazione e il codice non tornano, vale il codice.

Come leggerla: le sezioni 1–4 sono la storia (mosaici, prima impostazione). Dalla 5 in poi c'è lo studio sul caso d'uso largo (le 375 foto della PR #189), sul flusso con l'operatore, sul prompt e sui dati strutturati. **Dove la 4 e le 8–10 non tornano, valgono le 8–10; dove le 8–11 non tornano con la 12 (9 novembre), vale la 12.**

---

## 0. Decisioni prese

| Data | Decisione | Effetto |
|---|---|---|
| 7 nov | Opzione 3 a ciclo aperto: l'AI dà la diagnosi, il codice locale misura ed esegue | Nessun ritocco generativo, nessun agente |
| 8 nov | Solo formati feed | Niente 9:16 (storie, reel) |
| 8 nov | **Intervallo unico** 4:5–1,91:1 per Facebook e Instagram | Nessun doppio ritaglio: via API Instagram non accetta il 3:4 (sezione 5.2) |
| 8 nov | Rapporto **più vicino** al formato reale della foto | Dentro l'intervallo il rapporto resta, fuori si va al bordo più vicino |
| 8 nov | **Ritaglio anche per le foto dentro l'intervallo** (avvicinamento al soggetto, esclusione del disordine ai bordi) | Cambia R-42 ("da 4:5 a 1,91:1 nessun taglio"): il rapporto resta, la finestra si stringe |
| 8 nov | **Privacy come proposta all'operatore**: le zone da oscurare si propongono, le attiva l'operatore | Nessun oscuramento automatico in pubblicazione |
| 8 nov | Inserire l'operatore nel flusso, con accesso a tutte le modifiche che stanno nel perimetro del costo | Ogni azione dell'operatore è locale e gratuita, nessuna chiamata AI in più |
| 8 nov | **Una sola chiamata AI** per l'analisi delle foto (per gruppo, come oggi) | La pre-analisi locale e le scelte dell'operatore non chiamano l'AI |
| 8 nov | I task per scrivere il codice si costruiscono a fine sessione | La sezione 11 raccoglie solo gli ingredienti |
| 9 nov | **Approvate le proposte** delle sezioni 5–11, comprese quelle della 11.1 che avevano una proposta: foto "copertina" come foto feed; conferma della privacy in Approva con un clic; scelte dell'operatore su `VersionePostFoto` con migrazione | 11.1 aggiornata |
| 9 nov | **L'aumento di costo del +40% è eccessivo**; la cache del prompt va rispettata | Schema compatto e sparso, prompt più corto, regole di cache: stima +5–12% (sezione 12.2–12.3) |
| 9 nov | **L'operatore ha poche scelte a singolo clic**: si mostra una modifica Standard completa; un clic per una modifica Spinta, già pronta come comando strutturato; un clic per l'Originale | Il pannello Ritocca della 8.3 è sostituito dalle tre varianti (sezione 12.4) |
| 9 nov | **Il colore delle foto iPhone va risolto** | Conversione ICC → sRGB obbligatoria e per prima (sezione 12.1) |

| 9 nov | **Tutte le decisioni diventano operative**; si scrive il piano della corsia | [`ritocco-corsia.md`](ritocco-corsia.md) |
| 9 nov | Il codice congelato (ADR-114) si può cambiare, se fatto bene e in modo chirurgico | Regola 4 della corsia |
| 9 nov | Test seri anche per il frontend, con le dipendenze che servono | Vitest, Testing Library, MSW, Playwright (RT-09, RT-10) |
| 9 nov | Soglie iniziali prudenti, taratura dopo | RT-34 dopo la corsia |
| 9 nov | Una corsia con più task; la PR si apre solo a corsia completa | Regole 1–2 della corsia |

Ancora aperte: l'autorizzazione a usare le foto reali raccolte con la PR #189 (consenso dei titolari); nessun'altra: le scelte di default D1–D8 della corsia sono approvate (9 novembre).

---

## 1. Cronologia della conversazione

### 1.1 Come vengono trattate oggi le foto (sintesi della risposta)

- **Ingressi:** `POST /campagne/{id}/foto` (bozza), `POST /archivio/foto` (congelato, ADR-114), `POST /campagne/{id}/richiesta/foto` (sostituzione chiesta dall'operatore, R-46), immagini AI generate dal worker.
- **Controlli all'ingresso** (`campagne/immagini.py`, adapter archivio): lettura a blocchi con tetto 10 MB; formato dai magic bytes (JPG, PNG, WEBP); lato corto ≥ 1080 px; max 8192×8192 e 36 MP; max 20 foto per gruppo; nome file `uuid4` deciso dal server. **L'originale si salva byte per byte**, con EXIF e GPS.
- **Analisi AI** (tappa `ANALISI`, `generazione._analizza` → `AILiteLLM.analizza_gruppo`): `_foto_per_ai` rilegge l'originale, applica EXIF, converte in RGB, riduce a max 1024 px, JPEG q85, base64, `detail: high`. Risposta strutturata (`RispostaAnalisi`): `idonea`, `motivo`, `tipo`, `punteggio`, `soggetto`, `descrizione`, `simile_a`, `soggetto_box`, `persone_riconoscibili`, `marchi_visibili`. Salvata in `foto.analisi_ai` (JSONB).
- **Sistemazione per la pubblicazione** (`campagne/sistemazione_foto.py::sistema_foto_buffer`): solo Pillow, in memoria, ricalcolata a ogni richiesta, mai salvata. EXIF → RGB → adattamento a 4:5–1,91:1 (ritaglio sul soggetto se ≤ 35%, al centro se ≤ 10%, altrimenti bordi sfocati) → lato corto 1080 → autocontrasto → JPEG q90 senza metadati.
- **Pubblicazione:** Facebook riceve i byte JPEG; Instagram un URL pubblico firmato (HMAC-SHA256, 24 h) a `GET /foto/{id}/pubblica`. Limite MVP: una foto per post.
- **Vincoli di progetto:** costituzione §1.3 (l'originale non si modifica mai), R-42, R-43; nei test niente chiamate AI reali; adapter non importano moduli (gli schemi duplicati hanno un test di confronto).

### 1.2 «Le foto vengono modificate? Chi? A cosa serve l'analisi AI?»

Sì, ma solo alla pubblicazione e da codice Pillow, non dall'AI. L'AI guarda e giudica: scarta le inadatte, ordina per punteggio, evita i doppioni, alimenta piano e testi, dà `soggetto_box` per il ritaglio e lo stile alle immagini AI di rimpiazzo. `persone_riconoscibili` e `marchi_visibili` oggi sono salvati ma non usati da nessuna parte.

### 1.3 Le quattro opzioni per il ritocco

1. **Generativa:** esclusa (fedeltà del prodotto, non riproducibile, costo a immagine, risoluzione 1024, R-43).
2. **Solo locale** (Pillow): deterministica, ma cieca.
3. **L'AI emette istruzioni, il codice locale le esegue:** scelta. Schema già presente: `soggetto_box`.
4. **Server MCP / agente:** scartato (processi, turni, costo, test).

Linea tenuta: l'AI dà la **diagnosi** (qualitativa, regioni), il codice **misura e dosa**.

### 1.4 Richiesta dell'utente (messaggio, con quattro foto di mosaici)

> valuta impatto su aggiunta dipendenze numpy e opencv. questo software è incentrato sulle foto. valuta foto di mosaici caricate. il problema principale è scegliere il ritaglio, adatto a aspect ratio dei social. decidere cosa tagliare, decidere il centro, decidere se aggiungere barre laterali per salvare delle aree, anche raddrizzare delle forme (tollerando una deformazione). sono solo esempi: per far capire che il lavoro è importante ma puramente tecnico. ovviamente approvo opzione 3 a ciclo aperto. io invertirei i tempi: ai analizza e invia in uscita comandi deterministici per pillow/numpy e opencv. problema è: come istruire ai ai comandi dei tools disponibili? quanto costa, come implementarlo. [domanda fuori contesto: si possono dare prompt permanenti quando si fanno chiamate api a uno stesso servizio? si dovrebbe usare un servizio che offre agenti insieme alle api, invece di chiamate generiche e cieche?]

Le quattro foto (circa 1126×2000, 2000×1126, 1125×2000, 1129×2000) sono quelle descritte nella tabella del punto 2.1. Non sono copiate in questa cartella: prima di usarle come fixture serve il via libera sul loro uso (sono opere di artigiani reali).

### 1.5 Richiesta attuale

Aprire il worktree `ritocco-locale-supportato-ai`, salvare la conversazione e soprattutto l'ultima risposta, redigere un piano d'azione, dare subito un esempio di prompt verso l'AI e di output strutturato partendo da ciò che c'è.

---

## 2. Ultima risposta (valutazione numpy e OpenCV)

Non sono state eseguite prove: foto guardate e codice riletto. I costi sono ordini di grandezza, le dimensioni dei pacchetti approssimate: da verificare con prezzi e wheel reali.

**Correzione al messaggio precedente.** La correzione di prospettiva non era "fuori da Pillow": `Image.transform(..., PERSPECTIVE, coeffs)` esegue la deformazione. A Pillow manca solo il *trovare* i quattro angoli.

### 2.1 Le quattro foto e cosa fa il codice oggi

| Foto | Cosa si vede | Cosa fa oggi `sistema_foto_buffer` | Cosa servirebbe |
|---|---|---|---|
| 1. Figura in kimono, pannello verticale | Opera circa 1:2 su muro bianco con catenella, margine di muro su tre lati, riflessi sul vetro | Rapporto 0,56, fuori intervallo. Il riquadro dell'opera (~85% dell'altezza) non entra nella finestra: caso (c), bordi sfocati. Il **muro resta nella foto centrale** | Togliere il muro, poi barre. Tagliare a 4:5 farebbe perdere ~37% dell'opera |
| 2. Calle bianche in vaso rosa, panoramica | Rapporto 1,78, dentro l'intervallo. A destra spunta **un altro mosaico**, più una striscia di muro; in basso un altro oggetto; riflessi di finestre | Niente (è in intervallo). L'altra opera resta | Ritaglio semantico che esclude l'intruso |
| 3. Ritratto in bianco e nero su parete rosa | Opera nel 60% superiore, sotto mensola e ombre | Il riquadro entra nella finestra 4:5, taglio ~30%: caso (a), **funziona già** | Solo la dominante rosa sulle tessere bianche |
| 4. Due figure abbracciate, vetro | Pannello ripreso di tre quarti: bordi che convergono; muro, battiscopa, macchie | Rapporto 0,57, caso (c): barre sfocate. L'opera resta inclinata e circondata di muro | Raddrizzare il quadrilatero: l'opera diventa ~3:4, vicina a 4:5, basta un taglio minimo |

Conclusioni:
- Il problema non è *dove tagliare un rettangolo*: prima va **isolata l'opera** dal contesto (muro, cornici, altre opere). Il codice attuale non ha il concetto di "contesto".
- Il raddrizzamento (foto 4) trasforma un caso senza soluzione in uno banale: è il guadagno più grande.
- Sulle foto 1 e 3 il codice si comporta già in modo ragionevole; sulla 1 si migliora togliendo il muro.
- **Colore:** nella foto 3 il muro rosa scalda le tessere bianche. Le misure vanno fatte solo **dentro la regione dell'opera**, non su tutta l'immagine.
- Il ritratto della foto 3 è di una persona reale in mosaico: `persone_riconoscibili` oggi non è usato.
- I riflessi sul vetro (foto 1, 2, 4) non si tolgono in modo onesto: al massimo si segnalano.

### 2.2 Impatto di numpy e OpenCV

**numpy**
- Licenza BSD-3, poche decine di MB installati.
- Risolve misure veloci (istogrammi, percentili, luminosità in una regione), omografia (sistema 8×8), curve tonali, guadagni per canale.
- Non indispensabile (Pillow arriva quasi a tutto), ma il codice è più corto e testabile.
- **Giudizio: sì, da subito.**

**opencv-python-headless**
- Apache-2.0; le wheel includono librerie di terzi (tra cui FFmpeg, LGPL): la nota di licenza va riportata.
- Ordine di 50–60 MB di wheel, ~100 MB installati. Wheel per Windows, macOS, Linux: non rompe `uv run` multipiattaforma. Sempre `-headless`, mai `opencv-python`.
- **Rischio vero: sicurezza dei decoder.** Mai `cv2.imdecode`/`imread` su file dell'utente. Pillow resta l'unico decoder (già protetto da header e limiti 36 MP); i pixel passano a OpenCV come array (`np.asarray(img)`) e OpenCV fa solo calcolo.
- Niente denoise né CLAHE su queste foto: la grana delle tessere *è* il prodotto, e l'equalizzazione locale altera i colori.
- Lo giustifica solo la **geometria**: raffinare i quattro angoli proposti dall'AI (`Canny`, `HoughLinesP`, `findContours` + `approxPolyDP`, `cornerSubPix`) e verificarne la plausibilità. I modelli di visione sbagliano le coordinate dei punti di qualche punto percentuale: dopo la deformazione si vedrebbero bordi storti. La foto 4 (vetro chiaro su muro chiaro) è il caso difficile per il rilevamento classico: l'AI dà l'idea grossolana, OpenCV la affina.
- **Giudizio: probabilmente sì, ma dopo una prova.**

**Memoria e prestazioni**
- Oggi la sistemazione lavora sull'originale fino a 36 MP (un array RGB ≈ 108 MB). Il risultato è di ~1080 px: la geometria si fa su una copia di lavoro di 2000–2400 px, più leggera e veloce.
- La sistemazione si rifà a ogni richiesta (anche a ogni download di Meta). Con rilevamento e deformazione conviene valutare di **salvare il risultato** per foto e canale, con chiave su piano e versione. È una scelta di progetto da decidere.

### 2.3 Chi decide cosa

| L'AI dice (semantica) | Il codice calcola (geometria e misure) |
|---|---|
| Dove sono i 4 angoli dell'opera (`opera`) | Raffina gli angoli, controlla convessità, angoli, area |
| Se l'opera è piana (si può raddrizzare) | Calcola l'omografia e il rapporto finale |
| Aree **intruse** da escludere (altra opera, cornice altrui) | Sceglie la finestra di ritaglio che le evita |
| Il centro d'interesse (viso, fiore) | Centra la finestra, entro la foto |
| La preferenza: opera intera con barre, o ritaglio accettabile | Applica le soglie (35% / 10%): non l'AI |
| Lo stile delle barre: sfocate, neutre, tinta dell'opera | Sceglie il colore vero dalla palette dell'opera |
| Il difetto di tono, qualitativo, con gravità | Misura dentro l'opera e dosa la correzione |

L'AI non scrive mai coordinate di ritaglio finali né valori di gamma.

**Raddrizzare tollerando la deformazione.** Il rapporto vero del pannello non è noto da una foto sola. Si accetta il rapporto più vicino tra quelli plausibili (3:4, 4:5, 1:1, 1:2) solo se la distanza dal misurato è sotto una soglia (da tarare, ~8%); altrimenti non si raddrizza. `opera_piana: true` solo per pannelli e quadri, mai per oggetti tridimensionali.

**Guardie del codice**
- area dell'opera ≥ ~20% del fotogramma;
- risoluzione effettiva: il minimo di 1080 px (R-13) oggi vale per l'intera foto, ma un ritaglio stretto può scendere sotto, e un ingrandimento oltre ~1,3× si vede: in tal caso si lascia più margine;
- quota di opera persa nel ritaglio;
- colore dell'opera prima e dopo.

### 2.4 Come istruire l'AI sugli strumenti

1. **Un solo catalogo, in codice.** Ogni strumento è registrato (nome, descrizione, parametri e limiti, funzione che lo applica). Da lì derivano schema Pydantic, testo del prompt e validazione.
2. **Output strutturato rigido.** Schema chiuso (`Literal`, `Field(ge, le)`), al massimo 6 operazioni, `null` se nulla da fare. Il progetto lo fa già con `RispostaAnalisi` e `riquadro_valido`.
3. **Il prompt spiega *quando*, non *come*:** per ogni strumento, quando serve, cosa fa, cosa non fa; convenzione di coordinate (origine in alto a sinistra, 0–1, come `analisi_v3`); priorità "mai tagliare l'opera"; "nel dubbio, nessuna operazione". Pochi esempi in testo; esempi con immagini ~1.000 token l'uno: al massimo due o tre.
4. **Contesto misurato dal codice** nella richiesta: dimensioni, rapporto, intervallo ammesso dai canali.
5. **Insieme di foto di riferimento** (30–50 mosaici con decisioni scritte a mano) per misurare ogni versione del prompt: errore sugli angoli, riquadro dell'opera, accordo sulla strategia. `cli.py` ha già un meccanismo di confronto (`rapporto_confronto`, T3-925). Costa pochi centesimi e **non va nei test**.

Vincoli di architettura già risolti dal progetto:
- Un adattatore non importa i moduli: lo schema sta in `adapters/ai/schemi.py` e **un test lo confronta con il catalogo in `campagne`**, come per `TipoFoto`.
- Un test controlla che ogni strumento del catalogo compaia nel prompt.
- Se la risposta non passa la validazione, un solo nuovo tentativo con le violazioni, come il piano (`piano_precedente` + `violazioni`).

### 2.5 Costo (prezzi ipotizzati: 3 $/M ingresso, 15 $/M uscita)

- **Nessuna chiamata in più:** il piano si aggiunge a `analizza_gruppo`.
- **Ingresso:** prompt attuale ~3 KB; catalogo, regole ed esempi aggiungono ~2.000–2.500 token **una volta per gruppo**. Le immagini (~1.000 token l'una) restano uguali.
- **Uscita:** ~+150–250 token per foto: è la voce che pesa, quindi lo schema va tenuto stretto, niente testo libero.
- Gruppo da 10 foto: oggi ~7 centesimi, con il ritocco ~10–11 → **+3–4 centesimi per gruppo**, meno di mezzo centesimo a foto. La cache sul prefisso fisso riduce ancora l'ingresso.
- Un modello con ragionamento esteso moltiplicherebbe i token di uscita: modello di visione senza ragionamento, o livello basso. La precisione geometrica varia molto da modello a modello: si sceglie con la prova sulle foto di riferimento.

### 2.6 La domanda fuori contesto

**Prompt permanenti.** Sì, ma non come memoria lato server: le API di chat sono senza stato, il "prompt permanente" è il messaggio di sistema inviato a *ogni* chiamata (il progetto lo fa già: `prompts/*.md` versionati, `versione_prompt` in `chiamata_ai`). Per non pagarlo ogni volta si usa il **prompt caching**: parte fissa in testa (catalogo, regole, esempi), parte variabile dopo (foto, descrizione). Indicativamente la lettura da cache costa ~10% con Anthropic (marcatori `cache_control` espliciti) e ~50% con OpenAI (automatico oltre ~1.024 token): da verificare con il provider scelto, le soglie minime del modello e se LiteLLM/OpenRouter passa i marcatori. I prompt "salvati" lato provider sono una comodità, non un risparmio, e legano al fornitore.

**Servizi con agenti.** Qui no:
- il compito è a un colpo (input noto, output a schema, nessun passaggio dipendente da risultati intermedi);
- più turni = più costo (l'immagine si rimanda) e meno determinismo;
- si perderebbe l'intercambiabilità dei modelli di `litellm`/OpenRouter;
- con il provider finto i test sono deterministici, con un agente esterno no;
- alcune API per assistenti mi risultano in dismissione (da verificare).

La chiamata non è "cieca": porta immagine, descrizione, schema, regole e, volendo, misure già calcolate. Un agente avrebbe senso solo in ciclo chiuso (l'AI guarda il risultato e corregge), e anche lì basta una seconda chiamata a schema, solo dove una guardia fallisce.

---

## 3. Piano d'azione

Un lavoro alla volta, commit in italiano all'imperativo (`feat:`, `fix:`, `test:`, `docs:`, `refactor:`, `chore:`). Il branch del worktree è `worktree-ritocco-locale-supportato-ai` (indicato dalla persona; AGENTS.md prevede `feature/<breve>` salvo diversa indicazione). Niente su `main`.

### Decisioni da prendere prima di cominciare

1. Posso usare le 4 foto come fixture nei test (opere di artigiani reali)? In alternativa: immagini sintetiche e foto ridotte.
2. Si salva il risultato della sistemazione (file per foto e canale) o si continua a ricalcolarlo a ogni richiesta?
3. L'operatore deve poter rifiutare il ritocco foto per foto? (Impatta il frontend.)
4. Quale modello di visione per la prova della fase 0.
5. R-42 nello `spec.md` va aggiornato? (Solo se la persona lo chiede.)

### Fase 0 · Prova a parte (nessun merge)

- **Obiettivo:** sapere se i modelli di visione danno angoli e riquadri abbastanza precisi, e se serve OpenCV.
- **Come:** script fuori dal codice di prodotto (o sottocomando di `cli.py` in stile `rapporto_confronto`), con il modello vero, prompt candidato `analisi_v4` (punto 4), su 4 foto + altre 26–46 di mosaici. Verità scritta a mano per ogni foto (angoli, intrusi, strategia).
- **Misure:** errore medio degli angoli in % del lato, sovrapposizione tra riquadro dell'opera e verità, accordo sulla strategia, costo reale per gruppo, quota di risposte che non passano la validazione.
- **Soglia di decisione:** errore sugli angoli ≲ 2% del lato → basta Pillow + numpy; oltre → OpenCV per raffinare.
- **Costo atteso:** pochi centesimi. **Non entra in pytest.**

### Fase 1 · numpy e catalogo con esecutore (provider finto)

- `backend/requirements.txt`: `numpy` con nome, motivo e licenza (BSD-3). Segnalato in PR come cambio di composizione.
- Nuovo modulo in `campagne` (nome da decidere, es. `ritocco.py`) con il **catalogo degli strumenti**: raddrizza (omografia con `Image.transform`), ritaglio sull'opera, esclusione degli intrusi, finestra al rapporto del canale, barre (sfocate, neutre, tinta dell'opera), misure dentro l'opera.
- `sistema_foto_buffer(…, piano=None)`: nuovo parametro; **ordine fisso** deciso dal codice: EXIF → raddrizza → ritaglio opera → inquadratura per canale → ridimensiona → autocontrasto → JPEG. Con `piano=None` il comportamento resta quello di oggi (nessuna regressione).
- Catena di trasformazioni con **mappa delle coordinate**: tutte le coordinate dell'AI sono nel riferimento dell'originale (dopo EXIF); l'esecutore le porta nel riferimento dopo ogni passo (omografia, ritaglio).
- **Guardie:** convessità e angoli del quadrilatero, area ≥ ~20%, deformazione ≤ soglia, risoluzione effettiva, quota di opera persa, colore prima/dopo. Una guardia che fallisce → si scarta quel passo, non l'intero piano.
- **Test:** immagini sintetiche con geometria nota (rettangolo inclinato su sfondo uniforme, intruso a bordo), proprietà (output sempre nel rapporto dell'intervallo, lato corto 1080, mai eccezione su input strani), regressione identica con `piano=None`.

### Fase 2 · Schema, prompt e salvataggio del piano

- `adapters/ai/schemi.py`: nuovi modelli (punto 4); validatori "morbidi" come `riquadro_valido` (un piano malformato non è un errore: l'analisi resta, senza piano).
- `adapters/ai/prompts/analisi_v4.md` (v3 resta); `litellm.py::analizza_gruppo` con `versione_prompt="analisi_v4"` e `RispostaAnalisi` aggiornata; `finto.py` con piani canned.
- `moduli/contenuti/generazione.py::_analizza`: valida e salva `analisi_ai["ritocco"]` (nessuna migrazione: è JSONB). `_CAMPI_ANALISI` aggiornato.
- Test: confronto schema ⇄ catalogo (stesso schema di `TipoFoto`), ogni strumento compare nel prompt, nuovo tentativo con violazioni.
- Dato che `analisi_ai` vecchie non hanno `ritocco`: lettura tollerante (`None` = comportamento di oggi).

### Fase 3 · Guardie complete e anteprima

- `foto_sistemata` legge `analisi_ai["ritocco"]` come già legge `soggetto_box`.
- Anteprima prima/dopo per l'operatore con interruttore "usa l'originale" per foto (decisione 3). Se serve un campo per l'override: `analisi_ai["ritocco_operatore"]`, ancora senza migrazione.
- Misure di tono dentro l'opera (esposizione, dominante), dosate dal codice entro limiti fissi.
- Se si decide di salvare il risultato (decisione 2): chiave su piano + versione del codice, invalidazione al cambio.

### Fase 4 · OpenCV (solo se la fase 0 lo richiede)

- `opencv-python-headless` in `requirements.txt` (Apache-2.0, nota sulle librerie di terzi LGPL).
- Uso **solo** per raffinare gli angoli e verificare il quadrilatero. Mai `imdecode`/`imread` su file dell'utente: Pillow decodifica, OpenCV riceve array.
- Test sui casi difficili (vetro chiaro su muro chiaro).

### Criteri di accettazione

- Con `piano=None` il risultato è byte-identico a oggi.
- L'originale non viene mai toccato (§1.3); nessun GPS né EXIF in uscita.
- Su un insieme di foto di riferimento nessun ritocco taglia più dell'opera consentita né supera le guardie.
- Foto 4: raddrizzata e inquadrata senza barre grandi. Foto 2: l'altra opera esclusa. Foto 1: muro tolto. Foto 3: invariata o migliorata.
- Costo medio per gruppo entro il +50% dell'analisi attuale (da misurare in `chiamata_ai`).
- `uv run pytest`, `black --check .`, `npm run lint`, `npm run build` verdi.

### Rischi

- Precisione geometrica dei modelli di visione (fase 0).
- Riflessi sul vetro: non risolvibili, solo segnalabili.
- Colore del prodotto: la guardia deve essere severa (ceramiche, smalti, vetri).
- Costo di calcolo a ogni richiesta se non si salva il risultato.
- Dimensione dell'immagine di deploy con OpenCV.
- Il file `analisi_ai` cresce: tenere i campi compatti.

### Note per la PR

Se cambiano composizione, `core/`, `alembic/`, `requirements.txt` o un `domain.py`, scriverlo nella PR. Qui: nuove dipendenze (numpy, forse OpenCV), nuovi file in `adapters/ai` e `campagne`, versione del prompt `analisi_v4`. Nessuna modifica prevista a `alembic/` né a `docs/archivio/`.

---

## 4. Esempio di prompt e output strutturato (punto di partenza dal codice presente)

> **Superata dalle sezioni 9 e 10.** Lo schema qui sotto è pensato per i mosaici (`opera` con quattro angoli). Il caso d'uso largo (sezione 5) ha pochissime opere piane: lo schema è stato generalizzato. Il testo resta come storia.

Partenza: `analisi_v3.md` (elenco di campi per foto), `AnalisiFoto` con `SoggettoBox` e `riquadro_valido`, `RispostaAnalisi`, chiamata via `self._chiama("analisi", modello, messaggi, RispostaAnalisi, versione_prompt=…)`. L'esempio **estende** v3: i campi esistenti restano, si aggiungono `inquadratura` e `tono`.

### 4.1 Schema (in `adapters/ai/schemi.py`)

```python
class Punto(BaseModel):
    x: float
    y: float


class Quadrilatero(BaseModel):
    """I quattro angoli dell'opera, in senso orario dall'alto a sinistra."""

    alto_sx: Punto
    alto_dx: Punto
    basso_dx: Punto
    basso_sx: Punto


class Intruso(BaseModel):
    """Qualcosa di estraneo all'opera che entra nell'inquadratura."""

    box: SoggettoBox
    che_cosa: Literal["altra_opera", "cornice", "oggetto", "persona"]


class Inquadratura(BaseModel):
    opera: Quadrilatero | None           # i 4 angoli dell'opera; None se non c'è un'opera piana riconoscibile
    opera_piana: bool                    # vero solo per pannelli e quadri
    prospettiva: Literal["frontale", "obliqua_lieve", "obliqua_forte"]
    intrusi: list[Intruso] = Field(max_length=4)
    centro_interesse: Punto | None       # il punto da non perdere se si taglia
    preferenza: Literal["opera_intera", "ritaglio_ammesso"]
    barre: Literal["sfocate", "neutre", "tinta_opera"]


class Tono(BaseModel):
    esposizione: Literal["ok", "scura", "chiara"]
    dominante: Literal["nessuna", "calda", "fredda", "verde", "magenta"]
    gravita: Literal["lieve", "media"]
    riflessi: bool                        # riflessi sul vetro: si segnalano, non si correggono


class AnalisiFoto(BaseModel):
    # ... campi di oggi (foto_id, soggetto, descrizione, tipo, idonea, motivo,
    #     punteggio, simile_a, soggetto_box, persone_riconoscibili, marchi_visibili) ...
    inquadratura: Inquadratura | None
    tono: Tono | None

    @field_validator("inquadratura", mode="before")
    @classmethod
    def _inquadratura_sensata(cls, valore):
        # Come riquadro_valido: un riquadro o un quadrilatero fuori misura non è un
        # errore, l'analisi resta e il campo vale None.
        return inquadratura_valida(valore)
```

`inquadratura_valida` controlla: tutti i punti in 0–1, quadrilatero convesso, angoli tra 60° e 120°, area ≥ 20% della foto, al massimo 4 intrusi, `opera_piana` falso se non c'è `opera`. Qualunque violazione → `None`.

### 4.2 Aggiunte al prompt (`analisi_v4.md`, dopo `soggetto_box` e prima delle regole)

```text
- `inquadratura`: serve a chi prepara la foto per Facebook e Instagram. Riguarda solo la geometria, non la bellezza. Se la foto non mostra un'opera piana (un pannello, un quadro, una lastra) o non sei sicuro, scrivi `null`.
  - `opera`: i quattro angoli dell'opera, ognuno come `{"x", "y"}` da 0 a 1 rispetto alla foto che vedi, origine in alto a sinistra, nell'ordine `alto_sx`, `alto_dx`, `basso_dx`, `basso_sx`. L'opera è solo ciò che l'artigiano ha realizzato: muro, cornice altrui, mensole, battiscopa e altre opere non ne fanno parte. Se un angolo è coperto o fuori campo, scrivi `null` per tutta `opera`.
  - `opera_piana`: `true` solo se l'opera è una superficie piana (si può raddrizzare senza deformarla). Per oggetti con volume scrivi sempre `false`.
  - `prospettiva`: `frontale` se i bordi sono quasi paralleli ai bordi della foto; `obliqua_lieve` se convergono poco; `obliqua_forte` se la foto è ripresa chiaramente di lato.
  - `intrusi`: aree della foto che non vanno mostrate perché appartengono ad altro (un'altra opera che entra nel campo, una cornice altrui, un oggetto, una persona di passaggio), ognuna con `box` (stesse coordinate di `soggetto_box`) e `che_cosa`. Massimo quattro; lista vuota se non ce ne sono.
  - `centro_interesse`: il punto che non deve mai essere tagliato se la foto va ritagliata (un viso, il fiore principale, il centro del disegno); `null` se non c'è.
  - `preferenza`: `opera_intera` se tagliare farebbe perdere una parte importante dell'opera; `ritaglio_ammesso` se un taglio ai bordi non toglie nulla di essenziale. Nel dubbio, `opera_intera`.
  - `barre`: come riempire i lati se la foto va portata in proporzione senza tagliare: `sfocate` (la foto stessa sfocata), `neutre` (tinta unita neutra, per opere molto colorate), `tinta_opera` (tinta unita presa dal colore dominante dell'opera).
- `tono`: come appare la foto, senza numeri. `esposizione` (`ok`, `scura`, `chiara`), `dominante` (`nessuna`, `calda`, `fredda`, `verde`, `magenta`), `gravita` (`lieve`, `media`; usa `media` solo se il difetto si vede subito), `riflessi` (`true` se vetro o superfici lucide riflettono finestre o luci). Giudica il colore dell'**opera**, non quello del muro o dello sfondo: un muro rosa non rende l'opera calda. Un'opera volutamente scura o monocromatica ha `esposizione: "ok"`.

Regole in più:
- Non calcolare ritagli né proporzioni: dici dove sono le cose, a ritagliare ci pensa il programma.
- Non inventare ciò che non vedi: se non sei sicuro di un angolo, `inquadratura: null`.
- Nel dubbio, nessuna correzione: `esposizione: "ok"`, `dominante: "nessuna"`.
```

Il resto di `analisi_v3` (ruolo, formato «Foto <id>:», `idonea`, `punteggio`, `simile_a`, …) resta com'è. Il testo della versione porta `versione_prompt="analisi_v4"`, quindi la versione si legge in `chiamata_ai`.

### 4.3 Contesto aggiunto dal codice alla richiesta

Subito dopo la descrizione del gruppo, un blocco JSON come quello già inviato (`descrizione_del_gruppo`, `da_usare_il`), esteso per foto con ciò che il codice sa senza AI:

```json
{
  "descrizione_del_gruppo": "Mosaici in vetro e marmo, pezzi unici",
  "da_usare_il": null,
  "foto_note": [
    {"foto_id": 41, "larghezza": 1129, "altezza": 2000, "rapporto": 0.56},
    {"foto_id": 42, "larghezza": 2000, "altezza": 1126, "rapporto": 1.78}
  ],
  "intervallo_proporzioni_canali": {"min": 0.8, "max": 1.91}
}
```

### 4.4 Esempio di risposta (illustrativo: coordinate stimate a occhio, non misurate)

Foto 41 = pannello di vetro ripreso di tre quarti (foto 4 della cronologia). Foto 42 = calle bianche con un'altra opera che entra da destra (foto 2).

```json
{
  "foto": [
    {
      "foto_id": 41,
      "soggetto": "Pannello in vetro con due figure astratte abbracciate in rosso, blu, nero e bianco",
      "descrizione": "Mosaico in vetro dai contorni morbidi: due figure stilizzate si abbracciano, con tagli netti di rosso, blu cobalto, nero e bianco su un fondo a riquadri chiari e scuri. La luce cade sulla superficie lucida con qualche riflesso. Il pannello è appeso a un muro chiaro.",
      "tipo": "pezzo_finito",
      "idonea": true,
      "motivo": null,
      "punteggio": 4,
      "simile_a": null,
      "soggetto_box": {"x": 0.06, "y": 0.04, "larghezza": 0.91, "altezza": 0.81},
      "persone_riconoscibili": false,
      "marchi_visibili": false,
      "inquadratura": {
        "opera": {
          "alto_sx": {"x": 0.06, "y": 0.04},
          "alto_dx": {"x": 0.97, "y": 0.075},
          "basso_dx": {"x": 0.96, "y": 0.86},
          "basso_sx": {"x": 0.07, "y": 0.81}
        },
        "opera_piana": true,
        "prospettiva": "obliqua_forte",
        "intrusi": [],
        "centro_interesse": {"x": 0.52, "y": 0.42},
        "preferenza": "opera_intera",
        "barre": "neutre"
      },
      "tono": {
        "esposizione": "ok",
        "dominante": "nessuna",
        "gravita": "lieve",
        "riflessi": true
      }
    },
    {
      "foto_id": 42,
      "soggetto": "Mosaico di calle bianche in un vaso rosa su fondo azzurro",
      "descrizione": "Un mazzo di calle bianche con steli e foglie verdi esce da un vaso rosa a tessere sfumate. Lo sfondo è azzurro con linee viola, in basso una fascia ocra e marrone. La superficie è lucida e riflette finestre.",
      "tipo": "pezzo_finito",
      "idonea": true,
      "motivo": null,
      "punteggio": 4,
      "simile_a": null,
      "soggetto_box": {"x": 0.05, "y": 0.04, "larghezza": 0.83, "altezza": 0.9},
      "persone_riconoscibili": false,
      "marchi_visibili": false,
      "inquadratura": {
        "opera": {
          "alto_sx": {"x": 0.005, "y": 0.0},
          "alto_dx": {"x": 0.87, "y": 0.0},
          "basso_dx": {"x": 0.87, "y": 0.98},
          "basso_sx": {"x": 0.005, "y": 0.98}
        },
        "opera_piana": true,
        "prospettiva": "frontale",
        "intrusi": [
          {
            "box": {"x": 0.88, "y": 0.0, "larghezza": 0.12, "altezza": 0.64},
            "che_cosa": "altra_opera"
          }
        ],
        "centro_interesse": {"x": 0.43, "y": 0.5},
        "preferenza": "ritaglio_ammesso",
        "barre": "sfocate"
      },
      "tono": {
        "esposizione": "ok",
        "dominante": "nessuna",
        "gravita": "lieve",
        "riflessi": true
      }
    }
  ]
}
```

### 4.5 Cosa ne fa il codice (senza AI)

Foto 41:
1. Valida il quadrilatero (convesso, angoli ~80–100°, area ≥ 20%).
2. Con `opera_piana` e `prospettiva: obliqua_forte` calcola l'omografia e raddrizza; confronta il rapporto ottenuto con quelli plausibili (3:4, 4:5): se la differenza supera la soglia, non raddrizza.
3. Porta il rapporto al target del canale: opera ~3:4 → 4:5, taglio piccolo, nessuna barra grande (`barre` serve solo se il taglio supera la soglia).
4. Lato corto a 1080, tono misurato dentro l'opera (`dominante: nessuna` → niente correzione), JPEG.

Foto 42:
1. Il rapporto 1,78 è in intervallo: oggi non si farebbe niente.
2. Con `intrusi`, calcola la finestra di ritaglio al rapporto richiesto che **esclude** il riquadro (x ≥ 0,88), centrata su `centro_interesse` entro l'opera: l'altra opera sparisce.
3. Controlla la risoluzione effettiva: se il ritaglio scende sotto il minimo o richiede un ingrandimento troppo forte, si lascia più margine.

Se un controllo fallisce, si scarta quel passo (o l'intero piano) e si torna al comportamento di oggi.

### 4.6 Come si collega al codice presente

| Cosa | Dove |
|---|---|
| Prompt | `backend/app/adapters/ai/prompts/analisi_v4.md` (v3 resta) |
| Schemi e validatori | `backend/app/adapters/ai/schemi.py` |
| Chiamata e mappatura nel dict di analisi | `backend/app/adapters/ai/litellm.py::analizza_gruppo` |
| Provider finto | `backend/app/adapters/ai/finto.py` |
| Salvataggio del piano | `backend/app/moduli/contenuti/generazione.py::_analizza` (campi in `_CAMPI_ANALISI`) |
| Lettura e uso | `backend/app/moduli/campagne/service.py::foto_sistemata` → `sistema_foto_buffer` |
| Esecutore e catalogo | `backend/app/moduli/campagne/` (nuovo modulo) e `sistemazione_foto.py` |

---

## 5. Il caso d'uso largo: le 375 foto della PR #189

### 5.1 Il materiale

La PR #189 (`docs/prove-reali/`) descrive 15 profili fittizi di piccole attività del Lazio. Ognuno ha 25 foto da raccogliere, con i difetti attesi e l'uso previsto: in tutto **375 foto**. Sono descrizioni, non foto: i numeri sotto contano i difetti dichiarati, non quelli misurati.

Attività: panificio, pasticceria, due pizzerie, falegname, sarta, idraulico, calzolaio, ceramista, fioraio, oggettistica, vineria, alimentari, estetista, toelettatura.

| Difetto | Foto | Profili | | Difetto | Foto | Profili |
|---|---|---|---|---|---|---|
| riflessi | 75 | 15 | | controluce | 23 | 13 |
| persone | 74 | 15 | | zoom | 23 | 14 |
| disordine | 62 | 15 | | flash | 22 | 10 |
| testo | 56 | 15 | | buona | 21 | 15 |
| luce mista (+ fredda) | 40 | 15 | | sfocata | 16 | 11 |
| scura | 31 | 11 | | screenshot | 14 | 14 |
| mossa | 31 | 14 | | decentrata | 12 | 9 |
| sbilenca | 30 | 15 | | sovraesposta | 11 | 10 |
| lontana | 30 | 15 | | compressa | 10 | 10 |

- **Combinazioni:** 156 foto con un difetto, 215 con due, 4 con tre.
- **Usi previsti:** post 125, storia 90, copertina 44, evento 40, offerta 33, prima/dopo 21, caso limite 19, prodotto 3.
- **Cosa cambia rispetto ai mosaici:** le opere piane sono quasi assenti. I soggetti sono cibo, persone, ambienti, cartelli, prodotti dietro un vetro. La geometria non ruota più attorno a "l'opera con quattro angoli" ma attorno al **soggetto**, con la superficie piana come caso particolare (lavagna, cartello, volantino, foto rifotografata, pannello).

### 5.2 Formati feed

Pubblicando **via API**, la strada di AdFlow, il feed accetta da 4:5 a 1,91:1 sia su Facebook sia su Instagram. Il 3:4 risulta accettato solo pubblicando dall'app di Instagram: via API un 3:4 torna con un errore (codice 36003, sottocodice 2207009). Le fonti sono siti di terze parti: va confermato sulla documentazione Meta. Ne segue l'**intervallo unico** della sezione 0.

La regola "rapporto più vicino" è già quella del codice (`_ratio_target`): dentro l'intervallo il rapporto resta, fuori si va al bordo più vicino.

| Formato della foto | Rapporto | Risultato | Taglio per il rapporto |
|---|---|---|---|
| 1:1, 4:3, 3:2, 16:9 orizzontali | 1–1,78 | invariato | 0% |
| 3:4 verticale (il più comune) | 0,75 | → 4:5 | 6,25% |
| 9:16 verticale | 0,56 | → 4:5 | 29,7%: solo con il soggetto (soglia 35%), altrimenti barre |
| screenshot 9:19,5 | 0,46 | → 4:5 | 42%: sempre barre |

Con la decisione dell'8 novembre si aggiunge il **ritaglio di avvicinamento**: anche dentro l'intervallo la finestra può stringersi sul soggetto, mantenendo lo stesso rapporto (sezione 7.5).

### 5.3 Lista ragionata delle correzioni

Esiti possibili:
- **Tratta:** correzione automatica nella proposta, deterministica, a basso rischio.
- **Prudente:** nella proposta ma lieve, con tetto.
- **Segnala:** misura e avviso all'operatore, nessuna correzione.
- **Fuori:** eccessiva per il progetto.

**Geometria** (131 foto, 35%)

| Correzione | Difetti coperti | Esito | Chi decide che cosa |
|---|---|---|---|
| Rapporto feed (5.2) | verticale, storia | Tratta (esiste) | codice |
| Ritaglio di avvicinamento sul soggetto, anche in intervallo | lontana 30, decentrata 12 | Tratta | AI: soggetto e centro d'interesse. Codice: finestra allo stesso rapporto, senza ingrandire oltre il limite |
| Esclusione del disordine ai bordi | disordine 62 | Tratta (solo ai bordi) | AI: riquadri degli intrusi. Il disordine attorno al soggetto resta |
| Rotazione fine (orizzonte, verticali) | sbilenca 30 | Tratta | AI: storta sì/no/voluto. Codice: angolo misurato sulle linee |
| Prospettiva delle superfici piane | lavagne, cartelli, listini, volantini (~12), foto rifotografate (3) | Tratta | AI: superficie e candidato. Codice: affina gli angoli e raddrizza |
| Testo da preservare | testo 56 | Tratta, come vincolo | AI: riquadri del testo leggibile. Il ritaglio non lo taglia |
| Distorsione del grandangolo (bagni stretti) | pochi (profilo 07) | Fuori | serve il profilo dell'obiettivo; i telefoni la correggono già |

**Luce e colore** (125 foto, 33%)

| Correzione | Difetti coperti | Esito | Note |
|---|---|---|---|
| Profilo colore → sRGB | tutte le foto con profilo ICC (iPhone: Display P3) | Tratta, obbligatoria | Oggi il profilo si perde: colori spenti |
| Togliere l'autocontrasto per canale | tutte, comprese le 21 buone | Tratta, obbligatoria | `ImageOps.autocontrast(cutoff=2)` senza `preserve_tone` allunga ogni canale da solo: sposta il colore e taglia il 2% per canale. Va sostituito da una correzione di luminosità misurata, con zona morta e tetto |
| Esposizione | scura 31, sovraesposta 11 | Tratta | Curva sulla luminanza, misurata nel soggetto. Tetto più basso con ISO alto. Le luci bruciate non si recuperano |
| Bilanciamento del bianco | luce mista 38, fredda 2 | Prudente | Solo con un **riferimento neutro** indicato dall'AI. Senza, nessuna correzione (la carta da forno non è neutra) |
| Ombre (controluce) | controluce 23 | Prudente | Schiarita con maschera di luminanza; la silhouette estrema resta |
| Flash | flash 22 | Prudente | Compensa la caduta di luce verso i bordi; il punto caldo si attenua appena |
| Saturazione, vivacità | – | Fuori | Fioraio e ceramista: i colori sono il prodotto |

**Privacy** (73 foto, 19,5%), come **proposta all'operatore**

| Caso | Esempi | Proposta |
|---|---|---|
| Titolare o staff in posa | "Rosa e Matteo dietro il bancone" | nessuna |
| Mani, persona di spalle | "mani che stendono la frolla" | nessuna |
| Clienti, passanti | "coda di studenti", "sala piena" | zona da oscurare, oppure ritaglio se sono ai bordi |
| Minori | "lavoretti dei bambini" | zona da oscurare, avviso forte |
| Testo privato | nome della bambina sulla torta, biglietti con nomi, indirizzo sul pacco, targhe | zona da oscurare |

**Da segnalare, non da correggere**

| Difetto | Foto | Che cosa si fa |
|---|---|---|
| riflessi | 75 | Esclusi dal ritaglio se ai bordi; avviso "riflessi sul soggetto"; `simile_a` per preferire un altro scatto |
| mossa, sfocata | 47 | Misura di nitidezza nel soggetto; l'AI dice se il movimento è voluto (fuoco, phon, segatura) |
| zoom, compressa | 33 | Misura della qualità; la nitidezza finale si spegne (amplifica gli artefatti) |
| screenshot | 14 | Nessun ritocco, barre neutre, avviso |
| diritti di terzi | 2 | Avviso (spec: motivo di respingimento) |
| vapore, polvere | 3 | Fuori |

**Trasversali:** nitidezza dopo il ridimensionamento (Prudente, condizionata); coerenza prima/dopo (Prudente, fase successiva: stessa correzione su entrambe o nessuna, mai migliorare solo il "dopo").

**Fuori dal progetto:** ritocco generativo (riflessi, vapore, disordine interno, cielo), recupero del mosso, super-risoluzione, antirumore aggressivo, ritocco di pelle e viso, collage, formato copertina.

### 5.4 Il target

| Livello | Correzioni |
|---|---|
| **Obbligatorie** (ogni foto, senza AI) | sRGB, via l'autocontrasto per canale, rapporto feed, lato corto 1080, JPEG senza metadati |
| **Livello 1** (proposta) | avvicinamento, esclusione del disordine ai bordi, testo da preservare, rotazione fine, prospettiva delle superfici piane, esposizione, privacy proposta, avvisi di qualità |
| **Livello 2** | bianco con riferimento neutro, ombre, flash, nitidezza condizionata, riflessi ai bordi esclusi, coerenza prima/dopo |

Copertura stimata sui difetti dichiarati:

| | Foto | Quota |
|---|---|---|
| Almeno una correzione utile (privacy compresa) | 259 | 69% |
| Almeno una correzione di geometria o luce | 228 | 61% |
| Solo difetti da segnalare o testo | 95 | 25% |
| Buone, da lasciare **visibilmente uguali** | 21 | 5,6% |

Test di accettazione principale: le 21 foto buone e il profilo 09 (ceramista, "migliorare poco e non rovinare"). Ogni correzione ha una zona morta (sotto soglia non fa nulla), un tetto e un controllo che il colore del soggetto non si sposti oltre una soglia.

---

## 6. Il flusso oggi (dal codice, 9 novembre)

### 6.1 Le tappe

1. **Caricamento** (`campagne/immagini.py`): controlli, originale salvato byte per byte.
2. **Invio della campagna** → worker, generazione a tappe (`contenuti/generazione.py`).
3. **Tappa ANALISI** (`_analizza`): per ogni gruppo, le foto con `analisi_ai is None`, **una chiamata** `analizza_gruppo` con tutte le foto del gruppo (fino a 20). `_foto_per_ai` decodifica l'originale, EXIF, RGB, 1024 px, JPEG q85, `detail: high`. Il risultato va in `foto.analisi_ai` (`_CAMPI_ANALISI`). Un'analisi resta per sempre: la stessa foto riusata in un'altra campagna non si rianalizza.
4. **Piano e testi:** al piano arrivano solo `soggetto`, `descrizione`, `tipo`, `punteggio`, `motivo` (`litellm.py::_valutazione`).
5. **Revisione** (Vedi campagna): interventi di R-16 (modifica, rigenera, rigenera immagine, cambia foto, sposta), ognuno è una versione del post (`VersionePost`, `VersionePostFoto`).
6. **Pubblicazione** (`pubblicazione/service.py:137`): Facebook riceve i byte di `foto_sistemata(...)`; Instagram scarica `GET /foto/{id}/pubblica`, che **rifà la sistemazione a ogni richiesta**.

### 6.2 Che cosa non torna

| # | Scoperta | Dove | Peso |
|---|---|---|---|
| a | **L'operatore vede l'originale**, non la foto che esce. Il commento dice "L'immagine intera, come esce", ma la `src` è `/api/foto/{id}/file`. Ritaglio, barre e autocontrasto non si vedono mai prima della pubblicazione | `frontend/src/pages/operatore/campagna/PostCard.tsx` | Alto: oggi l'operatore approva una foto diversa da quella pubblicata |
| b | La proporzione forzata (`1:1`, `4:5`) esiste in `sistema_foto_buffer` e `foto_sistemata`, ma nessuna rotta la passa | `campagne/service.py`, `router.py` | Medio: R-42 "si possono ancora forzare a mano" non è raggiungibile |
| c | Autocontrasto per canale su ogni foto | `sistemazione_foto.py`, passo 5 | Alto sulle foto buone |
| d | Profilo ICC perso | `sistemazione_foto.py`, `_foto_per_ai` | Medio, su tutte le foto da iPhone |
| e | La sistemazione si ricalcola a ogni pubblicazione e a ogni download di Meta: se il codice cambia tra approvazione e pubblicazione, cambia la foto | `foto_sistemata` | Medio |
| f | Lo spec (§2.2) mette "foto sistemate" tra le tappe della generazione; nel codice non c'è, si sistema solo in pubblicazione | `docs/agenti/spec.md` | Documentazione |
| g | `finto.py` dà `punteggio: 0.8`, lo schema vuole un intero da 1 a 5 | `adapters/ai/finto.py` | Basso (test) |
| h | Il prompt di sistema `analisi_v3` è sotto i 1.024 token: la cache automatica del provider non scatta, nessuno sconto | `prompts/analisi_v3.md` | Basso oggi, utile con v4 |
| i | `persone_riconoscibili` e `marchi_visibili` sono salvati ma non usati | `_CAMPI_ANALISI` | – |
| j | Prezzi di configurazione 2,50 $ / 10 $ per milione (gpt-4o via OpenRouter); la sezione 2.5 usava 3 / 15 | `backend/.env.example` | I costi della 9.9 usano i prezzi della configurazione |
| k | R-42 dice "da 4:5 a 1,91:1 nessun taglio" e "mai deformata": contraddice le decisioni dell'8 novembre (avvicinamento, raddrizzamento) | `docs/agenti/spec.md` | Da aggiornare se la persona lo chiede |
| l | Il `.venv` locale aveva Pillow 12.3.0, `requirements.txt` fissa 13.0.0 | ambiente | Basta `allinea.py` |

---

## 7. Il flusso proposto: locale → AI → locale → operatore → pubblicazione

### 7.1 Lo schema

```text
caricamento (sincrono, invariato: nessun costo in più per l'artigiano)
   │
worker · tappa ANALISI (per gruppo)
   ├─ L1  pre-analisi locale, per foto, una decodifica     → misure e candidati
   ├─ AI  UNA chiamata per gruppo (analisi_v4)             → descrizione + diagnosi
   └─ L2  verifica locale: validatori, doppia chiave       → foto.analisi_ai (+ "locale", "ritocco")
   │
piano e testi (invariati: all'AI arrivano gli stessi campi di oggi)
   │
revisione · operatore
   ├─ anteprima = render della proposta (L3 in anteprima, locale)
   └─ "Ritocca": scelte discrete → versione nuova del post (ritocca_foto), nessuna AI
   │
approvazione → L3 render definitivo, salvato
   │
pubblicazione → si serve il file salvato (Facebook: byte; Instagram: URL firmato)
```

Il principio: **l'AI parla una volta, il codice fa tutto il resto**. Tutto ciò che viene dopo la chiamata (proposta, alternative, anteprime, scelte dell'operatore, render) è calcolo locale e quindi gratuito.

### 7.2 L1 · Pre-analisi locale

Dove: nella tappa ANALISI, prima della chiamata, solo per le foto `da_fare`. Non al caricamento, per non rallentare l'artigiano.

Per ogni foto, **una sola decodifica**, con Pillow (unico decoder: nota 2.2):
1. Limiti di oggi (36 MP), `draft()` per i JPEG: la decodifica ridotta in DCT dà direttamente una copia di ~2048 px, molto più veloce.
2. EXIF (orientamento), poi **sRGB** dal profilo ICC (`ImageCms`).
3. Due copie: **copia AI** (1024 px, JPEG q85: è quella che oggi fa `_foto_per_ai`, che va unificata qui) e **copia di lavoro** (~2048 px) per misure e candidati.
4. **Misure** (numpy), sul fotogramma intero: nitidezza (varianza del Laplaciano, normalizzata), percentili di luminanza, quota di luci bruciate e ombre chiuse, dominante (medie di a* e b* in Lab), caduta di luce centro-bordi, angolo delle linee dominanti, qualità JPEG stimata dalle tabelle di quantizzazione.
5. **Fatti dall'EXIF dell'originale:** flash scattato, ISO, zoom digitale, presenza di fotocamera e software (aiuta a riconoscere screenshot e foto scaricate).
6. **Candidati** (OpenCV, fase 4 della sezione 3): possibili **volti** (`V1`, `V2`…) e possibili **quadrilateri** (`Q1`…). A 2048 px il programma trova volti che a 1024 px l'AI vede a malapena (una coda di clienti, una sala piena). I candidati si congelano con l'analisi: un `V2` resta quel volto per sempre.
7. Se la fase 0 lo conferma, i candidati si **disegnano sulla copia AI** come riquadri sottili con etichetta (9.6).

Uscita: `analisi_locale` (10.3). Costo: solo CPU, ordine di frazioni di secondo per foto (da misurare).

### 7.3 AI · Una chiamata per gruppo

Invariata nella forma: `analizza_gruppo`, un messaggio di sistema (`analisi_v4.md`), un messaggio utente con il contesto del gruppo, poi per ogni foto la riga «Foto <id>:», il contesto misurato e l'immagine. Dettagli nella sezione 9.

- **Una chiamata, anche per un gruppo da una foto** (R-46): stesso prompt.
- **Nessun secondo tentativo per errori morbidi**: un campo di ritocco fuori misura vale `None` e la proposta si fa senza (perimetro del costo).
- Gli errori duri (schema, foto mancanti) seguono R-35 come oggi.

### 7.4 L2 · Verifica locale

Tre livelli, in ordine:
1. **Schema** (Pydantic, come oggi): se non passa, errore `risposta` (R-35).
2. **Validatori morbidi** per campo, come `riquadro_valido`: riquadri dentro la foto, punti in 0–1, quadrilatero convesso con angoli plausibili, codici candidato esistenti, liste troncate. Un campo che non passa vale `None` o lista vuota, l'analisi resta.
3. **Doppia chiave** (10.7): una correzione di luce o di geometria entra nella proposta solo se **l'AI dice che è un difetto** e **la misura lo conferma**. La dose la decide la misura. Così una vineria buia per scelta (AI: `esposizione: ok`) non si schiarisce, e un'AI che vede scuro per errore (misura normale) non tocca nulla.

Uscita: la **diagnosi verificata**, salvata in `foto.analisi_ai["ritocco"]` (10.8). La **proposta** non si salva: è una funzione pura della diagnosi e della versione del codice (10.9).

### 7.5 L3 · Esecutore (anteprima e render)

Un solo esecutore, la stessa funzione per anteprima e pubblicazione. **Ordine fisso**, deciso dal codice:

| # | Passo | Perché qui |
|---|---|---|
| 1 | Decodifica Pillow, limiti | unico decoder |
| 2 | EXIF, poi sRGB | tutte le coordinate dell'AI sono in questo riferimento |
| 3 | Rotazione di 90° scelta dall'operatore | le coordinate si ruotano con la foto |
| 4 | **Privacy**: sfocatura forte delle zone attive | prima della geometria: le coordinate sono quelle dell'originale, nessuna conversione, e la sfocatura segue ogni passo dopo |
| 5 | Raddrizzamento: prospettiva della superficie piana, oppure rotazione fine; ritaglio dei bordi vuoti | la finestra si calcola sulla foto già dritta |
| 6 | **Finestra**: rapporto più vicino nell'intervallo, contenendo soggetto e testo da tenere, evitando gli intrusi, centrata sul centro d'interesse; barre se serve | regole sotto |
| 7 | Lato corto 1080 | le misure di tono costano meno |
| 8 | Luce: esposizione, bianco, ombre, flash, misurati nella regione del soggetto | dosi dalla diagnosi |
| 9 | Nitidezza leggera, se ammessa | solo dopo il ridimensionamento |
| 10 | JPEG q90, sRGB, nessun metadato | come oggi |

Regole della finestra (passo 6), da tarare:
- **Rapporto:** quello della foto se è nell'intervallo, altrimenti il bordo più vicino.
- **Avvicinamento:** la finestra più piccola, con quel rapporto, che contiene soggetto e testo da tenere più un margine (~8%).
- **Limite di risoluzione:** il lato corto della finestra non scende sotto 1080 px della foto originale (nessun ingrandimento; al massimo ~1,3× se si decide di ammetterlo).
- **Contesto `ambiente`:** avvicinamento limitato (es. al più il 15% dell'area); con `preferenza: intera` nessun avvicinamento.
- **Intrusi:** si sposta la finestra per escluderli, senza mai tagliare soggetto e testo.
- **Soglie di oggi** (35% con soggetto, 10% senza) valgono per il taglio dovuto al rapporto; l'avvicinamento ha la sua soglia.

### 7.6 Approvazione e pubblicazione

- All'**approvazione** il piano effettivo di ogni foto (10.11) si rende **una volta** e si salva come file derivato nell'archivio (l'originale non si tocca, §1.3), con una chiave che è l'impronta del piano più la versione dell'esecutore.
- La **pubblicazione** serve quel file: Facebook i byte, Instagram un URL firmato che punta al file salvato. Ciò che l'operatore ha visto è ciò che esce (6.2 a, e).
- Un intervento dopo l'approvazione (R-16: attiva o sospesa, almeno 15 minuti prima) crea una versione nuova, quindi un render nuovo.

### 7.7 Ottimizzazioni

| # | Ottimizzazione | Guadagno |
|---|---|---|
| O1 | Una decodifica per foto in L1, con `draft()` | CPU: la decodifica di un 12 MP è la voce più cara |
| O2 | L1 nel worker, non al caricamento | nessun ritardo per l'artigiano |
| O3 | Una chiamata per gruppo, come oggi | nessun costo in più per chiamate |
| O4 | Prompt di sistema fisso in testa, sopra i 1.024 token | cache automatica del provider sul prefisso (9.7) |
| O5 | Uscita compatta: enum, liste vuote, `null`, nessun testo libero nuovo, coordinate a tre decimali | i token di uscita costano 4 volte quelli di ingresso |
| O6 | `persone_riconoscibili` derivato in L2 dai volti, non chiesto all'AI | meno uscita |
| O7 | Candidati come codici (`V1`, `Q1`) invece di coordinate | meno uscita e più precisione |
| O8 | Nessun nuovo tentativo per errori morbidi | perimetro del costo |
| O9 | Al piano gli stessi campi di oggi | la seconda chiamata non cresce |
| O10 | Proposta calcolata, non salvata; alternative solo quando l'operatore apre il pannello | nessun lavoro per le foto che nessuno guarda |
| O11 | Render salvato all'approvazione | oggi si risistema a ogni download di Meta |
| O12 | Analisi e pre-analisi persistenti con la foto | riuso tra campagne senza AI |

### 7.8 Che cosa resta uguale

Caricamento e controlli, tappe della generazione, piano e testi, validatore dei testi, regole di R-16 sugli stati, originale intatto, Pillow come unico decoder.

---

## 8. L'operatore

### 8.1 Principi

1. **Zero clic nel caso normale.** Se la proposta va bene, l'operatore non fa niente.
2. **Vede ciò che esce.** L'anteprima del post è il render, non l'originale (6.2 a).
3. **Scelte discrete**, non cursori: poche posizioni, deterministiche, facili da provare e da testare.
4. **Tutto locale e gratuito.** Nessuna scelta fa partire l'AI (spec 2.3: "Nessuna modifica fa partire l'AI da sola").
5. **Ogni scelta è una versione** del post, con autore (R-02), come gli altri interventi.
6. **L'originale non si tocca** (§1.3): le scelte producono solo file derivati.
7. **L'analisi del ritocco alimenta le azioni che esistono già:** una foto mossa o con riflessi sul soggetto porta a "Cambia foto" o a "Chiedi all'artigiano" (R-46), non a un ritocco.

### 8.2 Nella card del post

- **Anteprima:** il render della versione corrente (proposta o scelta dell'operatore).
- **Una riga di etichette** sotto la foto: cosa è stato fatto ("Ritagliata · Raddrizzata · Luce +1") e gli avvisi ("2 zone privacy da decidere", "Riflessi sul soggetto", "Foto mossa", "Screenshot").
- Un pulsante **Ritocca**, accanto agli interventi di oggi (`AzioniPost.tsx`).
- Tenendo premuto sull'anteprima si vede l'originale (confronto prima/dopo, gratuito).

### 8.3 Il pannello Ritocca

> **Superata dalla 12.4** (decisione del 9 novembre): niente pannello con molti controlli, ma tre varianti a un clic più la privacy. Il testo resta come storia.

Un cassetto (Mantine `Drawer`) con l'anteprima grande e questi controlli:

| Controllo | Valori | Predefinito | Compare |
|---|---|---|---|
| Inquadratura | Proposta · Foto intera · A mano | Proposta | sempre |
| A mano | rettangolo vincolato all'intervallo 4:5–1,91:1, trascinabile; un clic sull'anteprima sposta il centro | – | con "A mano" |
| Ruota di 90° | 0 · 90 · 180 · 270 | 0 | sempre (le foto passate da WhatsApp perdono l'EXIF) |
| Raddrizza | sì · no | come proposta | solo se proposto |
| Esposizione | −1 · Auto · +1 (passi rispetto alla proposta) | Auto | sempre |
| Colore | Auto · spento | Auto | se c'è una correzione del bianco |
| Ombre | Auto · spento | Auto | se proposta |
| Zone privacy | una riga per zona, con miniatura e interruttore | **spento** (proposta) | se ci sono zone |
| Aggiungi zona | rettangolo da disegnare | – | sempre |
| Solo l'essenziale | solo le correzioni obbligatorie (5.4) | – | sempre |
| Ripristina la proposta | – | – | se ci sono scelte |
| Applica anche all'altro canale | sì · no | sì | se la stessa foto è in un post dell'altro canale |

**Salva** crea una versione `ritocca_foto` del post (e dell'altro post, se richiesto). Il testo della versione resta quello di prima.

### 8.4 Privacy come proposta

Le zone proposte sono **spente** finché l'operatore non le attiva (decisione dell'8 novembre). Per non appesantire il flusso:
- Le zone non decise compaiono come **avviso** nella card, con lo stesso meccanismo degli avvisi del validatore (non è un blocco: R-21 distingue già avviso e blocco).
- Nel dialogo di **Approva** compare un riepilogo: "3 foto con 5 zone privacy da decidere · [Oscura tutte] [Rivedi]". Un clic per tutta la campagna.
- Una zona `volto_minore` porta un avviso più forte.

Da decidere: il riepilogo in Approva è solo informativo o chiede una conferma esplicita? Proposta: conferma esplicita, un clic.

### 8.5 Interventi e stati

- Nuovo intervento `RITOCCA_FOTO` in `INTERVENTI_AMMESSI` (`contenuti/domain.py`), negli stessi stati di `CAMBIA_FOTO`: in revisione su `da_approvare`, in attiva o sospesa su `approvato` almeno 15 minuti prima dell'uscita.
- Dopo l'approvazione la versione dell'operatore nasce approvata (R-16), e all'approvazione si rifà il render.
- Le immagini AI (1:1) restano fuori dal ritocco.

### 8.6 Dove si salvano le scelte

| Opzione | Pro | Contro |
|---|---|---|
| **A. Colonna JSONB `ritocco` su `VersionePostFoto`** (consigliata) | La scelta viaggia con la versione del post: storico, autore, annullabile come le altre | Migrazione Alembic |
| B. Dentro `foto.analisi_ai` | Nessuna migrazione | Nessuno storico; vale per ogni campagna che riusa la foto dall'archivio |

Con A, sulla stessa riga si può salvare anche la chiave del render definitivo (7.6).

### 8.7 Anteprima: tempi e costi

- Una rotta autenticata (es. `POST /post/{id}/anteprima-foto` con le scelte nel corpo) risponde con il JPEG del render.
- Stesso esecutore della pubblicazione (7.5), quindi stessa uscita.
- Cache per chiave del piano effettivo; richieste raggruppate lato frontend (attesa di ~250 ms dopo l'ultimo clic).
- Obiettivo da misurare: meno di mezzo secondo per un 12 MP, grazie a `draft()`.

### 8.8 Quanto pesa sul flusso

| Caso | Lavoro in più per l'operatore |
|---|---|
| Foto senza difetti né zone | nessuno |
| Foto con proposta di ritocco che va bene | nessuno |
| Foto con zone privacy | un clic per campagna (8.4) |
| Proposta da cambiare | apre Ritocca, uno o due clic |
| Foto da non usare | Cambia foto o Chiedi all'artigiano, come oggi |

---

## 9. Il prompt

### 9.1 Che cosa fa la chiamata

Guarda le foto e dice **che cosa c'è e dove**: descrizione per i testi, valutazione, diagnosi per il ritocco. Non dà dosi di correzione, non calcola ritagli, non dà numeri di luce. È la sola chiamata AI del ritocco.

### 9.2 Struttura dei messaggi

```text
[system]   analisi_v4.md                      ← fisso, in testa, in cache
[schema]   response_format = RispostaAnalisi   ← fisso
[user]     {"descrizione_del_gruppo": …, "da_usare_il": …}
           "Foto 51:" {contesto misurato della 51}  [immagine 51]
           "Foto 52:" {contesto misurato della 52}  [immagine 52]
           …
```

Tutto ciò che è fisso sta in testa (O4): la cache del provider lavora sul prefisso, e il prefisso di sistema è uguale per ogni gruppo di ogni campagna. Ciò che cambia (descrizione, misure, immagini) viene dopo.

### 9.3 Le sezioni di `analisi_v4.md`

| Sezione | Contenuto | Rispetto a v3 |
|---|---|---|
| A. Ruolo | assistente del consorzio; descrive per chi scrive i post e diagnostica per chi prepara le foto | ampliato |
| B. Come leggere l'ingresso | contesto del gruppo, contesto misurato di ogni foto, segni disegnati | nuovo |
| C. Coordinate | origine in alto a sinistra, 0–1, tre decimali al massimo, "rispetto alla foto che vedi" | da `soggetto_box` |
| D. Campi per i testi | `soggetto`, `descrizione`, `tipo` | invariati |
| E. Valutazione | `qualita`, `idonea`, `motivo`, `punteggio`, `simile_a` | + `qualita` |
| F. Inquadratura | soggetto, centro, contesto, intrusi, testo da tenere, superficie piana, storta, preferenza | nuovo |
| G. Luce | esposizione, controluce, flash, dominante, riferimento neutro, riflessi | nuovo |
| H. Privacy | volti per codice, zone aggiunte, marchi | nuovo (sostituisce `persone_riconoscibili`) |
| I. Regole | non inventare; niente numeri di correzione; nel dubbio niente (ma per la privacy nel dubbio segnala); i segni non sono la foto | ampliato |
| J. Esempi | due o tre esempi testuali brevi | nuovo |

### 9.4 Il testo delle sezioni nuove (bozza)

**B. Come leggere l'ingresso**

```text
Prima delle foto ricevi un blocco JSON con la descrizione del gruppo scritta dall'artigiano. Ogni foto è preceduta da una riga «Foto <id>:» e da un piccolo JSON con ciò che il programma ha misurato su quella foto: il rapporto tra i lati, alcune misure dette a parole (per esempio "nitidezza": "bassa") e gli elementi che ha trovato da solo, ognuno con un codice: V1, V2… sono possibili volti, Q1, Q2… possibili superfici piane.
Sulla foto quei codici sono disegnati come riquadri sottili con l'etichetta. I segni li ha messi il programma: non fanno parte della foto, non descriverli e non contarli nel punteggio.
Le misure servono per ciò che in una foto piccola non si vede bene, come la nitidezza o le luci bruciate. Non usarle per contraddire ciò che vedi: se una foto ti sembra buia per scelta, dillo.
```

**F. Inquadratura** (dopo `soggetto_box`; `null` per screenshot e grafiche)

```text
- `inquadratura`: serve a chi prepara la foto per il feed. Riguarda solo dove stanno le cose.
  - `centro_interesse`: il punto che non va mai tagliato (un viso, il centro della pizza, l'etichetta del prodotto), come {"x", "y"}; `null` se non c'è.
  - `contesto`: `solo_soggetto` se conta l'oggetto; `ambiente` se la foto racconta un luogo (la bottega, la sala, la vetrina, un allestimento) e va tagliata poco.
  - `intrusi`: cose estranee **ai bordi** della foto che conviene togliere tagliando (attrezzi, sacchi, scatole, cavi, persone di passaggio, un altro prodotto che non c'entra). Ognuna con `box` e `che_cosa`. Ciò che sta in mezzo al soggetto non è un intruso. Al massimo quattro; lista vuota se non ce ne sono.
  - `testo_da_tenere`: riquadri di scritte che devono restare leggibili e intere: cartello, lavagna, prezzo, etichetta del prodotto, insegna della bottega. Al massimo quattro. Non le scritte private (vanno in `privacy`) né i marchi di altre aziende.
  - `superficie_piana`: se la foto mostra una superficie piatta ripresa di sbieco che si può raddrizzare (lavagna, cartello, volantino, listino, foto stampata rifotografata, quadro, pannello, schermo). Se uno dei riquadri Q disegnati la contorna bene, scrivi il suo codice in `candidato` e `null` in `angoli`; altrimenti `candidato: null` e i quattro `angoli` in senso orario dall'alto a sinistra. Mai per cibo, persone, animali, oggetti con volume o stanze. Se non c'è, `null`.
  - `storta`: `si` se l'orizzonte o le linee verticali (muri, porte, scaffali, mobili) pendono senza motivo; `voluto` se l'inclinazione è una scelta (foto dall'alto, inquadratura creativa); altrimenti `no`. Non dire di quanto: lo misura il programma.
  - `preferenza`: `intera` se tagliare farebbe perdere una parte importante; `ritaglio_ammesso` se ai bordi non c'è nulla di essenziale. Nel dubbio `intera`.
```

**G. Luce** (`null` per screenshot e grafiche)

```text
- `luce`: come appare la foto, senza numeri.
  - `esposizione`: `ok`, `scura`, `chiara`. Un locale buio per scelta (candele, forno a legna, sera) è `ok`.
  - `controluce`: `true` se una finestra o una vetrina dietro il soggetto lo lascia in ombra.
  - `flash`: `true` se si vede il flash diretto: riflesso duro, ombra netta dietro il soggetto, centro più chiaro dei bordi.
  - `dominante`: `nessuna`, `calda`, `fredda`, `verde`, `magenta`. Giudica il colore del soggetto, non quello dello sfondo. Una luce calda voluta non è una dominante.
  - `riferimento_neutro`: il riquadro di una superficie che nella realtà è bianca o grigia (un piatto, una tovaglia bianca, un foglio stampato, un muro bianco); `null` se non c'è o non sei sicuro. Carta da forno, legno, pane, pelle e tessuti colorati non sono neutri.
  - `riflessi`: `no`, `ai_bordi`, `sul_soggetto` (vetri, vetrine, bottiglie, plastica, metallo, smalti).
```

**H. Privacy**

```text
- `privacy`: chi e che cosa non va mostrato senza consenso. Qui, al contrario del resto, nel dubbio segnala: decide l'operatore.
  - `volti`: per ogni codice V che il programma ti ha dato, `chi`: `staff` (titolare o personale che posa o lavora, riconoscibile da grembiule, divisa, posizione dietro il banco o dalla descrizione del gruppo), `cliente` (clienti, passanti, invitati), `minore` (bambini e ragazzi), `non_volto` (il riquadro non contiene un volto). Nel dubbio tra `staff` e `cliente`, `cliente`.
  - `zone_aggiunte`: ciò che il programma non ha segnato: volti riconoscibili senza codice, e scritte private (il nome di una persona su una torta, un biglietto o un pacco, un indirizzo, una targa, una schermata con dati personali). Ognuna con `box` e `che_cosa`. Al massimo sei.
- `marchi_visibili`: come prima.
```

**E. Qualità** (prima di `idonea`, perché la informa)

```text
- `qualita`:
  - `mossa`: `no`, `lieve`, `forte`, oppure `voluto` se il movimento racconta qualcosa (fuoco, vapore, il gesto del pizzaiolo).
  - `tipo_immagine`: `foto`, `foto_di_foto` (una stampa o uno schermo fotografati), `screenshot`, `grafica` (locandina, volantino digitale).
- `idonea` e `punteggio` giudicano la foto com'è adesso, non come sarà dopo i ritocchi.
```

**I. Regole in più**

```text
- Non calcolare ritagli, angoli di rotazione o correzioni di luce: dici che cosa vedi e dove, il programma decide quanto correggere.
- Nel dubbio: `null`, liste vuote, `esposizione: "ok"`, `dominante: "nessuna"`, `storta: "no"`. Per la privacy, al contrario, nel dubbio segnala.
- Le coordinate sono rispetto alla foto che vedi, con tre decimali al massimo.
```

**J. Esempi** (testuali, ~100 token ciascuno; nessuna immagine di esempio, che costerebbe ~765 token l'una)

```text
Esempio 1. Lavagna del menù scritta a gesso, ripresa di sbieco su un cavalletto: `tipo` "dettaglio"; `superficie_piana` con `che_cosa` "lavagna" (Q1 se contorna la lavagna); `testo_da_tenere` sulla scritta; `storta` "no" (l'inclinazione la corregge la superficie).
Esempio 2. Sala piena di sera, luce calda: `contesto` "ambiente"; `esposizione` "ok"; `dominante` "nessuna"; i volti V1–V4 dei clienti ai tavoli `cliente`; il cameriere in divisa `staff`.
```

### 9.5 Misure in fasce

All'AI le misure arrivano **a parole**, non come numeri: i modelli usano meglio "nitidezza: bassa" che "varianza 41,2", e le parole costano meno token. Le soglie stanno in codice, in un catalogo, e si tarano in fase 0 sulle foto reali.

| Misura | Fasce |
|---|---|
| nitidezza | alta · media · bassa |
| esposizione | scura · normale · chiara |
| luci bruciate | nessuna · poche · molte |
| ombre chiuse | nessuna · poche · molte |
| dominante misurata | nessuna · calda · fredda · verde · magenta |
| compressione | nessuna · lieve · forte |

Si mandano solo le fasce **non normali** (una foto pulita ha il contesto `{}` più il rapporto): pochi token.

### 9.6 I segni sulla copia AI

| | Segni disegnati sulla foto | Codici solo nel JSON | Seconda immagine con i segni |
|---|---|---|---|
| Precisione nel collegare codice e oggetto | alta | bassa (i modelli collegano male numeri e pixel) | alta |
| Costo | zero | zero | ~765 token per foto con candidati |
| Rischio | i segni influenzano descrizione e punteggio | – | nessuno |

Proposta: segni sottili, colore unico ad alto contrasto, etichetta piccola fuori dal riquadro, disegnati **solo** sulle foto che hanno candidati. Da provare in fase 0: stesse foto con e senza segni, confronto del punteggio e della descrizione.

### 9.7 Cache del prompt

- Oggi `analisi_v3` (~900 token) è sotto la soglia di 1.024 token della cache automatica (OpenAI, anche via OpenRouter): nessuno sconto (6.2 h).
- Con v4 il prefisso fisso (sistema + schema) supera ~3.000 token: la cache scatta e la parte in cache costa circa la metà (da verificare con il provider e con OpenRouter).
- Verifica: `usage.prompt_tokens_details.cached_tokens` nella risposta. Registrarlo in `chiamata_ai` richiede un campo nuovo (da decidere).

### 9.8 Versioni

- `prompts/analisi_v4.md` nuovo; `analisi_v3.md` resta.
- `versione_prompt="analisi_v4"` in `chiamata_ai`, come oggi.
- In `analisi_ai` si salvano anche `versione_prompt`, `versione_locale` e `versione_diagnosi`: un'analisi vecchia si legge per quello che è (10.12).

### 9.9 Costi (prezzi della configurazione: 2,50 $ / 10 $ per milione)

> **Superata dalla 12.2**: il +40% è stato giudicato eccessivo. Con lo schema compatto la stima scende a +5–12%.

Stime per un gruppo da 10 foto; un'immagine a 1024 px con `detail: high` vale ~765 token.

| Voce | Oggi (v3) | Con v4 | Note |
|---|---|---|---|
| Sistema + schema | ~1.100 | ~3.200 | in cache con v4 |
| Contesto del gruppo e delle foto | ~100 | ~600 | fasce e codici |
| Immagini | ~7.700 | ~7.700 | invariate (segni sulla stessa immagine) |
| **Ingresso** | ~8.900 → 2,2 ¢ | ~11.500 → 2,9 ¢, ~2,5 ¢ con la cache | |
| Uscita per foto | ~170 | ~300 | la voce che pesa |
| **Uscita** | ~1.700 → 1,7 ¢ | ~3.000 → 3,0 ¢ | |
| **Totale per gruppo** | **~3,9 ¢** | **~5,5 ¢** | **+40%**, ~0,55 ¢ a foto |

Il criterio "entro il +50%" (sezione 3) regge, ma con poco margine: lo decide l'uscita. Per questo O5, O6 e O7 sono necessari, non facoltativi. Le cifre vanno misurate in fase 0 con `chiamata_ai`.

### 9.10 Come si valuta il prompt (fase 0, fuori da pytest)

- **Insieme di riferimento:** le foto reali raccolte con i profili della PR #189 (stesso telefono e stesso locale per profilo), con la verità scritta a mano su un sottoinsieme: soggetto, intrusi, testo, superfici, volti, luce.
- **Metriche:** sovrapposizione dei riquadri con la verità; errore sugli angoli in % del lato; richiamo dei volti `cliente` e `minore` (conta più della precisione: decide l'operatore); accordo su esposizione, dominante e storta; quota di campi scartati dai validatori; token di uscita reali; deriva di punteggio e descrizione con i segni.
- **Varianti:** con e senza segni; con e senza fasce; due modelli di visione.

---

## 10. I dati strutturati nel flusso

### 10.1 Mappa

| Dato | Chi lo scrive | Quando | Dove | Chi lo legge |
|---|---|---|---|---|
| `Foto` (larghezza, altezza, file) | caricamento | sincrono | tabella `foto` | tutti |
| `analisi_locale` | L1 | tappa ANALISI | `foto.analisi_ai["locale"]` | AI (in fasce), L2, L3 |
| Contesto per foto | L1 | per la chiamata | solo nella richiesta (in `chiamata_ai.richiesta`) | AI |
| Risposta v4 | AI | tappa ANALISI | `chiamata_ai.risposta` | L2 |
| Analisi (campi v3) | L2 | tappa ANALISI | `foto.analisi_ai` (come oggi) | piano, testi |
| Diagnosi verificata | L2 | tappa ANALISI | `foto.analisi_ai["ritocco"]` | proposta |
| Proposta | funzione pura | a ogni anteprima | non salvata | L3, operatore |
| Scelte dell'operatore | operatore | revisione | `versione_post_foto.ritocco` (8.6 A) | piano effettivo |
| Piano effettivo | funzione pura (proposta + scelte) | anteprima, approvazione | impronta salvata con il render | L3 |
| Render | L3 | approvazione | file derivato nell'archivio | pubblicazione |

Nessuna migrazione per `analisi_ai` (è JSONB). Una migrazione per `versione_post_foto.ritocco` e per la chiave del render.

### 10.2 Un solo riferimento per le coordinate

Tutte le coordinate dell'AI, della pre-analisi e delle scelte dell'operatore sono **normalizzate 0–1 nel riferimento dell'originale dopo EXIF**: quello della copia AI. L'esecutore le porta nei riferimenti successivi (rotazione dell'operatore, raddrizzamento, finestra). Unica eccezione: la finestra "a mano" dell'operatore si esprime nel riferimento **dopo** il raddrizzamento, perché l'operatore la disegna sull'anteprima già dritta.

### 10.3 `analisi_locale`

```json
{
  "versione": "locale-1",
  "formato": {"larghezza": 3024, "altezza": 4032, "rapporto": 0.75, "orientamento_exif": 6},
  "colore": {"profilo": "Display P3", "convertito_srgb": true},
  "exif": {"flash": true, "iso": 1600, "zoom_digitale": 1.0, "fotocamera": true, "software": null},
  "misure": {
    "nitidezza": 41.2, "luminanza_mediana": 0.31, "luci_bruciate": 0.004,
    "ombre_chiuse": 0.18, "dominante_ab": [3.1, 11.8], "caduta_bordi": 0.22,
    "angolo_linee": -2.4, "qualita_jpeg": 87
  },
  "fasce": {"nitidezza": "bassa", "esposizione": "scura", "ombre_chiuse": "molte", "dominante": "calda"},
  "candidati": {
    "volti": [
      {"id": "V1", "box": {"x": 0.112, "y": 0.301, "larghezza": 0.061, "altezza": 0.046}, "affidabilita": 0.82},
      {"id": "V2", "box": {"x": 0.604, "y": 0.288, "larghezza": 0.055, "altezza": 0.041}, "affidabilita": 0.64}
    ],
    "quadrilateri": []
  }
}
```

### 10.4 Il contesto per foto inviato all'AI

```text
Foto 51: {"rapporto": 0.75, "misure": {"nitidezza": "bassa", "esposizione": "scura", "dominante": "calda"}, "flash": true, "candidati": ["V1", "V2"]}
```

Circa 40–60 token. Le coordinate dei candidati **non** si mandano: sono disegnate (9.6).

### 10.5 Lo schema di risposta (in `adapters/ai/schemi.py`)

> **Superate dalla 12.2 le sezioni 10.5, 10.6, 10.9 e 10.10**: lo schema diventa compatto e sparso (codici al posto di campi, riquadri in centesimi, `ritocco: null` per le foto senza nulla da dire), e la proposta diventa tre varianti salvate come comandi (12.5). Restano validi i principi: campi obbligatori, `Literal`, controlli nei validatori, test di confronto con il catalogo. La sezione 9.4 resta valida nel contenuto (che cosa l'AI deve riconoscere), ma va riscritta nella forma dei codici della 12.2.

Regole di oggi: tutti i campi obbligatori, nullabili con `| None` senza valore di partenza, `Literal` per gli enum, controlli di valore nei validatori e non nello schema (provider con schema stretto). L'ordine dei campi è l'ordine in cui il modello scrive: prima osserva, poi giudica, poi localizza.

```python
class Punto(BaseModel):
    x: float
    y: float


class Quadrilatero(BaseModel):
    alto_sx: Punto
    alto_dx: Punto
    basso_dx: Punto
    basso_sx: Punto


class Qualita(BaseModel):
    mossa: Literal["no", "lieve", "forte", "voluto"]
    tipo_immagine: Literal["foto", "foto_di_foto", "screenshot", "grafica"]


class Intruso(BaseModel):
    box: SoggettoBox
    che_cosa: Literal["attrezzi", "imballi", "cavi", "persona", "altro_prodotto", "altro"]


class SuperficiePiana(BaseModel):
    candidato: str | None          # "Q1": uno dei quadrilateri della pre-analisi
    angoli: Quadrilatero | None    # solo se candidato è None
    che_cosa: Literal[
        "lavagna", "cartello", "volantino", "foto_rifotografata", "quadro_pannello", "schermo"
    ]


class Inquadratura(BaseModel):
    centro_interesse: Punto | None
    contesto: Literal["solo_soggetto", "ambiente"]
    intrusi: list[Intruso]
    testo_da_tenere: list[SoggettoBox]
    superficie_piana: SuperficiePiana | None
    storta: Literal["no", "si", "voluto"]
    preferenza: Literal["intera", "ritaglio_ammesso"]


class Luce(BaseModel):
    esposizione: Literal["ok", "scura", "chiara"]
    controluce: bool
    flash: bool
    dominante: Literal["nessuna", "calda", "fredda", "verde", "magenta"]
    riferimento_neutro: SoggettoBox | None
    riflessi: Literal["no", "ai_bordi", "sul_soggetto"]


class Volto(BaseModel):
    candidato: str                 # "V1": uno dei volti della pre-analisi
    chi: Literal["staff", "cliente", "minore", "non_volto"]


class ZonaPrivata(BaseModel):
    box: SoggettoBox
    che_cosa: Literal["volto_cliente", "volto_minore", "nome", "indirizzo", "targa", "dati_personali"]


class Privacy(BaseModel):
    volti: list[Volto]
    zone_aggiunte: list[ZonaPrivata]


class AnalisiFoto(BaseModel):
    foto_id: int
    soggetto: str
    descrizione: str
    tipo: TipoFoto
    qualita: Qualita
    idonea: bool
    motivo: str | None
    punteggio: int
    simile_a: int | None
    soggetto_box: SoggettoBox | None
    inquadratura: Inquadratura | None   # None per screenshot e grafiche
    luce: Luce | None                   # None per screenshot e grafiche
    privacy: Privacy
    marchi_visibili: bool
    # persone_riconoscibili non si chiede più: lo deriva L2 dai volti (O6)
```

Come oggi, `TipoFoto` e gli enum nuovi sono copie: un test li confronta con il catalogo del ritocco in `campagne`, e un test controlla che ogni campo e ogni valore compaia nel prompt.

### 10.6 Esempio di risposta (illustrativo, coordinate inventate)

Foto 51 = "Sala piena di sera, tavoli apparecchiati" (profilo 03, n. 11). Foto 52 = "Lavagna del menù del giorno scritta a mano" (profilo 04, n. 14).

```json
{
  "foto": [
    {
      "foto_id": 51,
      "soggetto": "Sala della pizzeria piena di clienti ai tavoli, di sera",
      "descrizione": "Una sala con una decina di tavoli apparecchiati e occupati, luce calda dalle lampade a sospensione. In fondo si vede il bancone e la bocca del forno a legna accesa. I clienti sono seduti, alcuni di fronte all'obiettivo.",
      "tipo": "ambientato",
      "qualita": {"mossa": "lieve", "tipo_immagine": "foto"},
      "idonea": true,
      "motivo": null,
      "punteggio": 3,
      "simile_a": null,
      "soggetto_box": {"x": 0.0, "y": 0.18, "larghezza": 1.0, "altezza": 0.7},
      "inquadratura": {
        "centro_interesse": {"x": 0.62, "y": 0.35},
        "contesto": "ambiente",
        "intrusi": [],
        "testo_da_tenere": [],
        "superficie_piana": null,
        "storta": "no",
        "preferenza": "intera"
      },
      "luce": {
        "esposizione": "ok",
        "controluce": false,
        "flash": false,
        "dominante": "nessuna",
        "riferimento_neutro": {"x": 0.41, "y": 0.71, "larghezza": 0.06, "altezza": 0.04},
        "riflessi": "no"
      },
      "privacy": {
        "volti": [
          {"candidato": "V1", "chi": "cliente"},
          {"candidato": "V2", "chi": "cliente"}
        ],
        "zone_aggiunte": [
          {"box": {"x": 0.83, "y": 0.4, "larghezza": 0.04, "altezza": 0.05}, "che_cosa": "volto_cliente"}
        ]
      },
      "marchi_visibili": false
    },
    {
      "foto_id": 52,
      "soggetto": "Lavagna con il menù del giorno scritto a gesso",
      "descrizione": "Una lavagna nera su un cavalletto di legno elenca i piatti del giorno con i prezzi, scritti a gesso bianco con qualche parola in rosso. È ripresa di sbieco davanti al bancone.",
      "tipo": "dettaglio",
      "qualita": {"mossa": "no", "tipo_immagine": "foto"},
      "idonea": true,
      "motivo": null,
      "punteggio": 3,
      "simile_a": null,
      "soggetto_box": {"x": 0.14, "y": 0.08, "larghezza": 0.71, "altezza": 0.83},
      "inquadratura": {
        "centro_interesse": {"x": 0.5, "y": 0.45},
        "contesto": "solo_soggetto",
        "intrusi": [
          {"box": {"x": 0.0, "y": 0.62, "larghezza": 0.12, "altezza": 0.38}, "che_cosa": "imballi"}
        ],
        "testo_da_tenere": [{"x": 0.2, "y": 0.14, "larghezza": 0.6, "altezza": 0.7}],
        "superficie_piana": {"candidato": "Q1", "angoli": null, "che_cosa": "lavagna"},
        "storta": "no",
        "preferenza": "ritaglio_ammesso"
      },
      "luce": {
        "esposizione": "ok",
        "controluce": false,
        "flash": false,
        "dominante": "fredda",
        "riferimento_neutro": null,
        "riflessi": "no"
      },
      "privacy": {"volti": [], "zone_aggiunte": []},
      "marchi_visibili": false
    }
  ]
}
```

Lettura: nella 51 l'AI dice "buio voluto" (`esposizione: ok`) e la misura dice scura → **nessuna** correzione di esposizione (doppia chiave). Nella 52 la dominante fredda non ha un riferimento neutro → nessuna correzione del bianco; il raddrizzamento usa Q1.

### 10.7 Validatori e doppia chiave

**Validatori morbidi (un campo che non passa vale `None` o lista vuota):**

| Campo | Controllo |
|---|---|
| ogni `box` | `riquadro_valido` di oggi |
| `centro_interesse` | punto in 0–1 |
| `candidato` di volti e superficie | esiste nei candidati di quella foto; i codici sconosciuti si scartano |
| `superficie_piana` | o `candidato` o `angoli`, non entrambi né nessuno; angoli convessi, angoli interni 45°–135°, area ≥ 5% |
| liste | `intrusi` ≤ 4, `testo_da_tenere` ≤ 4, `zone_aggiunte` ≤ 6: troncate |
| `inquadratura`, `luce` | `None` se `tipo_immagine` è `screenshot` o `grafica` |
| `persone_riconoscibili` | derivato: vero se un volto non è `non_volto` o c'è una zona di volto |

**Doppia chiave (una correzione entra nella proposta solo se entrambe le condizioni valgono; la dose la dà la misura):**

| Correzione | Dice l'AI | Conferma la misura | Dose |
|---|---|---|---|
| Esposizione + | `scura` | luminanza mediana del soggetto sotto soglia | fino alla mediana obiettivo, con tetto (più basso con ISO alto) |
| Esposizione − | `chiara` | mediana alta e poche luci bruciate | con tetto |
| Bianco | `dominante` ≠ `nessuna` **e** `riferimento_neutro` | il riferimento si scosta dal neutro oltre soglia | guadagni per canale con tetto |
| Ombre | `controluce` | ombre chiuse nel soggetto oltre soglia | con tetto |
| Flash | `flash` | caduta centro-bordi oltre soglia | compensazione con tetto |
| Rotazione | `storta: si` | angolo misurato tra 0,5° e 8° | l'angolo misurato |
| Prospettiva | `superficie_piana` | angoli affinati validi, deformazione entro soglia | omografia |
| Nitidezza finale | `qualita.tipo_immagine` = `foto` | compressione `nessuna` o `lieve`, zoom 1 | lieve |
| Privacy | `cliente`, `minore`, zona aggiunta | – (la misura non conferma: decide l'operatore) | zona proposta, spenta |
| Volto senza risposta | candidato V che l'AI non ha classificato | – | zona proposta "da verificare" (richiamo) |

### 10.8 Diagnosi verificata (`foto.analisi_ai["ritocco"]`)

```json
{
  "versione": "diagnosi-1",
  "versione_prompt": "analisi_v4",
  "qualita": {"mossa": "lieve", "tipo_immagine": "foto", "nitidezza": "bassa"},
  "inquadratura": {"centro_interesse": {"x": 0.62, "y": 0.35}, "contesto": "ambiente", "intrusi": [], "testo_da_tenere": [], "superficie": null, "storta": false, "preferenza": "intera"},
  "luce": {"esposizione": null, "bianco": null, "ombre": null, "flash": null},
  "privacy": [
    {"id": "z1", "origine": "V1", "che_cosa": "volto_cliente", "box": {"x": 0.112, "y": 0.301, "larghezza": 0.061, "altezza": 0.046}},
    {"id": "z2", "origine": "V2", "che_cosa": "volto_cliente", "box": {"x": 0.604, "y": 0.288, "larghezza": 0.055, "altezza": 0.041}},
    {"id": "z3", "origine": "ai", "che_cosa": "volto_cliente", "box": {"x": 0.83, "y": 0.4, "larghezza": 0.04, "altezza": 0.05}}
  ],
  "avvisi": ["foto_mossa_lieve"],
  "scarti": [{"correzione": "esposizione", "motivo": "ai_ok_misura_scura"}]
}
```

`scarti` registra dove le due chiavi non si sono trovate: serve alla fase 0 e a tarare le soglie.

### 10.9 Proposta (derivata, non salvata)

```json
{
  "versione_esecutore": "ritocco-1",
  "rotazione_90": 0,
  "raddrizza": null,
  "finestra": {"x": 0.0, "y": 0.0, "larghezza": 1.0, "altezza": 1.0, "rapporto": 0.8},
  "barre": null,
  "luce": {"esposizione": 0.0, "bianco": null, "ombre": 0.0, "flash": 0.0},
  "nitidezza": false,
  "privacy": {"z1": false, "z2": false, "z3": false}
}
```

Con la 52 si avrebbe `"raddrizza": {"tipo": "prospettiva", "angoli": {…}}` e una finestra che esclude gli imballi.

### 10.10 Scelte dell'operatore (`versione_post_foto.ritocco`)

Solo ciò che cambia rispetto alla proposta:

```json
{
  "versione": 1,
  "base": "proposta",
  "privacy": {"z1": true, "z2": true, "z3": true},
  "luce": {"esposizione": 1}
}
```

Valori ammessi: `base` (`proposta`, `essenziale`); `rotazione_90` (0, 90, 180, 270); `raddrizza` (vero, falso); `inquadratura` (`{"modo": "proposta" | "intera" | "manuale", "finestra": …, "centro": …}`); `luce` (`esposizione` −1, 0, +1 passi; `colore` e `ombre` vero/falso); `privacy` (id → vero/falso); `privacy_aggiunte` (lista di `{box, che_cosa}`).

### 10.11 Piano effettivo e render

- `piano_effettivo = applica(proposta(diagnosi, versione_esecutore), scelte)`: funzione pura.
- `chiave = sha256(json_canonico(piano_effettivo) + versione_esecutore + foto.file)`.
- Anteprima: cache per chiave. Approvazione: render salvato come file derivato con quella chiave.
- La chiave si salva accanto alle scelte; l'URL firmato di Instagram firma la chiave del render (oggi firma foto e canale).

### 10.12 Compatibilità

- Un'analisi v3 (senza `ritocco` né `locale`) dà la proposta **essenziale**: correzioni obbligatorie e regole di oggi. Le misure locali si possono ricalcolare senza AI, ma solo quelle: i candidati mai, perché nessuna risposta AI li cita.
- Il criterio della sezione 3 "con `piano=None` byte-identico a oggi" non regge più per scelta: sRGB e la fine dell'autocontrasto per canale cambiano **ogni** foto. Diventa: "con le correzioni obbligatorie spente e nessun piano, identico a oggi" (test di regressione), più il test sulle 21 foto buone.
- Dimensione: `analisi_ai` cresce di ~1–2 KB per foto (misure, candidati, diagnosi).

---

## 11. Punti aperti e ingredienti per i task

I task si costruiscono a fine sessione (sezione 0). Qui solo ciò che servirà.

### 11.1 Decisioni ancora da prendere

Stato al 9 novembre (approvate le proposte):

1. Foto "copertina" trattate come feed: **sì** (approvato).
2. Riepilogo privacy in Approva: **conferma esplicita, un clic** (approvato).
3. Scelte dell'operatore su `VersionePostFoto` con migrazione (8.6 A): **sì** (approvato).
4. Ingrandimento nell'avvicinamento: **nessuno in Standard, fino a ~1,3× in Spinta** (12.4, proposta coerente con le varianti).
5. Segni disegnati sulla copia AI: si decide in fase 0.
6. OpenCV già in L1 per volti e quadrilateri: **sì** (approvato). Rilevatore dei volti: le cascate di Haar sono nel pacchetto; uno migliore richiede un modello da scaricare (licenza e dimensione da verificare).
7. Token in cache in `chiamata_ai`: **sì**, colonna nuova (12.3).
8. R-42 e `spec.md`: da aggiornare insieme al codice che li cambia (proposta).
9. Fase 0: autorizzazione a usare le foto reali raccolte con la PR #189 (consenso scritto, README della PR): **aperta**, dipende dai titolari.

### 11.2 Ingredienti, in ordine di dipendenza (non sono task)

> **Superata dalla 12.6**: l'ordine cambia (il colore sRGB va per primo) e le varianti sostituiscono il pannello.

1. **Fase 0 · prova:** script fuori da pytest sulle foto reali; v4 contro v3; con e senza segni; misura di token e costi.
2. **Correzioni obbligatorie:** sRGB, via l'autocontrasto per canale, esecutore con ordine fisso (7.5), test sulle 21 foto buone.
3. **Anteprima reale per l'operatore:** la card mostra il render (6.2 a). Già utile da sola, senza AI nuova.
4. **Render salvato all'approvazione** e pubblicazione dal file salvato (7.6).
5. **L1 pre-analisi:** misure, fasce, candidati; numpy e OpenCV in `requirements.txt` (nome, motivo, licenza).
6. **Prompt v4 e schema:** `analisi_v4.md`, `schemi.py`, `litellm.py`, `finto.py` (con risposte canned di ritocco), test di confronto e di presenza nel prompt.
7. **L2:** validatori morbidi, doppia chiave, diagnosi in `analisi_ai["ritocco"]`.
8. **Proposta ed esecutore completo:** finestra, raddrizzamento, luce, privacy.
9. **Pannello Ritocca:** intervento `RITOCCA_FOTO`, migrazione `versione_post_foto.ritocco`, rotta di anteprima, frontend.
10. **Privacy in Approva:** riepilogo e "Oscura tutte".

### 11.3 Da scrivere nella PR (AGENTS.md)

- `backend/requirements.txt`: numpy (BSD-3), opencv-python-headless (Apache-2.0, con librerie di terzi LGPL).
- `alembic/`: colonna `ritocco` e chiave del render su `versione_post_foto`.
- `contenuti/domain.py`: `RITOCCA_FOTO` in `INTERVENTI_AMMESSI`.
- Nuovi file in `adapters/ai` (prompt v4) e in `campagne` (catalogo, esecutore, pre-analisi).
- Nessuna modifica a `core/` prevista; nessuna a `docs/archivio/`.

Fonti sui formati feed (terze parti, da confermare sulla documentazione Meta): [Sked Social](https://skedsocial.com/blog/best-instagram-image-and-video-size-recommendations.md), [AdaptlyPost](https://adaptlypost.com/es/blog/instagram-api-image-requirements), [ZoomSphere](https://help.zoomsphere.com/en/articles/4852379-scheduler-image-post-requirements-for-ig-auto-publishing), [Metricool](https://metricool.com/facebook-image-sizes/), [HeyOrca](https://heyorca.com/blog/facebook-posting-specs-best-practices-in-2026).

---

## 12. Revisione del 9 novembre: colore, costo, cache, operatore a tre varianti

### 12.1 Il colore delle foto iPhone

**Il problema.** L'iPhone (e diversi Android recenti) salva i JPEG con il profilo colore **Display P3**, più ampio di sRGB. I numeri dei pixel hanno senso solo insieme al profilo. Oggi il profilo si perde in tre punti:
- `sistema_foto_buffer`: `convert("RGB")` lo ignora e il JPEG in uscita non lo porta, quindi Facebook e Instagram leggono i numeri P3 come se fossero sRGB;
- `_foto_per_ai`: anche l'AI vede i colori sbagliati e giudica la dominante su una foto falsata;
- l'anteprima dell'operatore mostra l'originale e il browser **gestisce** il profilo: l'operatore vede i colori giusti e la foto pubblicata esce diversa (6.2 a).

**La prova** (9 novembre, `ImageCms` con LittleCMS 2.19, già nelle wheel di Pillow). Il profilo Display P3 è stato costruito in codice dai primari pubblici (adattamento Bradford da D65 a D50, curva sRGB). Il metodo è stato verificato rifacendo nello stesso modo un sRGB: la conversione verso il sRGB di LittleCMS lascia i colori identici.

| Colore | Valori P3 | sRGB corretto | Uscita di oggi |
|---|---|---|---|
| pomodoro | (220, 60, 40) | (239, 35, 17) | (221, 60, 40) |
| basilico | (60, 150, 60) | (0, 152, 44) | invariato |
| rosa | (230, 90, 140) | (249, 77, 141) | invariato |
| pane | (205, 160, 110) | (213, 158, 102) | invariato |
| grigio, bianco | invariati | invariati | invariati |

I neutri restano giusti, per questo il difetto passa inosservato. I colori saturi escono spenti: pizza, fiori, smalti, cioè proprio i prodotti dei profili della PR #189.

**La soluzione.**
1. **Una funzione sola**, per esempio `apri_in_srgb(dati) -> Image`, in `campagne`, usata da sistemazione, pre-analisi, copia AI e anteprima. Fa: decodifica Pillow con i limiti di oggi, `exif_transpose`, e se c'è `icc_profile` la conversione `ImageCms.profileToProfile(img, profilo_sorgente, sRGB, renderingIntent=RELATIVE_COLORIMETRIC, flags=BLACKPOINTCOMPENSATION, outputMode="RGB")`.
2. **Modi particolari:** trasparenza appiattita su bianco prima della conversione (come oggi); `P` convertita prima in RGB; JPEG CMYK con profilo convertiti con il profilo, senza profilo con la conversione di oggi; scala di grigi con profilo grigio convertita in RGB.
3. **Profilo rotto o illeggibile:** si ignora, si registra un avviso, nessuna eccezione (la foto resta pubblicabile come oggi).
4. **Prestazioni:** la conversione si fa sulla copia già ridotta da `draft()`, non sui 12 MP.
5. **In uscita:** JPEG con il profilo **sRGB incorporato** (pochi KB, nessun dato personale), così nessuno deve indovinare. EXIF e GPS restano tolti.
6. **Colori fuori gamma:** i verdi e i rossi più saturi del P3 non esistono in sRGB e vengono tagliati al bordo (il canale rosso del basilico va a 0). È inevitabile pubblicando in sRGB, ed è comunque più fedele di oggi.
7. **Da verificare con un iPhone vero:** se dal browser arriva un HEIC, oggi i magic bytes lo rifiutano. Le foto HDR con gain map danno l'immagine SDR di base: va bene.

**Test senza foto reali:** il profilo P3 si genera in codice (nessuna licenza da verificare per la fixture). Casi: pomodoro P3 → atteso ±2; neutri invariati; foto senza profilo invariata; profilo rotto senza eccezione; PNG con `iCCP`; WEBP con ICC; JPEG CMYK.

**Posizione:** è una correzione obbligatoria e la **prima** dell'esecutore (passo 2 della 7.5). Non dipende dall'AI: si può fare subito, da sola.

### 12.2 Il costo: schema compatto e sparso

**Da dove veniva il +40%.** Dall'uscita: lo schema largo della 10.5 aggiungeva circa 187 token a foto (misurato sui caratteri dell'esempio 10.6), e un token di uscita costa 4 volte uno di ingresso. Poi dal prompt, circa 2.100 token in più.

**Le leve applicate:**
1. **Codici sparsi** invece di campi: si scrive solo ciò che non è normale.
2. **`ritocco: null`** quando non c'è niente da dire.
3. **Riquadri come quattro interi in centesimi**, `[x, y, larghezza, altezza]`, anche per `soggetto_box`. L2 li riconverte nel formato di oggi, quindi chi legge `analisi_ai` non cambia.
4. **Una sola lista di zone**, con il ruolo, invece di liste separate.
5. **Superficie piana solo per codice** (`Q1`). Se OpenCV non la trova, non si raddrizza: limite accettato.
6. **Volti solo per eccezione:** si scrivono solo `staff`, `minore` e `no`. Ogni codice V non citato vale `cliente`, perché nel dubbio si propone la zona.
7. **Via dall'uscita** `persone_riconoscibili` (lo deriva L2) e `marchi_visibili` (diventa il codice `marchi`).
8. **Contesto per foto in testo semplice**, solo le fasce non normali: in media una dozzina di token.
9. **Aggiunte al prompt contenute** in circa 900 token (non 2.100): un elenco di codici con una riga ciascuno.

**Lo schema** (sostituisce la 10.5):

```python
Nota = Literal[
    # inquadratura
    "lontana", "decentrata", "storta", "ambiente", "non_tagliare",
    "ruota_90", "ruota_180", "ruota_270",
    # luce
    "scura", "chiara", "controluce", "flash",
    "calda", "fredda", "verde", "magenta",
    "riflessi_bordi", "riflessi_soggetto",
    # qualità e tipo
    "mossa_lieve", "mossa_forte", "foto_di_foto", "screenshot", "grafica",
    # altro
    "marchi",
]
RuoloZona = Literal[
    "tieni",      # testo o elemento da non tagliare
    "togli",      # intruso ai bordi
    "neutro",     # superficie bianca o grigia di riferimento
    "volto",      # volto riconoscibile senza codice V
    "nome", "indirizzo", "targa", "dati",  # scritte private
]


class Zona(BaseModel):
    ruolo: RuoloZona
    b: list[int]          # [x, y, larghezza, altezza] in centesimi della foto


class Ritocco(BaseModel):
    note: list[Nota]
    centro: list[int] | None      # [x, y] in centesimi: il punto da non tagliare
    zone: list[Zona]
    piana: str | None             # codice Q di una superficie da raddrizzare
    volti: list[str]              # solo eccezioni: "V2 staff", "V3 minore", "V4 no"


class AnalisiFoto(BaseModel):
    foto_id: int
    soggetto: str
    descrizione: str
    tipo: TipoFoto
    idonea: bool
    motivo: str | None
    punteggio: int
    simile_a: int | None
    soggetto_box: list[int] | None    # [x, y, larghezza, altezza] in centesimi
    ritocco: Ritocco | None           # None: niente da segnalare
```

Validatori morbidi (L2): `b` e `soggetto_box` con quattro interi in 0–100 e il riquadro dentro la foto; `centro` con due interi in 0–100; codici V e Q esistenti; `volti` letti con il formato "Vn ruolo" (un elemento malformato si scarta); liste troncate (`zone` ≤ 8); note in conflitto (`scura` e `chiara` insieme) scartate entrambe.

**Il significato dei codici** (testo del prompt, una riga ciascuno; che cosa ne fa il codice):

| Codice | Quando l'AI lo scrive | Effetto (con la doppia chiave della 10.7) |
|---|---|---|
| `lontana`, `decentrata` | soggetto piccolo o fuori centro | avvicinamento |
| `storta` | orizzonte o verticali pendono senza motivo | rotazione dell'angolo misurato |
| `ambiente` | la foto racconta un luogo | avvicinamento limitato |
| `non_tagliare` | tagliare toglierebbe qualcosa di importante | nessun avvicinamento |
| `ruota_90/180/270` | la foto è girata (EXIF perso, per esempio da WhatsApp) | rotazione prima di tutto, anche in Originale |
| `scura`, `chiara` | difetto di esposizione, non il buio voluto | esposizione |
| `controluce`, `flash` | come in 9.4 | ombre, caduta ai bordi |
| `calda`, `fredda`, `verde`, `magenta` | dominante sul soggetto | bianco, solo con una zona `neutro` |
| `riflessi_bordi`, `riflessi_soggetto` | vetri, bottiglie, smalti | esclusione ai bordi, avviso |
| `mossa_lieve`, `mossa_forte` | movimento non voluto | avviso, nitidezza spenta se forte |
| `foto_di_foto`, `screenshot`, `grafica` | non è una foto diretta | screenshot e grafica: solo Originale, avviso |
| `marchi` | loghi o marchi di altre aziende | `marchi_visibili` per compatibilità, avviso |

**Esempio di risposta** (sostituisce la 10.6; stesse due foto, coordinate inventate):

```json
{"foto": [
  {"foto_id": 51, "soggetto": "Sala della pizzeria piena di clienti ai tavoli, di sera",
   "descrizione": "Una sala con una decina di tavoli apparecchiati e occupati, luce calda dalle lampade a sospensione. In fondo il bancone e la bocca del forno a legna accesa. I clienti sono seduti, alcuni di fronte all'obiettivo.",
   "tipo": "ambientato", "idonea": true, "motivo": null, "punteggio": 3, "simile_a": null,
   "soggetto_box": [0, 18, 100, 70],
   "ritocco": {"note": ["ambiente", "mossa_lieve"], "centro": [62, 35],
               "zone": [{"ruolo": "neutro", "b": [41, 71, 6, 4]}, {"ruolo": "volto", "b": [83, 40, 4, 5]}],
               "piana": null, "volti": []}},
  {"foto_id": 52, "soggetto": "Lavagna con il menù del giorno scritto a gesso",
   "descrizione": "Una lavagna nera su un cavalletto di legno elenca i piatti del giorno con i prezzi, a gesso bianco con qualche parola in rosso. È ripresa di sbieco davanti al bancone.",
   "tipo": "dettaglio", "idonea": true, "motivo": null, "punteggio": 3, "simile_a": null,
   "soggetto_box": [14, 8, 71, 83],
   "ritocco": {"note": ["fredda"], "centro": [50, 45],
               "zone": [{"ruolo": "tieni", "b": [20, 14, 60, 70]}, {"ruolo": "togli", "b": [0, 62, 12, 38]}],
               "piana": "Q1", "volti": []}}
]}
```

Nella 51 i volti V1 e V2 non sono citati, quindi valgono `cliente`. Nella 52 la dominante fredda non ha una zona `neutro`, quindi nessuna correzione del bianco.

**Misura dei caratteri** (stima a ~3 caratteri per token; i token veri in fase 0):

| Uscita per foto | Caratteri | Token stimati | Rispetto a v3 |
|---|---|---|---|
| v3, oggi | 514 | ~171 | – |
| schema largo (10.6) | 1.076 | ~358 | +187 |
| **compatto, foto con difetti** | 591 | ~197 | **+26** |
| **compatto, foto buona** (`ritocco: null`) | 441 | ~147 | **−24** |

**Costo stimato per un gruppo da 10 foto** (2,50 $ / 1,25 $ in cache / 10 $ per milione; ~765 token a immagine; media di +15 token di uscita a foto):

| Voce | Oggi (v3) | Compatto, cache mancata | Compatto, cache presa |
|---|---|---|---|
| Prefisso fisso (sistema + schema) | ~1.100 | ~2.250 | ~2.250 a metà prezzo |
| Contesto del gruppo e delle foto | ~100 | ~220 | ~220 |
| Immagini | ~7.700 | ~7.700 | ~7.700 |
| Ingresso | 2,2 ¢ | 2,5 ¢ | 2,3 ¢ |
| Uscita | ~1.710 → 1,7 ¢ | ~1.860 → 1,9 ¢ | 1,9 ¢ |
| **Totale** | **~3,9 ¢** | **~4,4 ¢ (+12%)** | **~4,1 ¢ (+5%)** |

Se il costo deve restare **invariato**, la leva è la `descrizione`, che è circa metà dell'uscita: da 60 a 50 parole recupera ~15 token a foto. È una scelta che tocca la qualità dei testi: va decisa dalla persona, non è inclusa.

### 12.3 Rispettare la cache del prompt

La cache del provider (OpenAI, anche via OpenRouter) è automatica sul **prefisso identico** di almeno 1.024 token, a blocchi di 128, e dura qualche minuto di inattività. Regole:

| # | Regola | Perché |
|---|---|---|
| C1 | Il messaggio di sistema è un file statico: nessuna data, nessun nome di bottega, nessun dato della campagna | basta un byte diverso e il prefisso non è più lo stesso |
| C2 | Lo schema (`response_format`) è deterministico: stesso ordine dei campi, nessun valore calcolato | lo schema fa parte del prefisso |
| C3 | Ordine fisso: sistema, schema, poi il messaggio utente con tutto ciò che cambia | la cache vale solo sul prefisso |
| C4 | Il prefisso fisso resta sopra i 1.024 token (con v4 ~2.250) | sotto la soglia non c'è cache: è il caso di v3 oggi, al limite |
| C5 | Stesso modello per tutte le analisi | la cache è per modello |
| C6 | Le analisi dei gruppi di una campagna partono una dopo l'altra, senza pause | le chiamate dopo la prima trovano il prefisso in cache |
| C7 | Una versione nuova del prompt è un file nuovo (`analisi_v5.md`), mai una modifica sul posto | cambiare il prefisso spegne la cache, va fatto apposta |
| C8 | Se si passa a un modello Anthropic, `cache_control` esplicito sul messaggio di sistema (LiteLLM lo supporta) | lì la cache non è automatica |

**Misurarla:**
- `usage.prompt_tokens_details.cached_tokens` va salvato in una **colonna nuova** di `chiamata_ai` (`token_in_cache`; migrazione approvata con la 11.1).
- Il costo di riserva di `litellm.py::_uso` (ingresso × prezzo) sovrastima le chiamate in cache: va corretto con il prezzo in cache.
- Va verificato se `litellm.completion_cost` conta già i token in cache e se OpenRouter li riporta.

### 12.4 L'operatore: tre varianti a un clic

Sostituisce il pannello della 8.3. Tutti i principi della 8.1 restano.

| Variante | Che cosa contiene | Quando si vede |
|---|---|---|
| **Standard** (predefinita) | la prima modifica completa: correzioni obbligatorie, codice `ruota_*`, e tutte le correzioni del livello 1 con le dosi prudenti della doppia chiave | è l'anteprima della card |
| **Spinta** | la stessa diagnosi con soglie e tetti più ampi, più il livello 2 (tabella sotto) | un clic |
| **Originale** | la foto come scattata, mai vista finora dall'operatore: correzioni obbligatorie tecniche (EXIF, `ruota_*`, **sRGB**, rapporto con le regole di oggi, 1080, JPEG senza metadati). Nessun avvicinamento, nessuna correzione di luce, nessun autocontrasto | un clic |

La conversione sRGB resta anche in Originale: non è un ritocco, è leggere correttamente i colori della foto (12.1).

**Nella card:**

```text
[ anteprima della variante scelta ]
( Originale | Standard ● | Spinta )      Oscura 3 zone  ☐
Ritagliata · Raddrizzata · Luce   ·  vale anche per il post Instagram
⚠ Riflessi sul soggetto → Cambia foto · Chiedi all'artigiano
```

- **Un controllo a tre posizioni** (Mantine `SegmentedControl`) e un interruttore per la privacy.
- **Spinta spenta** se coincide con Standard ("nessuna modifica in più"). Se Standard coincide con Originale, la card dice "Nessuna modifica necessaria". Il confronto si fa sui comandi strutturati, senza rendere niente.
- **Privacy:** un clic per foto ("Oscura N zone"), indipendente dalla variante, oppure un clic per tutta la campagna nel riepilogo di Approva (8.4). Le zone valgono anche in Originale.
- **Altro canale:** la scelta vale per tutti i post della campagna con la stessa foto. L'intervallo è unico, quindi il risultato è lo stesso.
- **Tolti:** ritaglio a mano, cursori, rotazione manuale (la fa il codice `ruota_*`), aggiunta di zone. Se nessuna variante va bene, restano "Cambia foto" e "Chiedi all'artigiano", come oggi. Limite accettato: un volto che né il programma né l'AI hanno segnato si risolve cambiando foto.

**Clic per l'operatore:**

| Caso | Clic |
|---|---|
| La Standard va bene | 0 |
| Serve una correzione più forte | 1 (Spinta) |
| La modifica non convince | 1 (Originale) |
| Zone privacy | 1 per foto, oppure 1 per campagna in Approva |
| Nessuna variante va bene | Cambia foto o Chiedi all'artigiano, come oggi |

**Dati della scelta** (`versione_post_foto.ritocco`, sostituisce la 10.10):

```json
{"variante": "spinta", "privacy": true}
```

`null` vale Standard senza privacy. Ogni cambio crea una versione `ritocca_foto` del post (8.5), senza AI.

### 12.5 Le varianti come comandi strutturati

L2, alla fine della tappa ANALISI, calcola i **tre comandi** e li salva in `foto.analisi_ai["ritocco"]["varianti"]`. Sono pronti prima che l'operatore apra la campagna, deterministici e confrontabili. Questo sostituisce la "proposta non salvata" della 10.9.

```json
{
  "versione_esecutore": "ritocco-1",
  "varianti": {
    "originale": {"ruota": 0, "srgb": true, "finestra": "regole_r42", "luce": null, "nitidezza": false},
    "standard": {
      "ruota": 0, "srgb": true,
      "raddrizza": {"tipo": "prospettiva", "candidato": "Q1"},
      "finestra": {"b": [12, 6, 76, 86], "rapporto": 0.8},
      "luce": {"esposizione": 0.0, "bianco": null, "ombre": 0.0, "flash": 0.0},
      "nitidezza": true
    },
    "spinta": {
      "ruota": 0, "srgb": true,
      "raddrizza": {"tipo": "prospettiva", "candidato": "Q1"},
      "finestra": {"b": [16, 8, 70, 80], "rapporto": 0.8},
      "luce": {"esposizione": 0.0, "bianco": {"r": 1.0, "g": 1.0, "b": 0.96}, "ombre": 0.0, "flash": 0.0},
      "nitidezza": true
    }
  },
  "privacy": [{"id": "z1", "origine": "V1", "b": [11, 30, 6, 5]}, {"id": "z2", "origine": "ai", "b": [83, 40, 4, 5]}],
  "avvisi": ["foto_mossa_lieve"],
  "scarti": [{"correzione": "esposizione", "motivo": "ai_ok_misura_scura"}]
}
```

**Standard e Spinta: dove cambiano** (i numeri sono di partenza, da tarare in fase 0):

| Parametro | Standard | Spinta |
|---|---|---|
| Avvicinamento | solo con `lontana` o `decentrata`, margine 10%, nessun ingrandimento | anche senza nota se il soggetto occupa meno del 40%, margine 5%, ingrandimento fino a 1,3× |
| Intrusi ai bordi | tolti se il taglio resta entro il 15% dell'area | entro il 30% |
| Con `ambiente` | avvicinamento entro il 10% dell'area | entro il 20% |
| Rotazione | 0,5°–5° | 0,5°–8° |
| Prospettiva | deformazione entro l'8% | entro il 15% |
| Esposizione | doppia chiave, tetto ±0,5 stop | doppia chiave con soglia di misura più bassa, tetto ±1 stop |
| Bianco | solo con `neutro`, tetto 5% per canale | con `neutro` tetto 10%; senza, media dei grigi sul soggetto con tetto 4% |
| Ombre (controluce) | lieve | media |
| Flash (caduta ai bordi) | spento | acceso |
| Nitidezza | lieve, se ammessa | media, se ammessa |

**Render:**
- La Standard si rende nel worker a fine generazione: la card si apre già pronta.
- Spinta e Originale si rendono al primo clic (frazioni di secondo), poi restano in cache.
- All'approvazione si salva il render della variante scelta, con la privacy, e la pubblicazione serve quel file (7.6).
- La chiave del render è l'impronta di (comando della variante + privacy + versione dell'esecutore + file originale).

### 12.6 Ingredienti aggiornati, in ordine (non sono task)

1. **Colore sRGB** (12.1): da solo, subito, senza AI. Funzione unica, profilo P3 generato per i test.
2. **Via l'autocontrasto per canale** ed esecutore con ordine fisso (7.5); test sulle 21 foto buone.
3. **Anteprima reale e render salvato:** la card mostra la foto che esce, la pubblicazione serve il file approvato.
4. **Fase 0:** prova sulle foto reali (schema compatto, con e senza segni, token reali, cache misurata).
5. **L1 pre-analisi:** misure, fasce, candidati; numpy e OpenCV in `requirements.txt`.
6. **Prompt `analisi_v4` compatto e schema** (12.2), regole di cache (12.3), colonna `token_in_cache`.
7. **L2:** validatori, doppia chiave, tre comandi (12.5).
8. **Esecutore completo:** finestra, raddrizzamento, luce, privacy.
9. **Tre varianti nella card:** intervento `RITOCCA_FOTO`, migrazione `versione_post_foto.ritocco`, rotta di anteprima, frontend.
10. **Privacy in Approva:** riepilogo e "Oscura tutte".
