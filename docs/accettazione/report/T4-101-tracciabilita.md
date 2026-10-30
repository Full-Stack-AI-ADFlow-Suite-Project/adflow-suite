# T4-101 · Matrice di tracciabilità requisito → CA → test

Generata da `docs/accettazione/strumenti/tracciabilita.py` (T4-101,
corsia 10): legge `docs/agenti/spec.md` (§5 regole, §6 criteri,
§7 fuori MVP) e i nomi dei test di `backend/tests`. Il contratto è
quello di spec §6: il test porta l'ID nel nome (`test_ca09_...`).

- regole del perimetro (§5): **43**;
- criteri del perimetro (§6): **96**;
- fuori MVP (§7): **33** tra regole e criteri;
- criteri coperti da almeno un test: **95 di 96**.

## Tabella CA → regole citate → test

| CA | Regole citate | Test |
|---|---|---|
| CA-01 | — | moduli/accesso/test_auth.py::test_ca01_login_utente_attivo_con_il_suo_ruolo |
| CA-02 | — | moduli/accesso/test_auth.py::test_ca02_credenziali_errate_non_rivelano_il_dato_sbagliato |
| CA-03 | — | 3 test: moduli/accesso/test_accesso_revisione.py |
| CA-04 | — | 4 test: moduli/campagne/test_api_bozza.py |
| CA-05 | — | moduli/artigiani/test_profilo.py::test_ca05_profilo_assente_restituisce_404 |
| CA-06 | — | moduli/artigiani/test_profilo.py::test_ca06_crea_legge_e_modifica_senza_duplicare |
| CA-07 | — | moduli/artigiani/test_profilo.py::test_ca07_obbligatorio_mancante_non_crea |
| CA-08 | — | moduli/campagne/test_modifica_bozza.py::test_ca08_modifica_bozza_successo_restituisce_dettaglio_completo |
| CA-09 | — | 4 test: moduli/campagne/test_api_bozza.py |
| CA-10 | — | moduli/campagne/test_api_bozza.py::test_ca10_durata_superiore_92_giorni_o_fine_prima_inizio_da_422<br>moduli/campagne/test_modifica_bozza.py::test_ca10_modifica_durata_non_valida_da_422 |
| CA-11 | — | moduli/campagne/test_api_bozza.py::test_ca11_bozza_esistente_nuova_bozza_da_409 |
| CA-12 | — | moduli/campagne/test_api_bozza.py::test_ca12_periodo_sovrapposto_campagna_attiva_ammesso |
| CA-13 | — | 5 test: moduli/campagne/test_foto_gruppi.py |
| CA-14 | R-41 | 10 test: moduli/campagne/test_invio_riprova.py |
| CA-15 | — | moduli/campagne/test_invio_riprova.py::test_ca15_invio_salva_snapshot_e_accoda |
| CA-16 | — | moduli/artigiani/test_profilo.py::test_ca16_modifica_profilo_non_altera_snapshot |
| CA-17 | — | 3 test: adapters/ai/test_ai.py |
| CA-18 | — | moduli/contenuti/test_generazione.py::test_ca18_testo_con_un_blocco_dopo_tre_riscritture_il_post_e_da_rivedere<br>moduli/contenuti/test_generazione.py::test_ca18_testo_con_i_soli_avvisi_non_e_da_rivedere_e_gli_avvisi_si_salvano |
| CA-19 | — | moduli/campagne/test_invio_riprova.py::test_ca19_ca50_riprova_conserva_snapshot_e_analisi<br>moduli/contenuti/test_generazione.py::test_ca19_errore_temporaneo_a_ogni_esecuzione_tre_esecuzioni_poi_fallita |
| CA-20 | — | moduli/contenuti/test_generazione.py::test_ca20_generazione_riuscita_piano_salvato_e_campagna_in_revisione |
| CA-21 | — | moduli/revisione/test_router.py::test_ca21_approva_in_blocco<br>moduli/revisione/test_router.py::test_ca21_post_passato_diventa_scaduto |
| CA-22 | — | 3 test: moduli/revisione/test_router.py |
| CA-23 | — | moduli/revisione/test_decisioni.py::test_ca23_nota_interna_stato_invariato_e_nessuna_email<br>percorsi/test_revisione_ca.py::test_ca23_nota_interna_privata_e_ca69_elenco_urgente |
| CA-24 | — | moduli/revisione/test_decisioni.py::test_ca24_respingi_senza_motivo_o_nota_422<br>percorsi/test_revisione_ca.py::test_ca24_respingi_incompleta_e_ca25_email_e_ca31_viste |
| CA-25 | — | moduli/notifiche/test_jobs.py::test_ca25_email_respinta_con_motivo_nota_e_miniature<br>moduli/revisione/test_decisioni.py::test_ca25_respingi_foto_scarta_i_post_e_avvisa |
| CA-26 | — | 3 test: moduli/contenuti/test_rigenera.py |
| CA-27 | — | 3 test: moduli/contenuti/test_rigenera.py |
| CA-28 | — | 4 test: moduli/contenuti/test_modifica_a_mano.py |
| CA-29 | — | 4 test: moduli/contenuti/test_modifica_a_mano.py |
| CA-30 | — | 6 test: moduli/notifiche/test_jobs.py |
| CA-31 | — | moduli/revisione/test_interventi.py::test_ca31_un_secondo_intervento_409_e_dopo_10_minuti_si_rilancia |
| CA-32 | — | 6 test: moduli/revisione/test_sospensione.py |
| CA-36 | — | 3 test: moduli/pubblicazione/test_service.py |
| CA-37 | — | 3 test: moduli/pubblicazione/test_service.py |
| CA-38 | — | moduli/pubblicazione/test_service.py::test_ca38_errore_temporaneo_al_terzo_tentativo_fallito<br>moduli/pubblicazione/test_service.py::test_ca38_errore_definitivo_fallisce_subito |
| CA-39 | — | 5 test: moduli/pubblicazione/test_service.py |
| CA-48 | — | 3 test: moduli/campagne/test_api_bozza.py |
| CA-50 | — | moduli/contenuti/test_generazione.py::test_ca50_riprova_non_rianalizza_le_foto_della_campagna<br>moduli/contenuti/test_generazione.py::test_ca50_riprova_dopo_l_analisi_non_rianalizza_le_foto |
| CA-53 | — | 3 test: moduli/revisione/test_decisioni.py |
| CA-54 | — | moduli/campagne/test_api_bozza.py::test_ca54_dettaglio_calcolo_post_chiesti_e_avvisi |
| CA-55 | — | 5 test: moduli/contenuti/test_generazione.py |
| CA-56 | — | 11 test: moduli/contenuti/test_calendario.py |
| CA-57 | — | 6 test: adapters/ai/test_ai.py |
| CA-58 | — | moduli/contenuti/test_generazione.py::test_ca58_errore_di_configurazione_fallita_subito_senza_altre_esecuzioni<br>moduli/contenuti/test_generazione.py::test_ca58_litellm_senza_i_modelli_fallita_subito_con_il_motivo |
| CA-59 | — | moduli/contenuti/test_generazione.py::test_ca59_errore_su_una_sola_foto_la_foto_resta_fuori_con_il_motivo |
| CA-60 | — | moduli/revisione/test_router.py::test_ca60_ultimo_errore_in_generazione_fallita |
| CA-61 | — | moduli/accesso/test_sessioni_sliding.py::test_ca61_admin_accede_operatore_non_artigiano<br>percorsi/test_stati_e_contratti.py::test_ca61_admin_passa_come_operatore_ma_non_artigiano |
| CA-62 | — | 3 test: moduli/accesso/test_accesso_revisione.py |
| CA-63 | — | percorsi/test_stati_e_contratti.py::test_ca63_consorzio_senza_sessione_dalla_configurazione |
| CA-64 | — | 6 test: moduli/contenuti/test_modifica_a_mano.py |
| CA-65 | — | moduli/revisione/test_interventi.py::test_ca65_spunta_salva_chi_e_quando_e_si_toglie<br>moduli/revisione/test_interventi.py::test_ca65_spunta_su_un_post_da_rivedere_409 |
| CA-66 | — | 4 test: moduli/contenuti/test_rigenera.py |
| CA-67 | — | 4 test: moduli/revisione/test_interventi.py |
| CA-68 | — | 3 test: moduli/revisione/test_scadenze.py |
| CA-69 | — | moduli/revisione/test_da_approvare.py::test_ca69_conteggi_entro_quando_e_ultima_nota |
| CA-70 | — | percorsi/test_revisione_ca.py::test_ca70_ordine_campagne_e_permessi_del_percorso |
| CA-71 | — | 13 test: moduli/contenuti/test_cambia_foto.py |
| CA-72 | — | 4 test: moduli/revisione/test_interventi.py |
| CA-79 | — | 3 test: moduli/artigiani/test_nuovo_artigiano.py |
| CA-80 | — | 5 test: adapters/ai/test_ai.py |
| CA-81 | — | 7 test: moduli/campagne/test_sistemazione_foto.py |
| CA-82 | — | moduli/contenuti/test_chiamate_ai.py::test_ca82_ogni_chiamata_della_generazione_ha_il_suo_costo |
| CA-83 | — | **nessuno** |
| CA-84 | — | 5 test: moduli/contenuti/test_modifica_a_mano.py |
| CA-85 | — | 3 test: moduli/revisione/test_interventi.py |
| CA-86 | — | 6 test: moduli/campagne/test_richiesta.py |
| CA-87 | R-13 | 8 test: moduli/campagne/test_richiesta.py |
| CA-88 | — | 4 test: moduli/campagne/test_richiesta.py |
| CA-89 | — | 3 test: moduli/campagne/test_richiesta.py |
| CA-90 | — | moduli/campagne/test_richiesta.py::test_ca90_l_artigiano_vede_la_richiesta_e_nessun_post<br>moduli/campagne/test_richiesta.py::test_ca90_la_campagna_con_la_richiesta_si_apre_per_prima |
| CA-91 | — | percorsi/test_percorso_corsia6.py::test_ca91_richiesta_cambia_foto_approva_pubblica<br>percorsi/test_percorso_corsia6.py::test_ca91_dopo_l_approvazione_modifica_sposta_annulla_sospendi_riattiva |
| CA-92 | — | 4 test: moduli/revisione/test_artigiani.py |
| CA-93 | — | 4 test: moduli/artigiani/test_scheda_artigiano.py |
| CA-94 | — | 3 test: moduli/campagne/test_elenco_campagne.py |
| CA-95 | — | 3 test: moduli/campagne/test_archivio_foto.py |
| CA-96 | — | 3 test: moduli/campagne/test_archivio_foto.py |
| CA-97 | — | 3 test: moduli/contenuti/test_settimana.py |
| CA-98 | — | 3 test: moduli/contenuti/test_settimana.py |
| CA-99 | — | percorsi/test_pagine_corsia7.py::test_ca99_percorso_pagine |
| CA-100 | — | 3 test: moduli/campagne/test_campagne_sovrapposte.py |
| CA-101 | — | moduli/contenuti/test_piano.py::test_ca101_nessun_tetto_alle_immagini_ai_piu_di_quelle_che_mancano<br>percorsi/test_ca101_immagini_ai_senza_tetto.py::test_ca101_campagna_senza_foto_trenta_post_per_canale_con_immagine_ai |
| CA-102 | — | 8 test: moduli/contenuti/test_rigenera_immagine.py |
| CA-103 | R-03 | 3 test: moduli/contenuti/test_rigenera_immagine.py |
| CA-104 | — | 4 test: moduli/contenuti/test_cambia_foto.py |
| CA-105 | — | 3 test: moduli/contenuti/test_cambia_foto.py |
| CA-106 | — | 5 test: moduli/contenuti/test_generazione.py |
| CA-107 | — | moduli/contenuti/test_generazione.py::test_ca107_altri_post_porta_le_prime_frasi_dei_testi_gia_scritti<br>moduli/contenuti/test_rigenera.py::test_ca107_la_rigenerazione_passa_gli_attacchi_degli_altri_post |
| CA-108 | — | 4 test: adapters/ai/test_litellm.py |
| CA-109 | — | 4 test: moduli/contenuti/test_chiamate_ai.py |
| CA-110 | — | 5 test: moduli/contenuti/test_storico_ai.py |
| CA-111 | — | 3 test: moduli/contenuti/test_storico_ai.py |
| CA-112 | — | 3 test: moduli/contenuti/test_storico_ai.py |
| CA-113 | — | 6 test: adapters/ai/test_litellm.py |
| CA-114 | — | 5 test: moduli/campagne/test_sistemazione_foto.py |
| CA-115 | — | moduli/contenuti/test_generazione.py::test_ca115_orari_occupati_delle_altre_campagne<br>moduli/contenuti/test_generazione.py::test_ca115_il_finto_non_mette_un_post_nella_stessa_ora_occupata |
| CA-116 | — | percorsi/test_ca116_percorso_corsia9.py::test_ca116_campagne_sovrapposte_rifai_il_post_rigenera_immagine_approva_storico |

## CA del perimetro senza test

- CA-83

## Test che non hanno il loro CA nello spec

— nessuno

## Fuori MVP con il test ancora nel repository

Spec §7: dove il codice resta (gruppi `create_ai`, caroselli,
archivio), il test resta. Gli altri CA di §7 non devono avere test.

- CA-46
- CA-47
- CA-52
- CA-76

## Regole del perimetro che nessun CA cita

Le regole di §5 che nessun criterio di §6 richiama nel testo: la
copertura passa da altre regole citate oppure manca del tutto.

- R-01
- R-02
- R-04
- R-05
- R-06
- R-08
- R-09
- R-10
- R-11
- R-12
- R-14
- R-15
- R-16
- R-18
- R-21
- R-22
- R-24
- R-25
- R-26
- R-27
- R-28
- R-29
- R-30
- R-31
- R-32
- R-33
- R-34
- R-35
- R-36
- R-37
- R-38
- R-42
- R-43
- R-44
- R-45
- R-46
- R-47
- R-48
- R-49
- R-50

## Controllo a campione

Fatto a mano su quanto la generazione automatica non può decidere (T4-101):

- **CA-83** (adattatore Meta con risposte HTTP simulate) è l'unico CA senza un
  test col nome del contratto `test_ca83_...`. Il file
  `tests/adapters/social/test_meta.py` dichiara «CA-83» nel docstring e i suoi
  16 test verificano proprio quel criterio (Facebook ok con id salvato,
  contenitore Instagram, errore definitivo → `fallito`, timeout e 5xx →
  temporaneo ritentato). Il criterio è coperto; il nome del test non segue lo
  spec §6 («il test porta l'ID nel nome»). Rilievo RL-010 nel registro.
- **Regole citate**: il collegamento R → CA nello spec è quasi assente (40
  regole di §5 su 43 non sono citate da nessun CA). Il campione su R-41…R-50,
  le regole nuove della corsia 9, mostra che tutte hanno il loro CA: R-42 →
  CA-81 e CA-114; R-43 → CA-102, CA-113; R-44 → CA-82, CA-109; R-45 → CA-56;
  R-46 → CA-86…CA-90; R-47 → CA-95, CA-96; R-48 → CA-97, CA-98; R-49 →
  CA-102, CA-103; R-50 → CA-109…CA-112. La copertura c'è; il collegamento
  esplicito no, quindi la matrice automatica può provare la copertura dei CA
  ma non quella delle regole. Rilievo RL-011 nel registro.
- **Sufficienza dei test**: letti a campione CA-71, CA-87 e CA-110 con i
  rispettivi test (`test_ca71_*`, `test_ca87_*`, `test_ca110_*`): i tre
  verificano ciò che il criterio dice (azioni ammesse e 422/409/403 attesi,
  caricamento con dichiarazione e 404 per l'artigiano di un'altra bottega,
  filtri e paginazione dello storico AI). Nessuna divergenza trovata.
