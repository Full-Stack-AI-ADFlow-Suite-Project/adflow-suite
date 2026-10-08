# Novità · T1-23 Foto e Gruppi

8-9 ottobre 2026 · corsia 2 (Silvia) · branch `feature/T1-23-foto-e-gruppi`

## Funzionalità implementate

- `POST /api/campagne/{id}/gruppi`: creazione esplicita di un gruppo di foto (`HTTP 201`).
  - Supporta sia gruppi di origine `caricate` (foto manuali) sia `create_ai` (foto generate dal modello AI, CA-46).
  - Validazione date (CA-47): se specificato `da_usare_il`, deve ricadere tra `data_inizio` e `data_fine` della campagna (`HTTP 422`).
  - Validazione immagini AI (CA-47): per gruppi `create_ai`, `n_immagini` deve essere compreso tra 1 e 20 (`HTTP 422`).
  - Consentito solo per campagne in stato `bozza` (`HTTP 409`) e dall'artigiano proprietario (CA-04: `HTTP 404` per campagne altrui).
- `PUT /api/campagne/{id}/gruppi/{gruppo_id}`: aggiornamento metadati del gruppo (`HTTP 200`).
  - Consente l'aggiornamento di `descrizione`, `da_usare_il` e `n_immagini`.
  - Vincolo di stato: consentito solo per campagne in stato `bozza` (`HTTP 409`).
  - Riservatezza CA-04: solo l'artigiano proprietario può aggiornare il gruppo (`HTTP 404` ad altri artigiani).
- `DELETE /api/campagne/{id}/gruppi/{gruppo_id}`: eliminazione atomica dell'intero gruppo (`HTTP 204`).
  - Eliminazione di tutte le foto del gruppo da database e rimozione dei rispettivi file fisici dall'archivio con pulizia sicura post-commit.
  - Consentito solo per campagne in stato `bozza` (`HTTP 409`) dall'artigiano proprietario.
- `POST /api/campagne/{id}/foto`: caricamento foto per campagna in bozza (`HTTP 201`).
  - Controllo del peso: lettura a blocchi di 64 KB con rifiuto oltre 10 MB (Spec R-13, CA-13: `HTTP 422`).
  - Parser binario puro (`immagini.py`) senza dipendenze esterne: ispezione nativa con `struct` per formati PNG (chunk IHDR), JPEG (marker SOF0..SOF15 con salto byte padding `0xFF` e RST), e WebP (VP8 lossy, VP8L lossless bit-packed e VP8X extended canvas a 24-bit).
  - Validazione dimensionale R-13 / CA-13: `min(larghezza, altezza) >= 1080 px` (`HTTP 422`).
  - Protezione Defense in Depth anti-DoS:
    - Limite dimensioni estreme `MAX_WIDTH = 8192` e `MAX_HEIGHT = 8192` (`HTTP 422`);
    - Protezione Decompression Bomb / Pixel Flood: `MAX_PIXELS = 36_000_000` (`HTTP 422`).
  - Sanificazione totale del nome file: memorizzazione su archivio con UUIDv4 univoco generato dal server (Constitution §3).
  - Compensazione transazionale: il file viene scritto prima del record; se il flush fallisce o la transazione termina con un rollback (anche dopo la risposta), il file viene rimosso. Se il processo si interrompe di colpo resta un file orfano, innocuo.
  - Associazione a gruppo: supporta l'ID del gruppo (`gruppo_id: int`); se omesso, viene creato automaticamente un gruppo `caricate`.
  - Blocco upload manuale su gruppi AI (CA-47): se il gruppo specificato ha `origine="create_ai"`, l'upload manuale viene bloccato con `HTTP 422`.
- `PUT /api/foto/{id}`: contrassegno stella foto per la generazione (`HTTP 200`).
  - Consente di impostare il flag `da_usare: bool` per marcare la foto da utilizzare (Plan §3).
  - Consentito solo in stato `bozza` (`HTTP 409`) dall'artigiano proprietario (`HTTP 404` per altri).
- `DELETE /api/foto/{id}`: eliminazione singola foto (`HTTP 204`).
  - Il file fisico viene cancellato solo dopo il commit riuscito (non dopo il `flush()`): se la transazione viene annullata restano record e file. Un errore del disco dopo il commit viene registrato nel log e lascia al massimo un file orfano.
  - Consentito solo per campagne in stato `bozza` (`HTTP 409`) dall'artigiano proprietario (`HTTP 404` ad altri).
- `GET /api/foto/{id}/file`: download file originale dall'archivio (`HTTP 200`).
  - Streaming dei byte con Content-Type corrispondente (`image/png`, `image/jpeg`, `image/webp`).
  - Autorizzazioni granulari: consentito all'artigiano proprietario e agli operatori/admin del consorzio; `HTTP 404` per artigiani terzi (CA-04).

## Test e Robustezza

- Suite completa in `tests/moduli/campagne/test_foto_gruppi.py` (49 test):
  - `test_ca13_rifiuto_file_non_immagine` (422)
  - `test_ca13_rifiuto_payload_oltre_10mb` (422)
  - `test_ca13_rifiuto_lato_corto_inferiore_1080px` (422)
  - `test_ca13_accettazione_png_jpeg_webp_conformi` (201)
  - `test_sicurezza_rifiuto_dimensioni_eccessive` (422)
  - `test_sicurezza_rifiuto_decompression_bomb_max_pixels` (422)
  - `test_ca04_upload_su_campagna_altrui_da_404` (404)
  - `test_upload_richiede_ruolo_artigiano` (403)
  - `test_upload_su_campagna_non_in_bozza_da_409` (409)
  - `test_gestione_gruppi_e_descrizione` (201, 200, ereditarietà)
  - `test_aggiornamento_descrizione_gruppo_campagna_non_in_bozza_da_409` (409)
  - `test_aggiornamento_descrizione_gruppo_inesistente_da_404` (404)
  - `test_eliminazione_foto_singola` (204 e pulizia disco)
  - `test_eliminazione_foto_campagna_non_in_bozza_da_409` (409)
  - `test_ca04_eliminazione_foto_altrui_da_404` (404)
  - `test_eliminazione_gruppo_completo` (204 e pulizia disco)
  - `test_download_file_foto` (200, test proprietario vs operatore vs terzo)
  - `test_compensazione_rollback_disco_se_db_fallisce` (anti-TOCTOU, zero file orfani)
  - `test_debug_jpeg_malformato_marker_inatteso` (422)
  - `test_debug_jpeg_malformato_senza_sof` (422)
  - `test_debug_png_troncato_o_senza_ihdr` (422)
  - `test_debug_webp_chunk_sconosciuto` (422)
  - `test_debug_confini_esatti_1080_e_1079` (201/422 al pixel)
  - `test_debug_gruppo_di_altra_campagna_vietato` (422)
  - `test_debug_descrizione_gruppo_caratteri_non_validi` (422 su NUL e spazi)
  - `test_debug_download_file_non_trovato_su_disco_da_404` (404)
  - `test_debug_upload_multipli_nello_stesso_gruppo` (201, coerenza multi-upload)
  - `test_debug_webp_vp8_lossy_e_vp8l_lossless` (201, VP8 lossy e VP8L lossless bit-packed)
  - `test_debug_anti_spoofing_estensione_file` (201, rilevamento magic bytes reali JPEG mascherato da PNG, CWE-434)
  - `test_debug_upload_file_vuoto_da_422` (422 su file a zero byte)
  - `test_debug_matrice_stati_non_bozza_vietati` (409 per tutti i 10 stati non-bozza)
  - `test_debug_dettaglio_campagna_con_struttura_foto_completa` (200, aggregato multi-gruppo verificato)
  - `test_debug_concorrenza_reale_upload_multi_thread` (201, 4 thread concorrenti su stesso gruppo)
  - `test_upload_con_rollback_rimuove_il_file_orfano` (rollback dopo upload, nessun file residuo)
  - `test_rollback_successivo_non_tocca_i_file_gia_confermati` (nessun effetto su foto già confermate)
  - `test_eliminazione_con_rollback_conserva_file_e_record` (DELETE annullata, tutto intatto)
  - `test_limite_massimo_20_foto_per_campagna` (422 al 21-esimo upload, nessun file orfano su disco)
  - `test_ca46_creazione_gruppo_create_ai_con_descrizione_e_n_immagini` (201, gruppo AI valido con data e n_immagini)
  - `test_ca47_gruppo_create_ai_n_immagini_fuori_limite_da_422` (422 se n_immagini < 1 o > 20)
  - `test_ca47_foto_caricata_in_gruppo_create_ai_da_422` (422 se si carica manualmente foto in gruppo create_ai)
  - `test_ca47_gruppo_da_usare_il_fuori_dal_periodo_da_422` (422 se data gruppo non compresa tra data_inizio e data_fine)
  - `test_stella_foto_put_da_usare` (200 toggle stella, 409 fuori bozza, 404 altrui)
  - `test_debug_form_upload_con_gruppo_id_stringa_vuota` (201, tolleranza su stringhe vuote da FormData)
  - `test_debug_form_upload_con_gruppo_id_alfanumerico_invalido` (422, validazione esplicita su id gruppo malformato)
  - `test_debug_png_con_dimensioni_zero_da_422` (422, protezione su dimensioni nulle o negative PNG)
  - `test_debug_webp_con_dimensioni_zero_da_422` (422, protezione su dimensioni nulle VP8)
  - `test_debug_gruppo_da_usare_il_uguale_a_inizio_e_fine` (201 e 200, validità dei confini esatti della campagna)
  - `test_debug_operatore_puo_scaricare_foto_in_campagna_conclusa` (200, download foto consentito all'operatore in qualunque stato)
  - `test_debug_concorrenza_upload_limite_20_foto` (concorrenza serializzata con row-lock PostgreSQL, limite 20 foto per gruppo rispettato)
- **261 test totali verdi** su tutta la suite locale (224 in `moduli/campagne`, 19 in `test_confini.py`, 18 in `adapters/archivio`).

## Limiti e Misure di Sicurezza Applicate

- **Quantità di foto per campagna**: introdotto un tetto prudenziale di 20 foto per campagna (`MAX_FOTO_PER_CAMPAGNA = 20`), con blocco a livello di servizio (`HTTP 422`) prima della scrittura su disco.

## Domande Formali per la Corsia 0 (Comune)

Secondo la Costituzione del Progetto (§2) e `tasks.md`, i componenti comuni (`requirements.txt`, `main.py`, middleware) possono essere modificati solo attraverso domande e task di Corsia 0. Di seguito il testo pronto per le due segnalazioni:

### Domanda 1: Aggiunta di `python-multipart` a `backend/requirements.txt`

> **Oggetto**: [Corsia 0 · Dipendenze] Inserimento di `python-multipart` in `requirements.txt` > **Contesto**: L'endpoint di caricamento foto `POST /campagne/{id}/foto` (T1-23) utilizza `UploadFile` e parametri `Form` di FastAPI.
> **Problema**: FastAPI delega il parsing del formato `multipart/form-data` alla libreria `python-multipart`. Sebbene sia presente nell'ambiente virtuale di sviluppo locale, non è dichiarata esplicitamente in `requirements.txt`.
> **Richiesta per Corsia 0**: Aggiungere `python-multipart>=0.0.9` (o versione compatibile) a `backend/requirements.txt` per garantire l'installazione deterministica negli ambienti di CI e produzione.

### Domanda 2: Protezione anti-DoS sul body HTTP a monte (`main.py` o reverse proxy)

> **Oggetto**: [Corsia 0 · Sicurezza] Limite massimo sulla dimensione del body HTTP in streaming
> **Contesto**: Il servizio foto (Corsia 2) rifiuta file con dimensione > 10 MB tramite streaming a blocchi (`DIMENSIONE_MAX_BYTE = 10 * 1024 * 1024`).
> **Problema**: Lo stack Starlette/FastAPI accetta lo stream della richiesta prima che il router applichi i controlli specifici. Un client malevolo potrebbe tentare un DoS saturando la banda o lo storage temporaneo (`tempfile`) con payload di svariati gigabyte prima che scatti il controllo applicativo.
> **Richiesta per Corsia 0**: Valutare l'introduzione di un middleware in `main.py` che controlli l'header `Content-Length` (o limiti i byte letti dalla request raw), oppure definire la direttiva di reverse proxy (es. `client_max_body_size 15M;` in Nginx / proxy di ingresso) a protezione di tutta l'applicazione.
