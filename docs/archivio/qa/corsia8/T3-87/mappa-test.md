# T3-87 - Mappa dei test rispetto ai nove passi di converge §4

Mappa statica dei test **esistenti**, ricavata leggendo `docs/agenti/converge.md`, spec §6 e `backend/tests`. Non è un verbale di esecuzione: in questo incarico non è stato lanciato pytest né dichiarato alcun test PASS. L'esito della suite completa è responsabilità della distinta esecuzione del controller.

Tutti i percorsi sotto sono relativi alla radice del repository `work/adflow-t385`. La notazione `file::test` identifica il test esistente. I CA sono quelli citati dal percorso e dai test, non nuovi criteri aggiunti per T3-87.

## Quadro dei nove passi

| Passo converge §4                                                        | Copertura backend presente                                             | Parte che richiede prova esterna a pytest                                                      |
| ------------------------------------------------------------------------ | ---------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| 1 - Nuovo artigiano, password una volta, ingresso al profilo             | CA-79, creazione/login/profilo assente, ruoli e duplicati              | Password mostrata una volta nell'interfaccia, navigazione effettiva al passo 1                 |
| 2 - Bentornato, campagna breve con poche foto, riepilogo e dichiarazione | CA-54, CA-14; validazione periodo/canali e invio                       | Bentornato, compilazione dei passi 10-12, numero visibile nel riepilogo, foto vere della demo  |
| 3 - Generazione, foto migliori, immagini AI/dicitura, costo              | CA-17, CA-57, CA-80, CA-82                                             | AI reale, qualità dei risultati e costo mostrato in Vedi campagna                              |
| 4 - Revisione, richiesta/riposta foto, approvazione e calendario         | CA-64/26/71/86/87/88/90/21/56 e CA-91 integrato                        | Due finestre/ruoli nel browser, upload e aggiornamento effettivo delle schermate               |
| 5 - Pubblicazione e foto corretta sui social                             | CA-81 e CA-83, più CA-36/37/38/39; adattatore Meta simulato            | Post visibile sulla pagina Facebook/Instagram reale, tunnel e credenziali/configurazione reali |
| 6 - Interventi dopo approvazione, sospendi/riattiva                      | CA-84, CA-72, CA-85, CA-32; CA-91 integrato                            | Interazioni browser e testo «Pubblicazioni ferme» realmente visibile all'artigiano             |
| 7 - Confronto visivo con statiche e larghezze S2                         | Nessuna certificazione visiva backend; CA-99 copre i dati delle pagine | Tutti gli screenshot, layout 375/1280, tocco/font/focus/scroll/console                         |
| 8 - Respinta con motivo foto, nota, foto segnate e vista artigiano       | CA-24, CA-25, CA-31                                                    | Scelta delle foto nella UI, visualizzazione nell'altra sessione                                |
| 9 - Prove negative                                                       | CA-09/10/13/48/03/61/29/89/22/79                                       | Riscontri dei messaggi e delle schermate nel percorso manuale                                  |

## Test concreti per passo

### 1. Nuovo artigiano - CA-79

In `backend/tests/moduli/artigiani/test_nuovo_artigiano.py`:

- `test_ca79_crea_login_profilo_e_account_come_seed`: parametrizzato per operatore/admin; crea l'account, controlla password nella sola risposta iniziale/no-store e assenza nei log/letture successive, login reale con la password, GET profilo 404 prima della compilazione, salvataggio profilo e canali seed.
- `test_ca79_email_duplicata_normalizzata_non_riespone_password`: conflitto senza riesposizione della password.
- `test_ca79_artigiano_403_e_anonimo_401`: permessi dell'API di creazione.

Il profilo 404 prova lo stato iniziale del backend; non prova l'arrivo della SPA al passo 1.

### 2. Campagna e invio - CA-54, CA-14

- `backend/tests/moduli/campagne/test_api_bozza.py::test_ca54_dettaglio_calcolo_post_chiesti_e_avvisi`: conteggio `post_chiesti_per_canale` e avvisi con zero/quattro foto. I dati del riepilogo sono coperti, il rendering del passo 12 no.
- `backend/tests/moduli/campagne/test_invio_riprova.py::test_ca14_dichiarazione_obbligatoria`: rifiuto senza dichiarazione.
- Nello stesso file: `test_ca14_una_foto_invio_ammesso`, `test_ca14_tre_foto_invio_ammesso`, `test_ca14_senza_foto_invio_ammesso` e `test_ca15_invio_salva_snapshot_e_accoda` coprono poche/zero foto, invio e job.
- `backend/tests/percorsi/test_percorso_sprint1.py::test_percorso_con_poche_foto_e_le_immagini_ai` integra il caso con dati/provider di prova.

### 3. Generazione - CA-17, CA-57, CA-80, CA-82

In `backend/tests/moduli/contenuti/test_generazione.py`:

- `test_ca17_sei_uscite_sei_post_per_canale_cinque_foto_e_un_immagine_ai`.
- `test_ca57_i_post_che_mancano_sono_immagini_ai_con_la_loro_immagine_e_il_loro_testo` e `test_ca57_senza_foto_la_campagna_e_tutta_di_immagini_ai`.
- `test_ca80_all_ai_vanno_le_foto_migliori_per_punteggio_e_le_altre_restano_fuori` e `test_ca80_il_piano_riceve_solo_le_foto_preselezionate`.

Inoltre:

- `backend/tests/moduli/contenuti/test_immagini_ai.py::test_il_testo_dei_rimpiazzi_porta_la_dicitura_in_fondo_gli_altri_no` verifica la dicitura; `test_ogni_immagine_ha_la_sua_riga_di_costo` la registrazione del costo immagini.
- `backend/tests/moduli/contenuti/test_chiamate_ai.py::test_ca82_ogni_chiamata_della_generazione_ha_il_suo_costo`: registra analisi/piano/testi/immagini e controlla `vedi_campagna(...).costo_ai`, usando costi/provider finti. Non certifica visualizzazione UI né addebiti del fornitore reale.
- `backend/tests/moduli/contenuti/test_piano.py::test_ca17_limiti_sei_post_chiesti_cinque_foto_e_un_immagine_ai` e `test_ca80_limiti_le_foto_migliori_per_punteggio_fino_ai_post_chiesti` coprono le regole del piano.

### 4. Revisione e scambio foto - CA-64, CA-26, CA-71, CA-86/87/88/90, CA-21, CA-56

- `backend/tests/moduli/revisione/test_interventi.py::test_ca64_modifica_nasce_una_versione_con_autore_e_foto_uguali`.
- Nello stesso file: `test_ca26_rigenera_da_zero_accende_intervento_e_accoda` e `test_ca71_cambia_foto_in_revisione_via_api`.
- `backend/tests/moduli/contenuti/test_rigenera.py::test_ca26_da_zero_nuova_versione_con_le_stesse_foto_validata` copre l'esecuzione della rigenerazione col provider finto.
- `backend/tests/moduli/campagne/test_richiesta.py`: `test_ca86_chiedi_all_artigiano_con_domanda_e_due_foto`, `test_ca87_carica_la_foto_nuova_con_la_dichiarazione`, `test_ca88_invia_la_risposta`, `test_ca88_da_approvare_segna_la_richiesta`, `test_ca90_l_artigiano_vede_la_richiesta_e_nessun_post`, `test_ca90_la_campagna_con_la_richiesta_si_apre_per_prima`.
- `backend/tests/moduli/revisione/test_router.py::test_ca21_approva_in_blocco`.
- `backend/tests/moduli/contenuti/test_calendario.py::test_ca56_calendario_dopo_approvazione_per_ruoli_ammessi` e `test_ca56_giorni_e_ora_roma_con_passaggio_ora_legale`.
- **Percorso integrato CA-91:** `backend/tests/percorsi/test_percorso_corsia6.py::test_ca91_richiesta_cambia_foto_approva_pubblica` esegue la richiesta, cambio ruolo, upload dichiarato, risposta, scelta della foto nuova, approvazione e tick di pubblicazione. Usa API vere in TestClient e AI/social/archivio finti, non due finestre browser.

### 5. Pubblicazione - CA-81, CA-83 e controlli worker

- `backend/tests/moduli/campagne/test_sistemazione_foto.py::TestSistemazioneFotoCA81::test_ca81_sistemazione_instagram`: PNG con orientamento/GPS convertita in JPEG 1080, proporzioni previste, GPS rimosso, originale immutato. Nella stessa classe: `test_ca81_forzatura_proporzione_quattro_quinti`, `test_ca81_forzatura_proporzione_uno_a_uno`.
- `backend/tests/moduli/campagne/test_foto_pubblica.py::test_api_download_foto_con_metadati_gps_rimossi` e `test_api_download_foto_pubblica_anonimo_successo`: accesso HTTP alla copia sistemata in ambiente di test.
- `backend/tests/adapters/social/test_meta.py`: `test_facebook_pubblica_con_foto_e_didascalia`, `test_instagram_pubblica_con_contenitore_pronto`, `test_instagram_contenitore_in_errore_e_definitivo`, `test_timeout_e_errore_temporaneo`, `test_5xx_e_errore_temporaneo`.
- `backend/tests/moduli/pubblicazione/test_service.py`: `test_ca36_post_approvato_dovuto_viene_pubblicato`, `test_ca36_due_tick_pubblicano_una_volta_sola`, `test_ca37_post_di_campagna_non_attiva_non_pubblicato`, `test_ca38_errore_definitivo_fallisce_subito`.

**Precisazione CA-83:** esiste nel docstring del file `test_meta.py`, con `httpx.MockTransport`. I nomi delle funzioni non iniziano con `test_ca83_`; il solo grep dei nomi `test_ca` può quindi dare un falso negativo nella mappa CA. Questi test verificano risposte/ID e classificazione errori simulati, non una pubblicazione sulla pagina Meta reale.

### 6. Dopo l'approvazione - CA-84, CA-72, CA-85, CA-32

- `backend/tests/moduli/revisione/test_interventi.py`: `test_ca84_modifica_dopo_l_approvazione_ha_la_riga_approvazione`, `test_ca72_sposta_dopo_l_approvazione`, `test_ca85_annulla_il_post_con_la_nota`.
- `backend/tests/moduli/contenuti/test_modifica_a_mano.py::test_ca84_dopo_l_approvazione_oltre_15_minuti_nasce_la_versione`.
- `backend/tests/moduli/revisione/test_sospensione.py`: `test_ca32_sospendi_con_la_nota`, `test_ca32_sospendi_ferma_la_pubblicazione`, `test_ca32_riattiva_pubblica_solo_gli_scelti`.
- **Percorso integrato CA-91:** `backend/tests/percorsi/test_percorso_corsia6.py::test_ca91_dopo_l_approvazione_modifica_sposta_annulla_sospendi_riattiva`, con tick e verifica della pubblicazione del testo/versione corretti, escluso il post annullato.

### 7. Confronto visivo - copertura backend solo dei dati

`backend/tests/percorsi/test_pagine_corsia7.py::test_ca99_percorso_pagine` controlla via API elenco/scheda artigiano, campagne, archivio con visibilità differenziata delle immagini AI e calendario dei due ruoli. `backend/tests/moduli/contenuti/test_settimana.py` aggiunge `test_ca97_sette_giorni_anche_vuoti` e `test_ca98_operatore_tutti_gli_artigiani_con_la_bottega`.

Il nome «percorso pagine» non indica un test frontend: nessuno di questi confronta HTML/CSS/screenshot delle pagine statiche con React, né misura viewport, font o bersagli tocco. Il PASS di pytest non chiude il passo 7 e non sostituisce le evidenze di T3-87.

### 8. Respinta - CA-24, CA-25, CA-31

- `backend/tests/moduli/revisione/test_decisioni.py::test_ca24_respingi_senza_motivo_o_nota_422`.
- Nello stesso file: `test_ca25_respingi_foto_scarta_i_post_e_avvisa`.
- `backend/tests/moduli/campagne/test_viste_artigiano.py::test_dettaglio_respinta_motivo_nota_e_foto_segnate_ca31`.
- `backend/tests/percorsi/test_revisione_sprint2b_ca.py::test_ca24_respingi_incompleta_e_ca25_email_e_ca31_viste` integra motivo/nota/foto, scarto post, notifica finta con allegati e dettaglio letto dall'artigiano. La valutazione che le foto reali non siano della bottega rimane umana.

### 9. Prove negative - riscontri puntuali

| Rifiuto richiesto dalla demo          | Test esistente                                                                                                                                                                                                              |
| ------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Inizio tra 1 giorno e durata 3 giorni | `backend/tests/percorsi/test_percorso_sprint2a.py::test_prove_negative_del_percorso_sprint2a` contiene esattamente i due payload e attende 422; CA-09/CA-10                                                                 |
| PDF al posto della foto               | stesso percorso; inoltre `backend/tests/moduli/campagne/test_foto_gruppi.py::test_ca13_rifiuto_file_non_immagine`                                                                                                           |
| Canale non collegato                  | `backend/tests/moduli/campagne/test_api_bozza.py::test_ca48_creazione_canale_non_collegato_da_422`; invio dopo scollegamento: `backend/tests/moduli/campagne/test_invio_riprova.py::test_ca48_canale_scollegato_all_invio`  |
| Artigiano escluso, admin ammesso      | `backend/tests/moduli/accesso/test_sessione_permessi.py::test_ca03_artigiano_non_accede_a_funzione_operatore`; `backend/tests/percorsi/test_stati_e_contratti.py::test_ca61_admin_passa_come_operatore_ma_non_artigiano`    |
| Rigenera su attiva                    | `backend/tests/moduli/revisione/test_interventi.py::test_ca29_in_campagna_attiva_o_sospesa_gli_interventi_409`; anche `backend/tests/moduli/contenuti/test_rigenera.py::test_ca29_in_campagna_attiva_409`                   |
| Modifica entro 15 minuti              | `backend/tests/moduli/contenuti/test_modifica_a_mano.py::test_ca29_dopo_l_approvazione_entro_15_minuti_409`; stesso caso via API nel test_interventi CA-29 sopra                                                            |
| Upload artigiano dopo approvazione    | `backend/tests/moduli/campagne/test_richiesta.py::test_ca89_dopo_l_approvazione_caricare_o_inviare_409`; upload ordinario: `backend/tests/moduli/campagne/test_foto_gruppi.py::test_upload_su_campagna_non_in_bozza_da_409` |
| Approva con post da rivedere          | `backend/tests/moduli/revisione/test_router.py::test_ca22_approva_con_da_rivedere_409`                                                                                                                                      |
| Email nuovo artigiano già usata, 409  | `backend/tests/moduli/artigiani/test_nuovo_artigiano.py::test_ca79_email_duplicata_normalizzata_non_riespone_password`                                                                                                      |

Le API di autorizzazione sono coperte; il routing client che impedisce la pagina dell'operatore è un distinto riscontro browser. Alcuni docstring storici dei percorsi citano numeri di passo precedenti: questa mappa usa l'attuale elenco di nove passi di converge, non quei numeri storici.

## Cosa il pytest automatico non certifica

1. **AI/Meta reali.** `backend/tests/conftest.py:9-10` forza provider finti anche se la demo configura quelli veri. `test_litellm.py` sostituisce `litellm.completion` e `litellm.image_generation` con finte; `test_meta.py` usa MockTransport. Non certifica token live, permessi pagina, tunnel pubblico, accesso Meta alle immagini, idoneità dell'account Instagram, qualità delle generazioni, addebiti effettivi o presenza del post sui social.
2. **Demo nelle due finestre.** I cambi ruolo dei test avvengono in client API/fixture, non nelle due sessioni SPA aperte contemporaneamente. Non certifica menu/focus, sincronizzazione delle schermate, ricariche, upload via selettore del telefono o correttezza del collegamento frontend alle API al posto degli esempi.
3. **Visuale e accessibilità di S2.** Nessuna attestazione di screenshot prima/dopo, equivalenza con statiche, layout 375/1280, assenza di overflow/zoom, font 16px, target 44px, gerarchia cromatica, tastiera/focus o console browser. Queste sono evidenze manuali/strumentali separate.
4. **Prova con persone.** La suite non rappresenta le due persone/artigiani, i propri telefoni, le sessioni da 30 minuti e le osservazioni di T3-86. Neppure il controllo automatizzato del browser sostituisce questa prova.
5. **Integrazione di consegna.** Il DB dei test è ricreato/migrato e le fixture `db` usano rollback; la coda è normalmente InMemoryConnector e l'ora è controllata. Anche i percorsi integrati non attestano da soli main pulito, seed T3-06 reale, processi API/worker autonomi, tunnel, catcher email reale, screenshot nella PR e video di riserva.

La suite completa può dare evidenza forte sulle regole/API e sui percorsi integrati con provider finti. Il verbale T3-87 deve riportare separatamente esito pytest, prove browser e prova AI/Meta reale, senza trasformare il primo in un PASS degli altri.
