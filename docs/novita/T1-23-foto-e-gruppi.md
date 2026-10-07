# Novità · T1-23 Foto e Gruppi

7 ottobre 2026 · corsia 2 (Silvia) · branch `feature/T1-23-foto-e-gruppi`

## Funzionalità implementate

- `POST /api/campagne/{id}/foto`: caricamento foto per campagna in bozza (`HTTP 201`).
  - Streaming protetto anti-DoS: lettura chunked a blocchi di 64 KB con blocco preventivo immediato e rifiuto se il payload supera 10 MB (Spec R-13, CA-13: `HTTP 422`).
  - Parser binario puro (`immagini.py`) senza dipendenze esterne: ispezione nativa con `struct` per formati PNG (chunk IHDR), JPEG (marker SOF0..SOF15 con salto byte padding `0xFF` e RST), e WebP (VP8 lossy, VP8L lossless bit-packed e VP8X extended canvas a 24-bit).
  - Validazione dimensionale R-13 / CA-13: `min(larghezza, altezza) >= 1080 px` (`HTTP 422`).
  - Protezione Defense in Depth anti-DoS:
    - Limite dimensioni estreme `MAX_WIDTH = 8192` e `MAX_HEIGHT = 8192` (`HTTP 422`);
    - Protezione Decompression Bomb / Pixel Flood: `MAX_PIXELS = 36_000_000` (`HTTP 422`).
  - Sanificazione totale del nome file: memorizzazione su archivio con UUIDv4 univoco generato dal server (Constitution §3).
  - Compensazione atomica anti-TOCTOU: in caso di eccezione a livello database durante la registrazione della foto, il file fisico scritto su disco viene immediatamente rimosso (zero file orfani garantito).
  - Gestione gruppi: generazione automatica di un nuovo UUID per il gruppo o associazione a un gruppo esistente della campagna con ereditarietà automatica della descrizione già impostata.
- `PUT /api/campagne/{id}/gruppi/{gruppo_id}`: aggiornamento descrizione del gruppo (`HTTP 200`).
  - Copia e sincronizzazione atomica della descrizione su tutte le foto appartenenti al gruppo indicato.
  - Vincolo di stato: consentito solo per campagne in stato `bozza` (`HTTP 409`).
  - Riservatezza CA-04: solo l'artigiano proprietario può aggiornare il gruppo (`HTTP 404` per altri artigiani).
- `DELETE /api/foto/{id}`: eliminazione singola foto (`HTTP 204`).
  - Rimozione atomica anti-TOCTOU: cancellazione dal database per prima con `flush()` e rimozione del file fisico dall'archivio solo a successo DB confermato.
  - Consentito solo per campagne in stato `bozza` (`HTTP 409`) dall'artigiano proprietario (`HTTP 404` ad altri).
- `DELETE /api/campagne/{id}/gruppi/{gruppo_id}`: eliminazione atomica dell'intero gruppo (`HTTP 204`).
  - Eliminazione di tutte le foto del gruppo da database e rimozione dei rispettivi file fisici dall'archivio.
  - Consentito solo per campagne in stato `bozza` (`HTTP 409`) dall'artigiano proprietario.
- `GET /api/foto/{id}/file`: download file originale dall'archivio (`HTTP 200`).
  - Streaming dei byte con Content-Type corrispondente (`image/png`, `image/jpeg`, `image/webp`).
  - Autorizzazioni granulari: consentito all'artigiano proprietario e agli operatori/admin del consorzio; `HTTP 404` per artigiani terzi (CA-04).

## Test e Robustezza

- Suite completa in `tests/moduli/campagne/test_foto_gruppi.py`:
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
- 224 test totali passati con successo su tutta la suite locale.
