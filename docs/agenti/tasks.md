# Tasks

Prendi un task libero con i prerequisiti chiusi; scrivi il tuo nome in "Chi"; nella PR cambia ☐ in ☑. Solo lo sprint corrente è diviso in task.

## Sprint 1 · Scheletro che cammina (modello definitivo, AI e social finti, profilo dal seed)

| ID | Task | Leggi | Dipende da | Chi | Fatto quando | ☐ |
|---|---|---|---|---|---|---|
| T1-01 | Struttura backend (`app/` come constitution §2), `config.py`, `db.py`, `GET /api/health`, fixture pytest su `adflow_test`, `.env.example`, README | plan §1 | — | | app avviata, test health verde | ☐ |
| T1-02 | Alembic + tabelle `utente`, `sessione` | plan §2 | T1-01 | | upgrade e downgrade su DB vuoto | ☐ |
| T1-03 | `domain.py`: ruoli, stati, transizioni, valori ammessi, `verifica_transizione()` | plan §2 | T1-01 | | test su ogni transizione ammessa e vietata | ☐ |
| T1-04 | Autenticazione: scrypt, login / logout / me, cookie, sessione con hash, "richiede ruolo", CLI crea utente | plan §3 | T1-02 | | CA-01…03 | ☐ |
| T1-05 | Tabelle `profilo_bottega`, `campagna`, `foto` + seed (artigiano con profilo, operatore, admin) | plan §2 | T1-02, T1-03 | | migrazione ok, seed funzionante | ☐ |
| T1-06 | Tabelle `post`, `versione_post`, `approvazione`, `decisione_campagna`, `pubblicazione` | plan §2 | T1-05 | | secondo `ok` sullo stesso post rifiutato | ☐ |
| T1-07 | API campagne: crea bozza, elenco, dettaglio, vincoli e permessi | plan §3; spec R-08, R-12 | T1-04, T1-05 | | CA-04, CA-09…12 | ☐ |
| T1-08 | Adattatore archivio + API foto e gruppi | plan §3, §5; spec R-13 | T1-07 | | CA-13 | ☐ |
| T1-09 | Worker Procrastinate + `coda.py` | plan §1, §4 | T1-02 | | job di prova eseguito in un test | ☐ |
| T1-10 | Invio: controlli, copia dal profilo, snapshot, accodamento | plan §3; spec §2.1 | T1-08, T1-09 | | CA-14, CA-15 | ☐ |
| T1-11 | Adattatore AI: interfaccia, provider finto (anche errori), LiteLLM non usato nei test | plan §5 | T1-01 | | nessuna chiamata di rete nei test | ☐ |
| T1-12 | Calcolo slot (funzione pura) | spec R-05, R-08 | T1-03 | | CA-17 + casi limite | ☐ |
| T1-13 | Validatore a regole (lunghezza, hashtag, parole vietate, "cose da non dire", niente prezzi o premi) | spec R-09 | T1-03 | | un test per regola | ☐ |
| T1-14 | Job `genera_campagna` + API Riprova | plan §4; spec R-09 | T1-06, T1-10…13 | | CA-17…20 | ☐ |
| T1-15 | API revisione: post della campagna, approva in blocco | plan §3; spec R-14 | T1-14 | | CA-21, CA-22 | ☐ |
| T1-16 | Social simulato + `tick_pubblicazione` | plan §4, §5 | T1-06, T1-09 | | CA-36…39 | ☐ |
| T1-17 | Frontend base: Mantine, `api.ts`, `auth.tsx`, login, rotte per ruolo, proxy `/api` | plan §3 | T1-04 | | login dal browser; build e lint puliti | ☐ |
| T1-18 | Frontend artigiano minimo: bozza, foto a gruppi, invio, stato | spec §2.1 | T1-17, T1-10 | | percorso a mano di converge §3 | ☐ |
| T1-19 | Frontend operatore minimo: da approvare, Vedi campagna (elenco), Approva, Riprova | spec §2.3, §4 | T1-17, T1-15 | | percorso a mano di converge §3 | ☐ |
| T1-20 | Test API del percorso completo + chiusura sprint | converge §3 | T1-15, T1-16 | | tutti i CA con S = 1 verdi | ☐ |

In parallelo: dopo T1-01 → T1-02, T1-03, T1-11; dopo T1-03 → T1-12, T1-13; T1-17 dopo T1-04. Le migrazioni (T1-02, T1-05, T1-06) in ordine, una persona alla volta.

## Sprint successivi (si dividono in task quando si arriva)
- **2a · Scheda bottega**: profilo e Bentornato, PATCH bozza, schermate passi 1–12. CA-05…08, CA-16.
- **2b · Revisione e motivi del No**: rimanda, respingi con motivo, notifiche ed email, scadenza, rigenera (2 modalità), sospendi / riattiva / annulla, visibilità artigiano. CA-23…32.
- **3 · Ritocco foto e pagine operatore**: `versione_foto`, ritocca / scegli foto, anagrafica, elenco e pagina artigiano, account social e sospensione, calendario, promemoria. CA-33…35, CA-40…43.
- **4 · Monitoraggio e demo**: metriche, dashboard, report, E2E, dati demo, prova con OpenAI. CA-44, CA-45.
