# Ritocco locale supportato dall'AI · note di lavoro

Worktree: `ritocco-locale-supportato-ai` · branch `worktree-ritocco-locale-supportato-ai` · aperto il 7 novembre 2026.
Questo file raccoglie la conversazione che ha portato al lavoro, la valutazione finale, il piano d'azione e un esempio di prompt con output strutturato. È una nota di lavoro, non documentazione di prodotto. Dove un'affermazione e il codice non tornano, vale il codice.

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
