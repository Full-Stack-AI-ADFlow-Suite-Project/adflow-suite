# Fuori MVP · regole, criteri, API e job

> **Archiviato il 5/11/2026 (ADR-122).** Era `docs/agenti/spec.md` §7 e le righe `fuori MVP` delle tabelle API e Job di `docs/agenti/plan.md` §3–§4. Non fa testo: è il dettaglio delle voci di `docs/ROADMAP.md`. Le tabelle del modello dati (`plan.md` §2) tengono ancora le loro righe `fuori MVP`, perché le tabelle esistono nel database.

## Dalla spec (§7)
Regole e criteri che non valgono nell'MVP (ADR-114): non si costruiscono né si estendono. Restano qui, con i loro ID, per la roadmap (`docs/ROADMAP.md`). Dove il codice c'è ancora (gruppi `create_ai`, caroselli, archivio) resta, con i suoi test, nascosto nell'interfaccia; il resto lo ha tolto T3-01.

**Regole**

| ID | Regola |
|---|---|
| R-03 (ritocchi) | Max **3** ritocchi della foto per post; scelta e cambio della foto e spostamento non consumano cicli. |
| R-06 (promemoria) | Promemoria all'operatore **48 h** prima dell'inizio. |
| R-07 | Permesso scaduto o account non più collegato alla pubblicazione → campagna `sospesa` + avvisi. Nell'MVP l'errore rende il post `fallito`. |
| R-13 (create_ai) | Gruppi `create_ai` con `n_immagini` da **1** a **20**. Il codice resta; il pulsante per aggiungerli è nascosto. |
| R-17 | Il ritocco vale solo per il post su cui si lavora; l'originale resta. Nell'MVP le foto si sistemano in locale (R-42). |
| R-19 | Immagini AI chieste dall'artigiano con i gruppi `create_ai`, sempre in aggiunta alle foto caricate; gruppo, descrizione e `n_immagini` si salvano fin da subito e la generazione li ignora. Nell'interfaccia il pulsante resta nascosto. Le immagini AI dell'MVP sono solo rimpiazzi (R-28). |
| R-20 | Piano debole: su un canale le foto disponibili sono meno della **metà** dei post chiesti, oppure un gruppo `caricate` non ha nessuna foto idonea; la campagna si ferma in `piano_da_rivedere` e Prosegui la fa ripartire. Nell'MVP il piano non è mai debole; lo stato resta per le righe vecchie. |
| R-23 | Foto con la stella (`da_usare`): se idonea, è sempre in un post del piano; non è mai un doppione (`simile_a` passa all'altra); se sono più dei post chiesti, il piano ne usa almeno quanti sono i post chiesti. Nell'MVP le foto le sceglie il punteggio dell'analisi; la colonna resta. |
| R-29 (ingresso) | L'operatore arriva su una pagina d'ingresso, con le campagne da sistemare. |
| R-37 (anagrafica) | Anagrafica dell'artigiano (codice ART, codice consorzio, telefono, `iscritto_il`, iscrizione sospesa), cambio password obbligato al primo accesso, "Nuova password provvisoria". |
| R-38 (pagine dell'operatore, oltre l'MVP) | Nell'MVP le pagine degli artigiani sono quelle di R-38 (ADR-117). Restano fuori: codice e data d'iscrizione nell'elenco, stato dell'account per canale (scaduto, scollegato), filtri oltre la ricerca; nella pagina artigiano l'anagrafica completa (R-37) e una pagina a parte per le campagne chiuse. |
| R-39 | **Metriche**. Filtri: artigiano, campagna, periodo (`dal`, `al`, sulla data di pubblicazione; **30** giorni se vuoto). Per ogni post l'ultima rilevazione; i totali sono la somma delle ultime rilevazioni, anche divisi per canale. Post `fallito` e `annullato` fuori dalla tabella; a parte il conteggio dei falliti. Nessun grafico. Report settimanale agli operatori; all'artigiano un riepilogo quando la campagna è `conclusa`. |
| R-40 | **Logo della bottega**: JPG, PNG o WEBP, ≤ **2 MB**, lato corto ≥ **300 px**; sta nel profilo e nella fotografia del profilo; va sulle cartoline. Nell'MVP il logo è una foto come le altre; la colonna resta. |

**Criteri**

| ID | Dato → Quando → Allora |
|---|---|
| CA-33 | generazione → ogni foto ha versione ritoccata e l'originale resta |
| CA-34 | foto usata su 2 canali → ritocca per un post → cambia solo quello |
| CA-35 | 3 ritocchi → quarto → 409; scegli originale → ok senza consumare cicli |
| CA-40 | permesso scaduto o account scollegato dopo l'invio → prima pubblicazione → sospesa + avvisi |
| CA-41 | campagne in stati diversi → pagina artigiano → ognuna nella sezione giusta; delle chiuse solo le ultime 3, le altre nella pagina delle campagne chiuse |
| CA-42 | in revisione, inizio tra < 48 h → tick orario → un promemoria, una volta |
| CA-43 | nome diverso tra anagrafica e profilo → pagina artigiano → differenza segnalata |
| CA-44 | post pubblicato → lettura giornaliera → metriche salvate e visibili |
| CA-45 | sistema completo → invio e approvazione → post pubblicati (E2E nel browser) |
| CA-46 | bozza → gruppo `create_ai` con descrizione e `n_immagini` → salvato e restituito nel dettaglio (il codice resta: il test resta) |
| CA-47 | → gruppo `create_ai` con `n_immagini` fuori da 1–20, foto caricata in un gruppo `create_ai`, o `da_usare_il` fuori dal periodo → 422 (il codice resta: il test resta) |
| CA-49 | su un canale foto disponibili sotto la metà dei post chiesti → generazione → `piano_da_rivedere`, nessun testo generato; Prosegui → riparte e arriva a `in_revisione` |
| CA-51 | foto con la stella idonea → è in un post del piano; non idonea → resta fuori, con il motivo; quasi uguale a un'altra senza stella → il doppione è l'altra |
| CA-52 | piano con un carosello → post con più foto in ordine; pubblicato una volta con tutte le foto (caroselli congelati: il test resta) |
| CA-73 | nuovo artigiano → password provvisoria mostrata una volta → al primo accesso deve cambiarla prima di ogni altra pagina |
| CA-74 | iscrizione sospesa → invio → 409; le campagne approvate continuano a uscire |
| CA-75 | metriche senza date → ultimi 30 giorni; per ogni post l'ultima rilevazione; falliti e annullati fuori dalla tabella |
| CA-76 | foto d'archivio idonea mai uscita su un canale → generazione → conta tra le foto disponibili di quel canale; uscita lì da meno di 90 giorni → resta fuori; da più di 90 → torna solo come riempitivo `archivio`; dopo la pubblicazione la foto porta canale e data (archivio congelato: il test resta) |
| CA-77 | profilo con il logo → campagna inviata → le cartoline portano il logo; logo sostituito dopo l'invio → la campagna inviata usa ancora quello di prima |
| CA-78 | → logo che non è un'immagine o > 2 MB → 422 con motivo |


## Dal plan · API (§3)

| Stato | Modulo | Metodo e percorso | Ruolo | Esito |
|---|---|---|---|---|
| fuori MVP | campagne | PUT /foto/{id} `{da_usare}` | artigiano | la stella (tolta da T3-01) |
| fuori MVP | revisione | POST /campagne/{id}/prosegui | operatore | piano_da_rivedere → in_generazione (tolto da T3-01, R-20) |
| fuori MVP | artigiani | PUT, GET, DELETE /profilo/logo | artigiano | il logo della bottega (tolto da T3-01, R-40) |
| fuori MVP | accesso | POST /auth/cambia-password `{password_attuale, password_nuova}` | autenticato | 204; spegne `deve_cambiare_password`; finché è acceso ogni altra chiamata → 403 (R-37) |
| fuori MVP | artigiani | POST /artigiani/{id}/password-provvisoria · POST /artigiani/{id}/social/{piattaforma}/collega | operatore | nuova password provvisoria · collegamento degli account |
| fuori MVP | revisione | POST /post/{id}/ritocca-foto · /scegli-foto | operatore | ritocco e versioni della foto (R-17) |
| fuori MVP | pubblicazione | GET /metriche?artigiano=&campagna=&dal=&al= | operatore; artigiano solo le sue | metriche (R-39) |

## Dal plan · Job (§4)

| Stato | Modulo | Job | Quando | Cosa fa |
|---|---|---|---|---|
| fuori MVP | contenuti | `ritocca_foto(post_id)` | da /ritocca-foto | nuova `versione_foto` e nuova versione del post (R-17) |
| fuori MVP | revisione | `promemoria` | ogni ora | email all'operatore 48 ore prima dell'inizio (R-06) |
| fuori MVP | pubblicazione | `raccogli_metriche` · `report_settimanale` | giorno · settimana | metriche e riepiloghi (R-39) |
