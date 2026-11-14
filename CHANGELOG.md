# Registro Ufficiale delle Modifiche al Software · AdFlow Suite

> **Documento Ufficiale di Progetto (`CHANGELOG.md`)**<br>
> Tracciamento storico dettagliato di tutte le modifiche, interventi, rilasci e integrazioni al software dal primo commit del 25 Settembre 2026 ad oggi.<br>
> Ogni voce riporta data e ora esatta (`YYYY-MM-DD HH:MM:SS`), autore, identificativo commit, etichetta di tipologia (`[FEAT]`, `[FIX]`, `[SECURITY]`, `[DOCS]`, `[TEST]`, `[REFACTOR]`, `[CHORE]`, `[MERGE]`) e l'area di competenza architetturale.

---

## 🏷️ Guida alle Etichette (Taxonomy)

| Etichetta | Significato | Descrizione Operativa |
|---|---|---|
| `[FEAT]` | Nuova Funzionalità | Nuovi endpoint API, moduli di dominio, pagine frontend o logiche applicative |
| `[FIX]` | Correzione Bug | Risoluzione di anomalie funzionali, difetti nei calcoli o test intermittenti (flaky) |
| `[SECURITY]` | Sicurezza & Hardening | Difese anti-DoS, sanitizzazione input, rate-limiting, audit SAST/DAST e crittografia |
| `[DOCS]` | Documentazione | Aggiornamento di ADR, specifiche funzionali (spec), piani tecnici e guide operative |
| `[TEST]` | Collaudo & QA | Test di unità, integrazione, confini di dominio, carico con Locust o guasti ordinati |
| `[REFACTOR]` | Refactoring | Riorganizzazione interna del codice senza modifiche al comportamento esterno |
| `[CHORE]` | Manutenzione & Setup | Manutenzione dipendenze, file di configurazione (`.gitignore`, linters, scripts) |
| `[MERGE]` | Integrazione PR | Fusione e approvazione formale di rami di lavoro su `origin/main` |

---

## 📊 Indice Cronologico delle Fasi e degli Sprint

| Fase / Sprint | Periodo | N. Modifiche | Obiettivo Principale |
|---|---|:---:|---|
| **Sviluppo Corrente, Risoluzione Bug e Rafforzamento Difese** | Novembre 2026 - In corso | 1 commit | Sviluppo Corrente, Risoluzione Bug e Rafforzamento Difese (Novembre 2026 - In corso) |
| **Sprint 5 · Chiusura, Vetrina Pubblica, Orchestratore e Design** | 1–5 Novembre 2026 | 101 commit | Sprint 5 · Chiusura, Vetrina Pubblica, Orchestratore e Design (1–5 Novembre 2026) |
| **Sprint 4 · Accettazione, Hardening, Simulazione e Concorrenza** | 26–31 Ottobre 2026 | 140 commit | Sprint 4 · Accettazione, Hardening, Simulazione e Concorrenza (26–31 Ottobre 2026) |
| **Sprint 3 · MVP Base: AI Vera, Sistemazione Foto e Pubblicazione Meta** | 15–25 Ottobre 2026 | 36 commit | Sprint 3 · MVP Base: AI Vera, Sistemazione Foto e Pubblicazione Meta (15–25 Ottobre 2026) |
| **Sprint 2b · Notifiche, Interventi e Macchina a Stati** | 11–14 Ottobre 2026 | 168 commit | Sprint 2b · Notifiche, Interventi e Macchina a Stati (11–14 Ottobre 2026) |
| **Sprint 2a · Profilo Bottega, Gruppi Foto e Invio Bozza** | 8–10 Ottobre 2026 | 170 commit | Sprint 2a · Profilo Bottega, Gruppi Foto e Invio Bozza (8–10 Ottobre 2026) |
| **Sprint 1 · Fondamenta Modulari, Tabelle PostgreSQL e Contratti** | 1–7 Ottobre 2026 | 56 commit | Sprint 1 · Fondamenta Modulari, Tabelle PostgreSQL e Contratti (1–7 Ottobre 2026) |
| **Setup Iniziale, Architettura e Reset Documentale** | 25–30 Settembre 2026 | 14 commit | Setup Iniziale, Architettura e Reset Documentale (25–30 Settembre 2026) |

---

## 🚀 Sviluppo Corrente, Risoluzione Bug e Rafforzamento Difese (Novembre 2026 - In corso)

Totale modifiche registrate nella fase: **1**

| Data e Ora | Commit | Autore | Tipo | Corsia / Modulo | Descrizione Dettagliata della Modifica |
|---|:---:|---|:---:|---|---|
| `2026-11-14 14:10:03` | `93c7e9f` | tresilvia83-wq | `[DOCS]` | **Comune / Sistema** | docs: aggiunge CHANGELOG.md e workflow di aggiornamento automatico |

---

## 🚀 Sprint 5 · Chiusura, Vetrina Pubblica, Orchestratore e Design (1–5 Novembre 2026)

Totale modifiche registrate nella fase: **101**

| Data e Ora | Commit | Autore | Tipo | Corsia / Modulo | Descrizione Dettagliata della Modifica |
|---|:---:|---|:---:|---|---|
| `2026-11-05 16:29:21` | `24885fa` | Nilton | `[MERGE]` | **Corsia 5 · Frontend & Interfaccia** | Merge pull request #188 from Full-Stack-AI-ADFlow-Suite-Project/docs/vetrina-pubblica |
| `2026-11-05 16:04:49` | `8523e4c` | NiL87AI | `[DOCS]` | **Corsia 5 · Frontend & Interfaccia** | docs: registra in ADR e tasks l'ingresso della vetrina pubblica (PR #170) |
| `2026-11-05 15:54:13` | `d2cae59` | Nilton | `[MERGE]` | **Corsia 5 · Frontend & Interfaccia** | Merge pull request #170 from Full-Stack-AI-ADFlow-Suite-Project/feature/accesso-sfondo-ricco |
| `2026-11-05 15:41:57` | `aef9d88` | NiL87AI | `[CHORE]` | **Comune / Sistema** | chore: leva i binari del motore Impeccable dal repository |
| `2026-11-05 15:20:37` | `640efbf` | NiL87AI | `[CHORE]` | **Comune / Sistema** | chore: ignora gli artefatti di lavoro di Impeccable |
| `2026-11-05 15:20:35` | `d2b0623` | NiL87AI | `[DOCS]` | **Comune / Sistema** | docs: sposta i rilievi RL-045…RL-055 in idee.md e ripristina il registro archiviato |
| `2026-11-05 15:09:37` | `2a220e8` | NiL87AI | `[DOCS]` | **Corsia 2 · Campagne & Foto** | docs: allinea i percorsi di PRODUCT.md all'archivio pagine |
| `2026-11-05 15:06:36` | `924e60e` | NiL87AI | `[MERGE]` | **Corsia 5 · Frontend & Interfaccia** | Merge remote-tracking branch 'origin/main' into feature/accesso-sfondo-ricco |
| `2026-11-05 13:52:25` | `e8159bf` | blulime7 | `[MERGE]` | **Corsia 0 · Core, Coda & Architettura** | Merge pull request #187 from Full-Stack-AI-ADFlow-Suite-Project/feature/avvia-logging-migliorie |
| `2026-11-05 13:48:51` | `aa89250` | blulime7 | `[MERGE]` | **Corsia 2 · Campagne & Foto** | Merge pull request #186 from Full-Stack-AI-ADFlow-Suite-Project/fix/test-foto-pubblica-firma-alterata |
| `2026-11-05 13:48:33` | `070a567` | blulime7 | `[FIX]` | **Corsia 0 · Core, Coda & Architettura** | fix: isola il finto sleep del test di Ctrl+C al solo modulo avvia |
| `2026-11-05 13:41:43` | `321a0bf` | blulime7 | `[FEAT]` | **Corsia 0 · Core, Coda & Architettura** | feat: rende affidabili avvio, registro e log di avvia.py |
| `2026-11-05 13:37:06` | `1175b64` | blulime7 | `[FIX]` | **Corsia 2 · Campagne & Foto** | fix: rende deterministico il test sulla firma alterata della foto pubblica |
| `2026-11-05 13:19:11` | `ae3d51f` | tresilvia83-wq | `[MERGE]` | **Comune / Sistema** | merge: allinea feature con le novita di main (PR #184 archiviazione finale) |
| `2026-11-05 12:36:13` | `9818bd0` | tresilvia83-wq | `[FEAT]` | **Comune / Sistema** | feat: unifica motore di avvio con logging e registro attivita |
| `2026-11-05 12:00:30` | `4e10e64` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge pull request #184 from Full-Stack-AI-ADFlow-Suite-Project/docs/archiviazione-finale |
| `2026-11-05 11:56:05` | `f1a78a3` | blulime7 | `[DOCS]` | **Comune / Sistema** | docs: aggiunge un elenco di idee facoltative, non citato da nessun documento |
| `2026-11-05 11:52:13` | `3788c84` | blulime7 | `[DOCS]` | **Comune / Sistema** | docs: precisa ordine, modifiche mirate, budget e dipendenze della corsia della presentazione |
| `2026-11-05 11:37:19` | `fb61f19` | blulime7 | `[DOCS]` | **Corsia 2 · Campagne & Foto** | docs: aggiorna ai percorsi di oggi i commenti del codice e la mappa dell'archivio |
| `2026-11-05 11:28:21` | `c6dbf70` | blulime7 | `[DOCS]` | **Corsia 2 · Campagne & Foto** | docs: aggiorna la mappa dell'archivio e i percorsi dopo l'ADR-123 |
| `2026-11-05 11:26:59` | `c2d563b` | blulime7 | `[DOCS]` | **Corsia 5 · Frontend & Interfaccia** | docs: riduce il README e aggiorna AGENTS e il README del frontend alla nuova struttura |
| `2026-11-05 11:25:53` | `b6cf8f5` | blulime7 | `[DOCS]` | **Comune / Sistema** | docs: archivia il video di riserva di T3-07 e accorcia tasks.md |
| `2026-11-05 11:24:10` | `e3e6aa4` | blulime7 | `[DOCS]` | **Comune / Sistema** | docs: porta converge e sicurezza nel README del backend e nella roadmap e li archivia |
| `2026-11-05 11:22:13` | `398eff8` | blulime7 | `[DOCS]` | **Comune / Sistema** | docs: archivia la sintesi dell'accettazione e il perimetro dell'MVP |
| `2026-11-05 11:21:25` | `4153be5` | blulime7 | `[DOCS]` | **Corsia 2 · Campagne & Foto** | docs: archivia le pagine statiche in docs/archivio/pagine |
| `2026-11-05 10:34:59` | `911e7f0` | blulime7 | `[DOCS]` | **Corsia 0 · Core, Coda & Architettura** | docs: chiude tutto, apre la corsia della presentazione e rende passiva la documentazione (ADR-123) |
| `2026-11-05 10:16:15` | `685b3cc` | blulime7 | `[DOCS]` | **Corsia 0 · Core, Coda & Architettura** | docs: riassume ADR, spec e plan e archivia i testi completi (ADR-122) |
| `2026-11-05 10:04:51` | `6458c91` | blulime7 | `[DOCS]` | **Corsia 0 · Core, Coda & Architettura** | docs: riduce README, spec e plan e archivia rilievi e parti fuori MVP (ADR-122) |
| `2026-11-05 09:50:30` | `08855c5` | blulime7 | `[DOCS]` | **Corsia 0 · Core, Coda & Architettura** | docs: archivia brief, simulazione e QA a sprint chiusi (ADR-122) |
| `2026-11-04 15:53:19` | `0ce2596` | NiL87AI | `[DOCS]` | **Corsia 1 · Accesso & Artigiani** | docs: altri tre rilievi dal giro utente (RL-053…RL-055) |
| `2026-11-04 14:53:35` | `3174062` | NiL87AI | `[DOCS]` | **Corsia 1 · Accesso & Artigiani** | docs: l'artigiano entra anche da PC, non solo da telefono |
| `2026-11-04 14:49:23` | `691c963` | NiL87AI | `[CHORE]` | **Comune / Sistema** | chore: aggiunge Impeccable e il contesto di design del progetto |
| `2026-11-04 14:49:02` | `54ea6f6` | NiL87AI | `[DOCS]` | **Comune / Sistema** | docs: registra i rilievi dell'audit UI (RL-045…RL-052) |
| `2026-11-04 14:47:24` | `cf0c7bb` | NiL87AI | `[FIX]` | **Corsia 5 · Frontend & Interfaccia** | fix: landmark e h1 sulle pagine pubbliche, copy corretto in Vetrina |
| `2026-11-04 13:53:55` | `06bf87c` | NiL87AI | `[MERGE]` | **Corsia 5 · Frontend & Interfaccia** | Merge remote-tracking branch 'origin/main' into feature/accesso-sfondo-ricco |
| `2026-11-04 13:37:22` | `0345980` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge pull request #182 from Full-Stack-AI-ADFlow-Suite-Project/feature/T5-chiusura-sprint |
| `2026-11-04 13:34:08` | `a8c6cd7` | blulime7 | `[DOCS]` | **Comune / Sistema** | docs: chiude lo sprint 5 con la nota su ciò che non è stato fatto |
| `2026-11-04 13:31:01` | `992bea7` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge pull request #181 from Full-Stack-AI-ADFlow-Suite-Project/feature/T5-136-contrasto |
| `2026-11-04 13:25:40` | `918649c` | blulime7 | `[FIX]` | **Comune / Sistema** | fix: contrasto dei colori e link riconoscibili senza il colore (RL-035) |
| `2026-11-04 13:14:45` | `dc963d8` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge pull request #180 from Full-Stack-AI-ADFlow-Suite-Project/feature/T5-135-input-estremi |
| `2026-11-04 13:11:15` | `e870567` | blulime7 | `[CHORE]` | **Comune / Sistema** | chore: unisce main in T5-135, caselle di tasks.md spuntate |
| `2026-11-04 13:10:51` | `901a169` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge pull request #179 from Full-Stack-AI-ADFlow-Suite-Project/feature/T5-124-limite-azioni-ai |
| `2026-11-04 13:07:27` | `2e90387` | blulime7 | `[CHORE]` | **Comune / Sistema** | chore: unisce main in T5-124, caselle di tasks.md spuntate |
| `2026-11-04 13:07:01` | `dd43a0a` | blulime7 | `[MERGE]` | **Corsia 2 · Campagne & Foto** | Merge pull request #178 from Full-Stack-AI-ADFlow-Suite-Project/feature/T5-132-foto-della-demo |
| `2026-11-04 13:04:37` | `031c46f` | blulime7 | `[CHORE]` | **Comune / Sistema** | chore: unisce main in T5-132, caselle di tasks.md spuntate |
| `2026-11-04 13:04:08` | `68bdeee` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge pull request #177 from Full-Stack-AI-ADFlow-Suite-Project/feature/T5-133-dipendenze |
| `2026-11-04 13:00:44` | `7c305d8` | blulime7 | `[CHORE]` | **Comune / Sistema** | chore: unisce main in T5-133, caselle di tasks.md spuntate |
| `2026-11-04 13:00:25` | `b37db08` | blulime7 | `[MERGE]` | **Corsia 2 · Campagne & Foto** | Merge pull request #176 from Full-Stack-AI-ADFlow-Suite-Project/feature/T5-131-immagini-ai |
| `2026-11-04 13:00:00` | `4e1c9d0` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge pull request #175 from Full-Stack-AI-ADFlow-Suite-Project/feature/T5-134-intestazioni |
| `2026-11-04 12:59:40` | `2348ece` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge pull request #174 from Full-Stack-AI-ADFlow-Suite-Project/feature/T5-123-guasti-ordinati |
| `2026-11-04 12:56:43` | `8b608d6` | blulime7 | `[CHORE]` | **Comune / Sistema** | chore: unisce main in T5-123, caselle di tasks.md tutte spuntate |
| `2026-11-04 12:56:08` | `12f54d7` | blulime7 | `[MERGE]` | **Corsia 2 · Campagne & Foto** | Merge pull request #173 from Full-Stack-AI-ADFlow-Suite-Project/feature/T5-122-foto-una-volta |
| `2026-11-04 12:55:14` | `5b8c474` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge pull request #172 from Full-Stack-AI-ADFlow-Suite-Project/feature/T5-121-approva-respingi-atomiche |
| `2026-11-04 12:53:16` | `dbf393b` | blulime7 | `[MERGE]` | **Corsia 4 · Meta & Pubblicazione** | Merge pull request #171 from Full-Stack-AI-ADFlow-Suite-Project/feature/T5-111-pubblicazione-una-volta |
| `2026-11-04 12:43:25` | `6095d49` | blulime7 | `[DOCS]` | **Corsia 2 · Campagne & Foto** | docs: spunta T5-134, foto visibili nel frontend con le nuove intestazioni |
| `2026-11-04 12:32:56` | `10fa42e` | blulime7 | `[DOCS]` | **Comune / Sistema** | docs: variabili del limite delle azioni AI in .env.example (T5-124) |
| `2026-11-04 12:29:28` | `2d1fce5` | blulime7 | `[DOCS]` | **Corsia 2 · Campagne & Foto** | docs: il limite di dimensione è quello della foto, 10 MB (T5-132) |
| `2026-11-04 12:27:25` | `392214d` | blulime7 | `[DOCS]` | **Corsia 2 · Campagne & Foto** | docs: il percorso delle foto della demo diventa un segnaposto (T5-132) |
| `2026-11-04 12:22:38` | `d523803` | blulime7 | `[DOCS]` | **Corsia 2 · Campagne & Foto** | docs: i passi mancanti per partire e il percorso delle foto della demo (T5-132) |
| `2026-11-04 12:20:20` | `af4e43d` | blulime7 | `[FIX]` | **Comune / Sistema** | fix: ripristina il codice congelato e limita gli id in ingresso (T5-135) |
| `2026-11-04 12:18:00` | `3e05980` | blulime7 | `[CHORE]` | **Comune / Sistema** | chore: toglie httpx2, pacchetto che nessuno importa né richiede (T5-133) |
| `2026-11-04 12:14:16` | `d41f641` | blulime7 | `[FIX]` | **Comune / Sistema** | fix: blocca prima la campagna in accendi_intervento (T5-122) |
| `2026-11-04 12:06:28` | `44f904b` | blulime7 | `[DOCS]` | **Comune / Sistema** | docs: il task T5-133 delle dipendenze è fatto (T5-133) |
| `2026-11-04 12:06:18` | `28ee50d` | blulime7 | `[CHORE]` | **Comune / Sistema** | chore: pillow 13, httpx e filelock dichiarate (T5-133) |
| `2026-11-04 12:05:49` | `6036d47` | blulime7 | `[FIX]` | **Corsia 5 · Frontend & Interfaccia** | fix: il 503 del limite delle azioni AI non parla di accesso (RL-018) |
| `2026-11-04 11:53:44` | `3016d6b` | blulime7 | `[DOCS]` | **Comune / Sistema** | docs: chiude T5-135 |
| `2026-11-04 11:53:15` | `94570ee` | blulime7 | `[FIX]` | **Comune / Sistema** | fix: limita il tipo dello storico AI (T5-135) |
| `2026-11-04 11:53:02` | `fcf7f88` | blulime7 | `[FIX]` | **Comune / Sistema** | fix: limita gli id di percorso a int4 (T5-135) |
| `2026-11-04 11:52:44` | `1409214` | blulime7 | `[FIX]` | **Comune / Sistema** | fix: rifiuta il byte NUL negli schemi di testo (T5-135) |
| `2026-11-04 11:41:21` | `66aab5a` | blulime7 | `[TEST]` | **Comune / Sistema** | test: la raffica di azioni AI incontra il 429 (RL-018), spunta T5-124 |
| `2026-11-04 11:41:21` | `f8373f5` | blulime7 | `[FEAT]` | **Corsia 1 · Accesso & Artigiani** | feat: limite per utente sulle azioni AI, con prenota() parametrica (RL-018) |
| `2026-11-04 11:37:49` | `36609d0` | blulime7 | `[DOCS]` | **Comune / Sistema** | docs: le stesse intestazioni nell'esempio Nginx di /api (T5-134) |
| `2026-11-04 11:37:40` | `3cdb361` | blulime7 | `[FIX]` | **Comune / Sistema** | fix: le cinque intestazioni di sicurezza sull'API (T5-134) |
| `2026-11-04 11:35:25` | `1a000be` | blulime7 | `[DOCS]` | **Comune / Sistema** | docs: chiude T5-123 |
| `2026-11-04 11:35:21` | `68afb81` | blulime7 | `[TEST]` | **Comune / Sistema** | test: toglie il marcatore ai test RL-028 e RL-029 (T5-123) |
| `2026-11-04 11:35:16` | `f9b4766` | blulime7 | `[FIX]` | **Corsia 0 · Core, Coda & Architettura** | fix: risponde 503 con database giù e disco pieno (T5-123) |
| `2026-11-04 11:25:14` | `7052113` | blulime7 | `[DOCS]` | **Comune / Sistema** | docs: chiude T5-122 |
| `2026-11-04 11:25:11` | `f1dbbbf` | blulime7 | `[TEST]` | **Comune / Sistema** | test: toglie il marcatore ai test RL-023 e RL-024 (T5-122) |
| `2026-11-04 11:25:07` | `5d655e0` | blulime7 | `[FIX]` | **Comune / Sistema** | fix: blocca campagna e post negli interventi (T5-122) |
| `2026-11-04 11:24:17` | `528b03b` | blulime7 | `[TEST]` | **Comune / Sistema** | test: la catena di downgrade parte dalla migrazione 014 (T5-111) |
| `2026-11-04 11:17:12` | `ebccc7f` | blulime7 | `[DOCS]` | **Corsia 2 · Campagne & Foto** | docs: il nuovo esito della tappa immagini e il task T5-131 fatto (T5-131) |
| `2026-11-04 11:17:04` | `954d03c` | blulime7 | `[TEST]` | **Corsia 2 · Campagne & Foto** | test: le immagini AI via OpenRouter nella forma osservata (T5-131) |
| `2026-11-04 11:14:02` | `15dbc7c` | blulime7 | `[FIX]` | **Corsia 1 · Accesso & Artigiani** | fix: rilegge la campagna bloccata anche se è già in sessione (T5-122) |
| `2026-11-04 11:12:15` | `45a1f61` | blulime7 | `[DOCS]` | **Comune / Sistema** | docs: spunta T5-111 in tasks.md |
| `2026-11-04 11:12:14` | `392afd4` | blulime7 | `[TEST]` | **Corsia 4 · Meta & Pubblicazione** | test: pubblicazione a due fasi, processo morto, errore temporaneo (RL-025) |
| `2026-11-04 11:12:13` | `01bb9c0` | blulime7 | `[FIX]` | **Corsia 4 · Meta & Pubblicazione** | fix: la pubblicazione conferma chiamata_il prima del social e non ripubblica dopo un esito sconosciuto (RL-025) |
| `2026-11-04 11:06:58` | `70ffea5` | blulime7 | `[DOCS]` | **Comune / Sistema** | docs: annota campagna_bloccata e chiude T5-121 |
| `2026-11-04 11:06:54` | `4108690` | blulime7 | `[TEST]` | **Comune / Sistema** | test: toglie il marcatore ai due test di concorrenza (T5-121) |
| `2026-11-04 11:06:47` | `11de839` | blulime7 | `[FIX]` | **Comune / Sistema** | fix: blocca la campagna in approva e respingi (T5-121) |
| `2026-11-04 10:53:49` | `1bf89a4` | blulime7 | `[FEAT]` | **Corsia 4 · Meta & Pubblicazione** | feat: migrazione 014, colonna chiamata_il su pubblicazione (T5-111) |
| `2026-11-02 18:38:47` | `ba47dc1` | NiL87AI | `[FEAT]` | **Corsia 5 · Frontend & Interfaccia** | feat: vetrina pubblica, restyling accesso e marchio wordmark |
| `2026-11-02 13:53:15` | `2bddcea` | blulime7 | `[MERGE]` | **Corsia 0 · Core, Coda & Architettura** | Merge pull request #169 from Full-Stack-AI-ADFlow-Suite-Project/feature/ADR-121-corsia-rapida |
| `2026-11-02 13:52:40` | `59184e6` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge pull request #168 from Full-Stack-AI-ADFlow-Suite-Project/feature/T4-100-108-simulazione |
| `2026-11-02 13:22:02` | `e8dce92` | blulime7 | `[DOCS]` | **Corsia 0 · Core, Coda & Architettura** | docs: la prova finale aspetta solo le correzioni del percorso (ADR-121) |
| `2026-11-02 13:20:12` | `3c1d710` | blulime7 | `[TEST]` | **Corsia 5 · Frontend & Interfaccia** | test: la pagina dei task ha lo sprint 5 (ADR-121) |
| `2026-11-02 13:17:13` | `4f91ada` | blulime7 | `[DOCS]` | **Corsia 0 · Core, Coda & Architettura** | docs: apre la corsia rapida dello sprint 5 (ADR-121) |
| `2026-11-02 13:04:52` | `bfdcde4` | blulime7 | `[FIX]` | **Corsia 0 · Core, Coda & Architettura** | fix: i test di concorrenza migrano il database di test (T4-103) |
| `2026-11-02 12:58:02` | `7669d64` | blulime7 | `[DOCS]` | **Comune / Sistema** | docs: annota i cookie redatti nella traccia (T4-106) |
| `2026-11-02 12:54:03` | `94fd575` | blulime7 | `[CHORE]` | **Comune / Sistema** | chore: allinea la simulazione a origin/main |
| `2026-11-02 12:43:32` | `97a949a` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge pull request #167 from Full-Stack-AI-ADFlow-Suite-Project/feature/T3-07-chiusura |
| `2026-11-02 12:43:04` | `edc440e` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge pull request #166 from Full-Stack-AI-ADFlow-Suite-Project/integrazione-finale |

---

## 🚀 Sprint 4 · Accettazione, Hardening, Simulazione e Concorrenza (26–31 Ottobre 2026)

Totale modifiche registrate nella fase: **140**

| Data e Ora | Commit | Autore | Tipo | Corsia / Modulo | Descrizione Dettagliata della Modifica |
|---|:---:|---|:---:|---|---|
| `2026-10-31 01:10:45` | `1d93214` | blulime7 | `[CHORE]` | **Comune / Sistema** | chore: merge feature/T4-108-sintesi |
| `2026-10-31 01:10:45` | `88d4b11` | blulime7 | `[DOCS]` | **Comune / Sistema** | docs: sintesi della simulazione e classi dei rilievi (T4-108) |
| `2026-10-31 01:07:03` | `25575d2` | blulime7 | `[CHORE]` | **Comune / Sistema** | chore: merge feature/T4-107-analisi-tavolino |
| `2026-10-31 01:07:02` | `ec092ff` | blulime7 | `[TEST]` | **Corsia 3 · Motore AI & Testi** | test: prompt injection, minacce, AI vera, log, dati personali e ASVS (T4-107) |
| `2026-10-31 01:01:10` | `79f341f` | blulime7 | `[CHORE]` | **Corsia 5 · Frontend & Interfaccia** | chore: merge feature/T4-106-frontend |
| `2026-10-31 01:01:09` | `cc97c28` | blulime7 | `[TEST]` | **Corsia 0 · Core, Coda & Architettura** | test: percorso E2E a due ruoli, axe e contratto dei tipi (T4-106) |
| `2026-10-31 00:56:20` | `7605c49` | blulime7 | `[CHORE]` | **Comune / Sistema** | chore: merge feature/T4-105-esercizio-guasti-carico |
| `2026-10-31 00:56:19` | `dc36b5c` | blulime7 | `[TEST]` | **Corsia 4 · Meta & Pubblicazione** | test: guasti, carico, backup e prova Meta (T4-105) |
| `2026-10-31 00:51:44` | `99c1114` | blulime7 | `[CHORE]` | **Comune / Sistema** | chore: merge feature/T4-104-invarianti-proprieta |
| `2026-10-31 00:51:43` | `40fa4e3` | blulime7 | `[TEST]` | **Comune / Sistema** | test: invarianti, macchine a stati e fuzzing (T4-104) |
| `2026-10-31 00:17:06` | `8a311b3` | blulime7 | `[CHORE]` | **Comune / Sistema** | chore: merge feature/T4-103-concorrenza |
| `2026-10-31 00:17:05` | `2f2a62a` | blulime7 | `[TEST]` | **Comune / Sistema** | test: prove di concorrenza con barriera e commit veri (T4-103) |
| `2026-10-31 00:09:22` | `52a00dd` | blulime7 | `[CHORE]` | **Comune / Sistema** | chore: merge feature/T4-102-permessi-superficie-http |
| `2026-10-31 00:09:18` | `d2865f2` | blulime7 | `[TEST]` | **Comune / Sistema** | test: matrice dei permessi e superficie HTTP (T4-102) |
| `2026-10-30 21:01:34` | `e0a8752` | blulime7 | `[CHORE]` | **Comune / Sistema** | chore: merge feature/T4-101-linea-base |
| `2026-10-30 21:01:33` | `bb100d2` | blulime7 | `[DOCS]` | **Comune / Sistema** | docs: spunta T4-101 in tasks.md |
| `2026-10-30 21:01:12` | `2c56b12` | blulime7 | `[DOCS]` | **Comune / Sistema** | docs: linea di base della simulazione di accettazione (T4-101) |
| `2026-10-30 20:29:36` | `aff8404` | blulime7 | `[CHORE]` | **Comune / Sistema** | chore: merge feature/T4-100-preparazione-corsia-10 |
| `2026-10-30 20:29:33` | `6038216` | blulime7 | `[DOCS]` | **Comune / Sistema** | docs: prepara la corsia 10 della simulazione di accettazione (T4-100) |
| `2026-10-30 19:47:38` | `6573c44` | blulime7 | `[DOCS]` | **Comune / Sistema** | docs: registra risposte alle nove domande e genera corsia 10 (T4-100…T4-108) |
| `2026-10-30 19:35:18` | `278cec5` | blulime7 | `[DOCS]` | **Comune / Sistema** | docs: riscrive la proposta di accettazione come simulazione, corsia 10 su main a 8c01e2b |
| `2026-10-30 19:28:55` | `0c93cc4` | blulime7 | `[CHORE]` | **Comune / Sistema** | chore: merge feature/proposta-accettazione-post-mvp |
| `2026-10-30 15:13:40` | `8c01e2b` | blulime7 | `[CHORE]` | **Comune / Sistema** | chore: merge feature/T3-07-chiusura |
| `2026-10-30 15:13:39` | `8c90606` | blulime7 | `[DOCS]` | **Comune / Sistema** | docs: registra rapporto finale e video di riserva e chiude T3-07 |
| `2026-10-30 15:09:06` | `4feb66b` | blulime7 | `[CHORE]` | **Comune / Sistema** | chore: merge feature/T3-05-pitch |
| `2026-10-30 15:09:05` | `80f0846` | blulime7 | `[DOCS]` | **Comune / Sistema** | docs: prepara scaletta e slide del pitch dei 10 minuti e chiude T3-05 |
| `2026-10-30 15:06:12` | `2bdacd0` | blulime7 | `[CHORE]` | **Comune / Sistema** | chore: merge feature/T3-02-proposta-tecnica |
| `2026-10-30 15:06:11` | `44d2f72` | blulime7 | `[DOCS]` | **Comune / Sistema** | docs: completa proposta tecnica v1.0 e chiude T3-02 |
| `2026-10-30 15:02:18` | `60ba235` | blulime7 | `[CHORE]` | **Comune / Sistema** | chore: merge feature/issue-17-proxy-cookie-tls |
| `2026-10-30 15:02:16` | `8e62cfc` | blulime7 | `[TEST]` | **Comune / Sistema** | test: completa verifica TLS proxy/cookie locale e chiude follow-up #17 |
| `2026-10-30 14:59:28` | `1f3bbab` | blulime7 | `[CHORE]` | **Corsia 2 · Campagne & Foto** | chore: merge feature/T3-08-sistemazione-parte-2 |
| `2026-10-30 14:59:13` | `fc3433d` | blulime7 | `[DOCS]` | **Comune / Sistema** | docs: archivia brief chiusi e completa T3-08 |
| `2026-10-30 14:55:42` | `552db4e` | blulime7 | `[DOCS]` | **Comune / Sistema** | docs: rimuove commenti e riferimenti agli sprint passati dal codice attivo (T3-08) |
| `2026-10-30 14:50:55` | `ab0ee4f` | blulime7 | `[REFACTOR]` | **Comune / Sistema** | refactor: rimuove import inutilizzati in backend e test (T3-08) |
| `2026-10-30 14:48:03` | `c6a5d39` | blulime7 | `[CHORE]` | **Comune / Sistema** | chore: rimuove cryptography non importato da requirements.txt e allinea plan §1 (T3-08) |
| `2026-10-30 14:47:13` | `1c3abe7` | blulime7 | `[REFACTOR]` | **Comune / Sistema** | refactor: allinea i dati di esempio al perimetro MVP togliendo piano_da_rivedere (T3-08) |
| `2026-10-30 14:47:12` | `3993d25` | blulime7 | `[CHORE]` | **Comune / Sistema** | chore: rimuove il mirror deprecato di prettier da pre-commit (T3-08) |
| `2026-10-30 14:45:04` | `99ae2d2` | blulime7 | `[DOCS]` | **Corsia 2 · Campagne & Foto** | docs: aggiorna docstring di foto_per_id e campagne_di in campagne/service.py (T3-08) |
| `2026-10-30 14:44:46` | `8661669` | blulime7 | `[TEST]` | **Comune / Sistema** | test: raccoglie i test sulle funzioni tolte in test_perimetro_mvp.py (T3-08) |
| `2026-10-30 14:42:23` | `1f0f7f2` | blulime7 | `[TEST]` | **Comune / Sistema** | test: rinomina i test di percorso togliendo i riferimenti agli sprint (T3-08) |
| `2026-10-30 14:40:46` | `0ea41a0` | blulime7 | `[DOCS]` | **Comune / Sistema** | docs: ripulisce plan.md da colonna Scritta in e note di sprint passati (T3-08) |
| `2026-10-30 11:32:07` | `ce60f7e` | blulime7 | `[FIX]` | **Corsia 2 · Campagne & Foto** | fix: la spunta Riscrivi anche il testo vale per ogni cambio di immagine; R-43 ammette le immagini di concetto |
| `2026-10-29 21:11:44` | `aa22034` | blulime7 | `[TEST]` | **Corsia 4 · Meta & Pubblicazione** | test: demo con AI vera e Facebook vero automatica e chiusura (T3-927) |
| `2026-10-29 20:53:41` | `36e8461` | blulime7 | `[TEST]` | **Comune / Sistema** | test: prove negative della corsia 9 e confronto visivo (T3-927) |
| `2026-10-29 20:45:15` | `5f87622` | blulime7 | `[DOCS]` | **Comune / Sistema** | docs: chiude le pagine statiche della corsia 9 (T3-926) |
| `2026-10-29 20:19:10` | `f78d6ba` | blulime7 | `[DOCS]` | **Comune / Sistema** | docs: spunta T3-925 |
| `2026-10-29 20:19:01` | `c867a0f` | blulime7 | `[DOCS]` | **Corsia 3 · Motore AI & Testi** | docs: prova dei prompt v3 e correzione della versione del piano (T3-925) |
| `2026-10-29 20:07:09` | `84db133` | blulime7 | `[FEAT]` | **Corsia 3 · Motore AI & Testi** | feat: comando prova-prompt per la prova dei prompt v3 (T3-925) |
| `2026-10-28 21:16:53` | `e23dbcf` | blulime7 | `[DOCS]` | **Comune / Sistema** | docs: aggiunge il percorso a mano della corsia 9 (T3-927) |
| `2026-10-28 20:52:17` | `1f15aeb` | blulime7 | `[TEST]` | **Comune / Sistema** | test: aggiunge il percorso CA-116 della corsia 9 (T3-927) |
| `2026-10-28 20:47:47` | `a29af69` | blulime7 | `[DOCS]` | **Comune / Sistema** | docs: aggiorna le pagine statiche della corsia 9 (T3-926) |
| `2026-10-28 20:31:18` | `a54a0c0` | blulime7 | `[DOCS]` | **Comune / Sistema** | docs: aggiunge gli screenshot di T3-914 e spunta la casella |
| `2026-10-28 20:27:49` | `811da67` | blulime7 | `[DOCS]` | **Comune / Sistema** | docs: aggiunge gli screenshot di T3-904 e spunta la casella |
| `2026-10-28 20:26:28` | `30fc57c` | blulime7 | `[DOCS]` | **Comune / Sistema** | docs: aggiunge gli screenshot di T3-903 e spunta la casella |
| `2026-10-28 20:22:52` | `d13106a` | blulime7 | `[DOCS]` | **Comune / Sistema** | docs: aggiunge gli screenshot di T3-902 e spunta la casella |
| `2026-10-28 20:21:44` | `85611ff` | blulime7 | `[DOCS]` | **Comune / Sistema** | docs: aggiunge gli screenshot di T3-901 e spunta la casella |
| `2026-10-28 19:59:58` | `f56d761` | blulime7 | `[MERGE]` | **Corsia 2 · Campagne & Foto** | Merge branch 'feature/T3-920-prompt-immagini-v3' into integrazione-finale |
| `2026-10-28 19:59:33` | `58891f2` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge branch 'feature/T3-921-ritaglio-soggetto' into integrazione-finale |
| `2026-10-28 19:13:49` | `9f11786` | blulime7 | `[FEAT]` | **Comune / Sistema** | feat: ritaglio sul soggetto e bordi sfocati (T3-921) |
| `2026-10-28 18:59:48` | `fdfe228` | blulime7 | `[FEAT]` | **Comune / Sistema** | feat: barra di avanzamento della campagna in vedi campagna (T3-915) |
| `2026-10-28 18:55:13` | `0aec5c6` | blulime7 | `[FEAT]` | **Comune / Sistema** | feat: rifai il post e rigenera immagine (T3-923) |
| `2026-10-28 18:54:39` | `a3771d1` | blulime7 | `[FEAT]` | **Comune / Sistema** | feat: mostra numeri e voto nello storico dell'AI (T3-924) |
| `2026-10-28 18:52:20` | `20ee030` | blulime7 | `[FEAT]` | **Corsia 2 · Campagne & Foto** | feat: il prompt delle immagini v3 parte da scena, bottega, campagna e stile (T3-920) |
| `2026-10-28 18:50:19` | `4b8ed92` | blulime7 | `[FEAT]` | **Comune / Sistema** | feat: dai un voto da 1 a 5 alle risposte dell'AI (T3-918) |
| `2026-10-28 18:49:35` | `7ed6bee` | blulime7 | `[FEAT]` | **Corsia 2 · Campagne & Foto** | feat: cambia immagine con foto di gruppo, campagna e archivio (T3-919) |
| `2026-10-28 18:48:06` | `6122ef7` | blulime7 | `[FEAT]` | **Comune / Sistema** | feat: leggi lo storico dell'AI, con dettaglio e numeri (T3-917) |
| `2026-10-28 18:43:03` | `6e111b1` | blulime7 | `[FEAT]` | **Comune / Sistema** | feat: registra ogni chiamata all'AI nello storico, anche se fallita (T3-916) |
| `2026-10-28 18:42:54` | `7211e31` | blulime7 | `[FEAT]` | **Comune / Sistema** | feat: il piano evita gli orari già occupati dalle altre campagne (T3-922) |
| `2026-10-28 18:39:15` | `573f418` | blulime7 | `[FEAT]` | **Corsia 2 · Campagne & Foto** | feat: il piano v3 scrive la scena delle immagini AI (T3-910) |
| `2026-10-28 18:23:28` | `99e8579` | blulime7 | `[MERGE]` | **Corsia 5 · Frontend & Interfaccia** | Merge branch 'feature/T3-914-storico-ai-pagina' into integrazione-corsia9 |
| `2026-10-28 18:23:28` | `0fa345b` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge branch 'feature/T3-913-analisi-v3' into integrazione-corsia9 |
| `2026-10-28 18:23:10` | `af6ffcb` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge branch 'feature/T3-912-proporzioni-vere' into integrazione-corsia9 |
| `2026-10-28 18:23:10` | `6e4d0b4` | blulime7 | `[MERGE]` | **Corsia 3 · Motore AI & Testi** | Merge branch 'feature/T3-911-prompt-dei-testi' into integrazione-corsia9 |
| `2026-10-28 18:22:50` | `4236f75` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge branch 'feature/T3-904-una-sola-rigenera-testo' into integrazione-corsia9 |
| `2026-10-28 18:22:50` | `bce8845` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge branch 'feature/T3-903-durata-rapida' into integrazione-corsia9 |
| `2026-10-28 18:22:50` | `9377ba6` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge branch 'feature/T3-902-nome-della-bottega' into integrazione-corsia9 |
| `2026-10-28 18:22:50` | `a205895` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge branch 'feature/T3-901-stati-leggibili' into integrazione-corsia9 |
| `2026-10-28 18:22:49` | `edcdd32` | blulime7 | `[MERGE]` | **Corsia 2 · Campagne & Foto** | Merge remote-tracking branch 'origin/feature/T3-909-cambia-foto-fonti' into integrazione-corsia9 |
| `2026-10-28 18:22:12` | `364cb26` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge remote-tracking branch 'origin/feature/T3-908-rigenera-immagine-backend' into integrazione-corsia9 |
| `2026-10-28 18:21:48` | `122fcd3` | blulime7 | `[MERGE]` | **Corsia 2 · Campagne & Foto** | Merge remote-tracking branch 'origin/feature/T3-906-immagini-ai-senza' into integrazione-corsia9 |
| `2026-10-28 18:20:32` | `4ba9016` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge pull request #153 from Full-Stack-AI-ADFlow-Suite-Project/feature/T3-905-campagne-sovrapposte |
| `2026-10-28 18:20:24` | `8718ae8` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge pull request #155 from Full-Stack-AI-ADFlow-Suite-Project/feature/T3-907-migrazione-013 |
| `2026-10-28 18:11:20` | `d04d79d` | blulime7 | `[FEAT]` | **Comune / Sistema** | feat: un solo pulsante Rigenera testo con testo di partenza facoltativo (T3-904) |
| `2026-10-28 18:11:20` | `64f684e` | blulime7 | `[FEAT]` | **Comune / Sistema** | feat: durata rapida di 1 settimana, 2 settimane e 1 mese al passo 10 (T3-903) |
| `2026-10-28 18:04:24` | `3e0f864` | blulime7 | `[FEAT]` | **Corsia 2 · Campagne & Foto** | feat: cambia immagine da gruppo, campagna e archivio (T3-909) |
| `2026-10-28 17:58:20` | `7e026c2` | blulime7 | `[FEAT]` | **Comune / Sistema** | feat: rigenera l'immagine AI di un post (T3-908) |
| `2026-10-28 17:49:30` | `649b2c6` | blulime7 | `[FEAT]` | **Comune / Sistema** | feat: aggiunge lo storico dell'AI con la migrazione 013 (T3-907) |
| `2026-10-28 17:48:40` | `c32da5e` | blulime7 | `[FEAT]` | **Corsia 5 · Frontend & Interfaccia** | feat: pagina Storico AI con filtri e dettaglio, su dati di esempio (T3-914) |
| `2026-10-28 17:46:43` | `1ae4869` | blulime7 | `[FEAT]` | **Corsia 2 · Campagne & Foto** | feat: l'analisi delle foto dà il riquadro del soggetto (T3-913) |
| `2026-10-28 17:42:12` | `ee188bb` | blulime7 | `[FEAT]` | **Corsia 2 · Campagne & Foto** | feat: le foto dentro 4:5 – 1,91:1 non si tagliano (T3-912) |
| `2026-10-28 17:39:02` | `96b8541` | blulime7 | `[FEAT]` | **Comune / Sistema** | feat: i testi non cominciano come gli altri post del canale (T3-911) |
| `2026-10-28 17:30:22` | `c8b3199` | blulime7 | `[FIX]` | **Corsia 2 · Campagne & Foto** | fix: sana il DataError dei testi e prova le immagini AI senza tetto (T3-906) |
| `2026-10-28 17:24:45` | `1fc3c7c` | blulime7 | `[FEAT]` | **Comune / Sistema** | feat: permette campagne sovrapposte e segnala l'avviso (T3-905) |
| `2026-10-28 17:23:17` | `3f8798f` | blulime7 | `[FEAT]` | **Corsia 5 · Frontend & Interfaccia** | feat: mostra il nome della bottega su ogni pagina dell'artigiano (T3-902) |
| `2026-10-28 17:22:37` | `6524a98` | blulime7 | `[FEAT]` | **Comune / Sistema** | feat: etichette leggibili per gli stati dell'operatore (T3-901) |
| `2026-10-28 17:19:27` | `714592c` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge pull request #152 from Full-Stack-AI-ADFlow-Suite-Project/feature/T3-900-preparazione-corsia-9 |
| `2026-10-28 17:16:57` | `a6a66bb` | blulime7 | `[DOCS]` | **Comune / Sistema** | docs: prepara la corsia 9 (T3-900) |
| `2026-10-28 16:14:14` | `36e627c` | blulime7 | `[MERGE]` | **Corsia 4 · Meta & Pubblicazione** | Merge pull request #151 from Full-Stack-AI-ADFlow-Suite-Project/feature/T3-43-pubblicazione-reale-provata |
| `2026-10-28 16:04:07` | `926b921` | blulime7 | `[DOCS]` | **Corsia 4 · Meta & Pubblicazione** | docs: prova la pubblicazione reale dal tick (T3-43) |
| `2026-10-28 15:50:39` | `28c02af` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge pull request #139 from Full-Stack-AI-ADFlow-Suite-Project/feature/T3-09-controlli-sicurezza |
| `2026-10-28 15:49:56` | `e5ed7c3` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge pull request #134 from Full-Stack-AI-ADFlow-Suite-Project/feature/fix-openrouter-e-postgres-italiano |
| `2026-10-28 15:49:51` | `9a8f08f` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge pull request #149 from Full-Stack-AI-ADFlow-Suite-Project/feature/sistema-dopo-corsia8 |
| `2026-10-28 15:47:52` | `6b9ef30` | Nilton | `[MERGE]` | **Corsia 0 · Core, Coda & Architettura** | Merge pull request #147 from Full-Stack-AI-ADFlow-Suite-Project/feature/avvia-server-e-logging |
| `2026-10-28 15:47:46` | `7cbf296` | blulime7 | `[FIX]` | **Comune / Sistema** | fix: i test di sicurezza della configurazione non leggono il .env locale |
| `2026-10-28 15:39:12` | `f8d00f4` | blulime7 | `[DOCS]` | **Corsia 3 · Motore AI & Testi** | docs: brief-ai cita i prompt v2 |
| `2026-10-28 15:39:12` | `cc78f66` | blulime7 | `[TEST]` | **Comune / Sistema** | test: copri il comando pubblica-ora |
| `2026-10-28 15:39:11` | `79a2876` | blulime7 | `[FIX]` | **Corsia 1 · Accesso & Artigiani** | fix: il limite del login nei test scrive su adflow_test, non sul database di sviluppo |
| `2026-10-28 15:31:43` | `b25b725` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge pull request #148 from Full-Stack-AI-ADFlow-Suite-Project/feature/corsia8-integrazione-finale |
| `2026-10-28 15:28:05` | `aec89f0` | tresilvia83-wq | `[FIX]` | **Comune / Sistema** | fix: risolvi duplicazione log uvicorn.error, auto-crea changelog e restringe gitignore |
| `2026-10-28 15:26:53` | `f329701` | blulime7 | `[DOCS]` | **Comune / Sistema** | docs: spunta T3-83…T3-87 della corsia 8 |
| `2026-10-28 15:26:39` | `d9247f4` | blulime7 | `[MERGE]` | **Comune / Sistema** | merge: porta main in test/corsia8-integrata |
| `2026-10-28 15:26:24` | `41a9b67` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge pull request #146 from Full-Stack-AI-ADFlow-Suite-Project/feature/T3-87-verifica-corsia8 |
| `2026-10-28 15:26:13` | `168f22a` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge pull request #145 from Full-Stack-AI-ADFlow-Suite-Project/feature/T3-86-prova-persone |
| `2026-10-28 15:26:03` | `ba8a2f9` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge pull request #144 from Full-Stack-AI-ADFlow-Suite-Project/feature/T3-85-layout-telefono |
| `2026-10-28 15:25:52` | `6384790` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge pull request #143 from Full-Stack-AI-ADFlow-Suite-Project/feature/T3-84-testi |
| `2026-10-28 15:25:14` | `6ffe842` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge pull request #142 from Full-Stack-AI-ADFlow-Suite-Project/feature/T3-83-tema-componenti-base |
| `2026-10-28 15:24:02` | `4795cb3` | blulime7 | `[CHORE]` | **Corsia 5 · Frontend & Interfaccia** | chore: avvia.py lancia API, worker e frontend con un solo comando |
| `2026-10-28 15:24:01` | `31db19c` | blulime7 | `[FIX]` | **Corsia 2 · Campagne & Foto** | fix: l'anteprima del post mostra testo e foto interi, anche l'immagine AI |
| `2026-10-28 15:24:01` | `a8ecccf` | blulime7 | `[FEAT]` | **Corsia 2 · Campagne & Foto** | feat: la demo carica tutte le foto e pubblica-ora per le prove a mano |
| `2026-10-28 15:23:59` | `13731cd` | blulime7 | `[FEAT]` | **Corsia 2 · Campagne & Foto** | feat: l'AI descrive le foto e i testi richiamano l'immagine (prompt v2) |
| `2026-10-28 14:46:04` | `82a83ed` | tresilvia83-wq | `[FEAT]` | **Comune / Sistema** | feat: aggiungi script avvio server con logging e ignora change log e log |
| `2026-10-28 11:11:44` | `30bcf9c` | blulime7 | `[CHORE]` | **Comune / Sistema** | chore: unisci le evidenze della corsia 8 nel branch integrato |
| `2026-10-27 00:40:33` | `4ae8814` | GiorgiTechAi | `[DOCS]` | **Comune / Sistema** | docs: collega tutte le PR e il collaudo aggiornato |
| `2026-10-27 00:38:16` | `96641d6` | GiorgiTechAi | `[TEST]` | **Comune / Sistema** | test: documenta il collaudo isolato della corsia 8 |
| `2026-10-27 00:35:42` | `8cb4e0b` | GiorgiTechAi | `[DOCS]` | **Comune / Sistema** | docs: collega il protocollo alla PR del layout |
| `2026-10-27 00:11:12` | `0643b1a` | GiorgiTechAi | `[DOCS]` | **Comune / Sistema** | docs: escludi le catture desktop duplicate dalle evidenze |
| `2026-10-27 00:10:04` | `cae620c` | GiorgiTechAi | `[DOCS]` | **Comune / Sistema** | docs: pubblica prove responsive e stato reale della corsia 8 |
| `2026-10-26 23:30:08` | `84103d9` | GiorgiTechAi | `[DOCS]` | **Comune / Sistema** | docs: Prepara il protocollo della prova con due persone (T3-86) |
| `2026-10-26 23:25:41` | `9a7b21b` | GiorgiTechAi | `[FIX]` | **Comune / Sistema** | fix: Correggi stepper mobile ed Escape del menu |
| `2026-10-26 23:17:02` | `3fcbba1` | GiorgiTechAi | `[DOCS]` | **Comune / Sistema** | docs: allega inventario dei testi della corsia 8 |
| `2026-10-26 23:15:37` | `524c219` | GiorgiTechAi | `[FEAT]` | **Comune / Sistema** | feat: Adatta layout e telefono (T3-85) |
| `2026-10-26 23:03:38` | `54958e9` | GiorgiTechAi | `[FEAT]` | **Comune / Sistema** | feat: riscrivi i testi di AdFlow per i due ruoli |
| `2026-10-26 22:39:31` | `edbf819` | GiorgiTechAi | `[FEAT]` | **Comune / Sistema** | feat: applica il tema bosco alla corsia 8 (T3-83) |
| `2026-10-26 19:18:28` | `299b582` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge pull request #141 from Full-Stack-AI-ADFlow-Suite-Project/feature/T3-82-scelte-visive |
| `2026-10-26 19:15:28` | `e45135c` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge pull request #140 from Full-Stack-AI-ADFlow-Suite-Project/feature/T3-81-scelte-d-uso |
| `2026-10-26 19:13:00` | `00569e2` | blulime7 | `[DOCS]` | **Comune / Sistema** | docs: scelte visive e prove di stile per la corsia 8 (T3-82) |
| `2026-10-26 19:01:14` | `b780a7e` | blulime7 | `[DOCS]` | **Comune / Sistema** | docs: scelte d'uso per la corsia 8 (T3-81) |
| `2026-10-26 18:02:18` | `2cd7abb` | NiL87AI | `[MERGE]` | **Comune / Sistema** | merge: porta main in feature/T3-09-controlli-sicurezza |
| `2026-10-26 13:44:41` | `c90c324` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge pull request #138 from Full-Stack-AI-ADFlow-Suite-Project/feature/proposta-corsia-8-interfaccia |
| `2026-10-26 13:28:39` | `c79d3c1` | blulime7 | `[DOCS]` | **Comune / Sistema** | docs: crea la corsia 8, interfaccia ed esperienza d'uso (T3-80) |

---

## 🚀 Sprint 3 · MVP Base: AI Vera, Sistemazione Foto e Pubblicazione Meta (15–25 Ottobre 2026)

Totale modifiche registrate nella fase: **36**

| Data e Ora | Commit | Autore | Tipo | Corsia / Modulo | Descrizione Dettagliata della Modifica |
|---|:---:|---|:---:|---|---|
| `2026-10-24 19:41:04` | `6e64243` | blulime7 | `[DOCS]` | **Comune / Sistema** | docs: domande su come procedere e corsia 9 generata nella proposta di accettazione |
| `2026-10-24 19:31:20` | `8a680c2` | blulime7 | `[DOCS]` | **Comune / Sistema** | docs: aggiungi la proposta della corsia 8, interfaccia ed esperienza d'uso |
| `2026-10-24 18:13:14` | `76f8c85` | blulime7 | `[DOCS]` | **Comune / Sistema** | docs: aggiungi la proposta preliminare di accettazione dopo l'MVP |
| `2026-10-23 15:57:16` | `23fce4f` | NiL87AI | `[FEAT]` | **Comune / Sistema** | feat: porta i controlli di sicurezza su main (T3-09) |
| `2026-10-21 13:33:47` | `6a8e2ed` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge pull request #137 from Full-Stack-AI-ADFlow-Suite-Project/ccr-adc21f37-51t6gv |
| `2026-10-21 11:29:57` | `69bf1d1` | Claude | `[MERGE]` | **Comune / Sistema** | Merge remote-tracking branch 'origin/main' into ccr-adc21f37-51t6gv |
| `2026-10-21 13:29:44` | `d4156f5` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge pull request #136 from Full-Stack-AI-ADFlow-Suite-Project/ccr-54021e0e-l5x17x |
| `2026-10-21 11:23:56` | `38738ec` | Claude | `[TEST]` | **Comune / Sistema** | test: percorso delle pagine della corsia 7 (T3-78) |
| `2026-10-21 11:20:46` | `d5d9f70` | Claude | `[FEAT]` | **Corsia 5 · Frontend & Interfaccia** | feat: calendario settimanale, frontend (T3-77) |
| `2026-10-21 11:17:15` | `d46c73b` | Claude | `[FEAT]` | **Corsia 2 · Campagne & Foto** | feat: archivio foto in sola lettura, frontend (T3-76) |
| `2026-10-21 11:14:45` | `32389e1` | Claude | `[FEAT]` | **Corsia 5 · Frontend & Interfaccia** | feat: artigiani per l'operatore, frontend (T3-75) |
| `2026-10-21 11:10:02` | `af85c5d` | Claude | `[FEAT]` | **Comune / Sistema** | feat: calendario settimanale, backend (T3-73) |
| `2026-10-21 11:10:01` | `d50250e` | Claude | `[TEST]` | **Comune / Sistema** | test: i test di T3-71 non dipendono da dati lasciati da altri test |
| `2026-10-21 11:08:26` | `a49db1f` | Claude | `[FEAT]` | **Corsia 5 · Frontend & Interfaccia** | feat: ingresso e campagne dell'artigiano, frontend (T3-74) |
| `2026-10-21 11:00:56` | `2ba7a28` | Claude | `[FEAT]` | **Corsia 2 · Campagne & Foto** | feat: archivio foto in sola lettura, backend (T3-72) |
| `2026-10-21 11:00:30` | `ac9fa56` | Claude | `[FEAT]` | **Comune / Sistema** | feat: artigiani per l'operatore, backend (T3-71) |
| `2026-10-21 10:42:19` | `fabcd22` | Claude | `[DOCS]` | **Comune / Sistema** | docs: pagine statiche della corsia 7 (T3-70) |
| `2026-10-21 10:37:20` | `efe4ed4` | Claude | `[DOCS]` | **Corsia 2 · Campagne & Foto** | docs: prepara la corsia 7, pagine, archivio foto e calendario (T3-70) |
| `2026-10-21 10:24:24` | `1951dfd` | Claude | `[CHORE]` | **Comune / Sistema** | revert: toglie da main la PR #135 (elenco artigiani e restyling) |
| `2026-10-21 12:15:05` | `f671510` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge pull request #135 from Full-Stack-AI-ADFlow-Suite-Project/feature/artigiani-elenco-operatore |
| `2026-10-21 03:27:26` | `b712944` | NiL87AI | `[FEAT]` | **Comune / Sistema** | feat: passa la palette a teal Tailwind e grigi slate con KPI piu' incisivi |
| `2026-10-21 02:57:53` | `32a784a` | NiL87AI | `[DOCS]` | **Comune / Sistema** | docs: annota nel riepilogo il branch usato e lo stato di prototipo-stile |
| `2026-10-21 02:53:59` | `cee16d9` | NiL87AI | `[FEAT]` | **Comune / Sistema** | feat: rifinisci elenco e scheda artigiani con KPI, badge e pannello unico |
| `2026-10-21 02:19:15` | `87aca71` | NiL87AI | `[FEAT]` | **Comune / Sistema** | feat: elenco e scheda artigiani per l'operatore |
| `2026-10-21 02:18:38` | `c50b558` | NiL87AI | `[FEAT]` | **Corsia 1 · Accesso & Artigiani** | feat: restyling interfaccia con verde scuro, login split-screen e testi professionali |
| `2026-10-19 20:22:00` | `3c180ac` | blulime7 | `[FIX]` | **Corsia 0 · Core, Coda & Architettura** | fix: chiave OpenRouter e Procrastinate con PostgreSQL in italiano |
| `2026-10-19 11:42:10` | `67b3773` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge pull request #133 from Full-Stack-AI-ADFlow-Suite-Project/feature/T3-60-interventi-richiesta |
| `2026-10-19 11:32:43` | `980354d` | blulime7 | `[DOCS]` | **Comune / Sistema** | docs: spunta T3-66, percorso a mano della corsia 6 provato |
| `2026-10-19 11:19:51` | `ed829a1` | blulime7 | `[FIX]` | **Comune / Sistema** | fix: caselle di T3-61…65, testo dell'approvazione e badge della richiesta (T3-66) |
| `2026-10-19 10:42:34` | `6ad5364` | blulime7 | `[TEST]` | **Corsia 1 · Accesso & Artigiani** | test: percorso della corsia 6, richiesta all'artigiano e interventi dopo l'approvazione (T3-66) |
| `2026-10-19 10:37:45` | `2f9d20f` | blulime7 | `[FEAT]` | **Corsia 5 · Frontend & Interfaccia** | feat: richiesta all'artigiano nella pagina Vedi campagna e nella pagina Campagna (T3-65) |
| `2026-10-19 10:31:03` | `caede45` | blulime7 | `[FEAT]` | **Corsia 5 · Frontend & Interfaccia** | feat: interventi sui post nella pagina Vedi campagna, sospendi con la nota (T3-64) |
| `2026-10-19 10:22:51` | `09c0317` | blulime7 | `[FEAT]` | **Corsia 2 · Campagne & Foto** | feat: cambia foto del post, in revisione e dopo l'approvazione (T3-62) |
| `2026-10-19 10:17:57` | `4987a9e` | blulime7 | `[FEAT]` | **Corsia 2 · Campagne & Foto** | feat: richiesta all'artigiano, chiedi, carica la foto nuova e invia la risposta (T3-63) |
| `2026-10-19 09:55:17` | `ad0d73d` | blulime7 | `[FEAT]` | **Comune / Sistema** | feat: interventi sul post dopo l'approvazione, sposta, annulla il post, sospendi con la nota (T3-61) |
| `2026-10-19 09:32:00` | `9a4949f` | blulime7 | `[DOCS]` | **Corsia 1 · Accesso & Artigiani** | docs: corsia 6, interventi dopo l'approvazione e richiesta all'artigiano (T3-60) |

---

## 🚀 Sprint 2b · Notifiche, Interventi e Macchina a Stati (11–14 Ottobre 2026)

Totale modifiche registrate nella fase: **168**

| Data e Ora | Commit | Autore | Tipo | Corsia / Modulo | Descrizione Dettagliata della Modifica |
|---|:---:|---|:---:|---|---|
| `2026-10-14 21:44:24` | `81c70e4` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge pull request #130 from Full-Stack-AI-ADFlow-Suite-Project/feature/T3-06-dati-demo |
| `2026-10-14 21:44:19` | `ddc6f08` | blulime7 | `[MERGE]` | **Corsia 3 · Motore AI & Testi** | Merge pull request #131 from Full-Stack-AI-ADFlow-Suite-Project/feature/T3-32-costo-analisi |
| `2026-10-14 21:42:00` | `7245ba1` | blulime7 | `[REFACTOR]` | **Comune / Sistema** | refactor: demo indipendente dalla bottega, con demo.json facoltativo (T3-06) |
| `2026-10-14 21:27:29` | `b46ca10` | blulime7 | `[DOCS]` | **Corsia 2 · Campagne & Foto** | docs: costo dell'analisi delle foto con GPT-4o nella proposta tecnica (T3-32) |
| `2026-10-14 21:23:27` | `b9ad9b0` | blulime7 | `[FEAT]` | **Corsia 2 · Campagne & Foto** | feat: comando demo con bottega, campagna in bozza e foto vere (T3-06) |
| `2026-10-14 20:53:18` | `b1c70dd` | blulime7 | `[MERGE]` | **Corsia 3 · Motore AI & Testi** | Merge pull request #129 from Full-Stack-AI-ADFlow-Suite-Project/feature/T3-32-risultati |
| `2026-10-14 20:50:32` | `8d72fa9` | blulime7 | `[FEAT]` | **Corsia 2 · Campagne & Foto** | feat: anteprima delle foto reali nei post e nei materiali della campagna |
| `2026-10-14 20:23:16` | `a153927` | blulime7 | `[DOCS]` | **Corsia 3 · Motore AI & Testi** | docs: risultati della prova su 10 post e scelta del modello GPT-4o (T3-32) |
| `2026-10-14 18:39:50` | `0978bb5` | blulime7 | `[FEAT]` | **Corsia 1 · Accesso & Artigiani** | feat: calendario editoriale per giorno in Vedi campagna e vista artigiano (T3-53) (#128) |
| `2026-10-14 18:04:44` | `c6179b1` | blulime7 | `[FEAT]` | **Corsia 5 · Frontend & Interfaccia** | feat: pagina Campagna e passo 7 del profilo ridotti all'MVP (T3-52) (#127) |
| `2026-10-14 17:58:47` | `ca391f8` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge pull request #126 from Full-Stack-AI-ADFlow-Suite-Project/feature/T3-51-vedi-campagna-mvp |
| `2026-10-14 17:56:26` | `8655492` | blulime7 | `[MERGE]` | **Corsia 3 · Motore AI & Testi** | Merge pull request #125 from Full-Stack-AI-ADFlow-Suite-Project/feature/T3-32-prova-su-10 |
| `2026-10-14 17:55:58` | `3d46ed7` | blulime7 | `[FEAT]` | **Corsia 2 · Campagne & Foto** | feat: vedi campagna MVP con immagini AI, costo AI e azioni congelate nascoste (T3-51) |
| `2026-10-14 17:54:32` | `1570f20` | blulime7 | `[MERGE]` | **Corsia 2 · Campagne & Foto** | Merge pull request #124 from Full-Stack-AI-ADFlow-Suite-Project/feature/T3-34-immagini-ai-rimpiazzo |
| `2026-10-14 17:49:58` | `9a86a47` | blulime7 | `[FEAT]` | **Corsia 2 · Campagne & Foto** | feat: immagini AI di rimpiazzo con genera_immagine, dicitura e costo registrato; tolte le cartoline (T3-34) |
| `2026-10-14 17:46:34` | `4a7ad1e` | Nilton | `[MERGE]` | **Corsia 4 · Meta & Pubblicazione** | Merge pull request #121 from Full-Stack-AI-ADFlow-Suite-Project/feature/T3-42-adattatore-meta-brief |
| `2026-10-14 17:37:41` | `ff17eb4` | NiL87AI | `[FIX]` | **Corsia 4 · Meta & Pubblicazione** | fix: richiedi post_id per la pubblicazione Facebook |
| `2026-10-14 17:36:21` | `aaead62` | NiL87AI | `[FIX]` | **Corsia 4 · Meta & Pubblicazione** | fix: il messaggio di errore Meta è sempre convertito in stringa |
| `2026-10-14 17:29:32` | `71b8ab5` | NiL87AI | `[TEST]` | **Comune / Sistema** | test: la didascalia si verifica sulla funzione, non sul corpo multipart |
| `2026-10-14 17:28:21` | `87a6aca` | blulime7 | `[FEAT]` | **Corsia 3 · Motore AI & Testi** | feat: comando prova-ai per la prova su 10 post con chiamate, costo, riscritture e post segnalati (T3-32) |
| `2026-10-14 17:18:12` | `249f0f3` | blulime7 | `[MERGE]` | **Corsia 3 · Motore AI & Testi** | Merge pull request #123 from Full-Stack-AI-ADFlow-Suite-Project/feature/T3-33-generazione-mvp |
| `2026-10-14 17:15:12` | `aef9c3a` | blulime7 | `[FEAT]` | **Corsia 2 · Campagne & Foto** | feat: generazione MVP con foto preselezionate e post immagine_ai (T3-33) |
| `2026-10-14 17:09:25` | `b6147dc` | blulime7 | `[MERGE]` | **Corsia 3 · Motore AI & Testi** | Merge pull request #122 from Full-Stack-AI-ADFlow-Suite-Project/feature/T3-31-adattatore-litellm-brief |
| `2026-10-14 16:11:00` | `749c150` | blulime7 | `[MERGE]` | **Corsia 5 · Frontend & Interfaccia** | Merge pull request #119 from Full-Stack-AI-ADFlow-Suite-Project/feature/T3-54-nuovo-artigiano-frontend |
| `2026-10-14 16:10:49` | `840c62f` | blulime7 | `[CHORE]` | **Corsia 3 · Motore AI & Testi** | chore: allinea il branch a origin/main (T3-31) |
| `2026-10-14 16:08:44` | `7ccf19f` | blulime7 | `[FEAT]` | **Corsia 5 · Frontend & Interfaccia** | feat: Nuovo artigiano passa alle API vere; barra laterale senza voci disabilitate; script e screenshot fuori da frontend/tests |
| `2026-10-14 16:06:55` | `216af21` | blulime7 | `[MERGE]` | **Corsia 5 · Frontend & Interfaccia** | Merge remote-tracking branch 'origin/main' into feature/T3-54-nuovo-artigiano-frontend |
| `2026-10-14 16:06:50` | `5c5aa91` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge pull request #110 from Full-Stack-AI-ADFlow-Suite-Project/feature/T3-12-calendario-mvp |
| `2026-10-14 16:05:35` | `f494c61` | blulime7 | `[CHORE]` | **Corsia 3 · Motore AI & Testi** | chore: allinea il branch a origin/main (T3-31) |
| `2026-10-14 16:05:15` | `5d22408` | blulime7 | `[FEAT]` | **Corsia 3 · Motore AI & Testi** | feat: adattatore LiteLLM con costo di ogni chiamata (T3-31, CA-82) |
| `2026-10-14 16:04:39` | `7ed130f` | blulime7 | `[REFACTOR]` | **Comune / Sistema** | refactor: test e docstring del calendario senza MVP; plan §3 al posto della sezione in fondo (T3-12) |
| `2026-10-14 15:57:47` | `2fd5ab1` | NiL87AI | `[FIX]` | **Corsia 4 · Meta & Pubblicazione** | fix: risposta Meta senza id diventa errore definitivo |
| `2026-10-14 15:50:17` | `5455036` | NiL87AI | `[MERGE]` | **Corsia 4 · Meta & Pubblicazione** | Merge remote-tracking branch 'origin/main' into feature/T3-42-adattatore-meta-brief |
| `2026-10-14 15:49:53` | `be11705` | blulime7 | `[CHORE]` | **Comune / Sistema** | chore: allinea il branch a main dopo i merge di #109, #112, #113 e #114 |
| `2026-10-14 15:49:03` | `94621ba` | blulime7 | `[MERGE]` | **Corsia 1 · Accesso & Artigiani** | Merge pull request #109 from Full-Stack-AI-ADFlow-Suite-Project/feature/T3-11-nuovo-artigiano-mvp |
| `2026-10-14 15:46:32` | `a7e128e` | blulime7 | `[REFACTOR]` | **Corsia 1 · Accesso & Artigiani** | refactor: test e docstring del nuovo artigiano senza MVP; plan §2 e §3 al posto della sezione in fondo (T3-11) |
| `2026-10-14 15:45:20` | `b518a8e` | NiL87AI | `[MERGE]` | **Corsia 4 · Meta & Pubblicazione** | Merge remote-tracking branch 'origin/main' into feature/T3-42-adattatore-meta-brief |
| `2026-10-14 15:43:14` | `a82ffe0` | blulime7 | `[MERGE]` | **Corsia 1 · Accesso & Artigiani** | Merge remote-tracking branch 'origin/main' into feature/T3-11-nuovo-artigiano-mvp |
| `2026-10-14 15:43:10` | `f0cc00b` | blulime7 | `[MERGE]` | **Corsia 2 · Campagne & Foto** | Merge pull request #114 from Full-Stack-AI-ADFlow-Suite-Project/feature/T3-22-invio-mvp |
| `2026-10-14 15:39:49` | `0cca732` | NiL87AI | `[DOCS]` | **Corsia 4 · Meta & Pubblicazione** | docs: spunta T3-42, adattatore Meta completato (CA-83) |
| `2026-10-14 15:39:40` | `228984a` | tresilvia83-wq | `[CHORE]` | **Corsia 2 · Campagne & Foto** | chore: allinea branch con T3-21 e T3-23 da origin/main |
| `2026-10-14 15:38:18` | `5605d46` | NiL87AI | `[MERGE]` | **Corsia 4 · Meta & Pubblicazione** | Merge remote-tracking branch 'origin/main' into feature/T3-42-adattatore-meta-brief |
| `2026-10-14 15:37:32` | `07a2c46` | NiL87AI | `[FEAT]` | **Corsia 4 · Meta & Pubblicazione** | feat: adattatore social Meta con canale e indirizzi pubblici (T3-42) |
| `2026-10-14 15:35:57` | `2d63149` | blulime7 | `[MERGE]` | **Corsia 2 · Campagne & Foto** | Merge pull request #113 from Full-Stack-AI-ADFlow-Suite-Project/feature/T3-23-indirizzo-pubblico-foto |
| `2026-10-14 15:34:15` | `782d71e` | tresilvia83-wq | `[CHORE]` | **Comune / Sistema** | chore: allinea branch a origin/main e risolve conflitto tasks.md |
| `2026-10-14 15:30:27` | `35a5fe9` | blulime7 | `[REFACTOR]` | **Corsia 2 · Campagne & Foto** | refactor: indirizzo pubblico della foto letto da leggi_impostazioni(); chiave della firma documentata (T3-23) |
| `2026-10-14 15:26:16` | `560b646` | blulime7 | `[MERGE]` | **Corsia 2 · Campagne & Foto** | Merge remote-tracking branch 'origin/main' into feature/T3-23-indirizzo-pubblico-foto |
| `2026-10-14 15:26:12` | `15787d7` | blulime7 | `[MERGE]` | **Corsia 2 · Campagne & Foto** | Merge pull request #112 from Full-Stack-AI-ADFlow-Suite-Project/feature/T3-21-sistemazione-delle-foto |
| `2026-10-14 15:23:42` | `11720f6` | blulime7 | `[DOCS]` | **Corsia 2 · Campagne & Foto** | docs: docstring di sistemazione_foto senza corsia e task (T3-21) |
| `2026-10-14 15:20:57` | `1db424a` | blulime7 | `[MERGE]` | **Corsia 2 · Campagne & Foto** | Merge remote-tracking branch 'origin/main' into feature/T3-21-sistemazione-delle-foto |
| `2026-10-14 15:13:32` | `7796d62` | tresilvia83-wq | `[FIX]` | **Corsia 2 · Campagne & Foto** | fix: carica FOTO_URL_PUBBLICO da Impostazioni per Instagram (T3-23) |
| `2026-10-14 15:03:54` | `ef6d167` | tresilvia83-wq | `[CHORE]` | **Comune / Sistema** | chore: allinea branch a origin/main |
| `2026-10-14 15:01:26` | `37b00cf` | NiL87AI | `[MERGE]` | **Corsia 4 · Meta & Pubblicazione** | Merge remote-tracking branch 'origin/main' into feature/T3-42-adattatore-meta-brief |
| `2026-10-14 14:54:01` | `4d1b048` | blulime7 | `[MERGE]` | **Corsia 2 · Campagne & Foto** | Merge pull request #120 from Full-Stack-AI-ADFlow-Suite-Project/feature/T3-08-sistemazione-parte-1 |
| `2026-10-14 14:47:50` | `c866185` | blulime7 | `[DOCS]` | **Comune / Sistema** | docs: brief di T3-08 ridotto alla parte 2 |
| `2026-10-14 14:47:45` | `eb6d784` | blulime7 | `[REFACTOR]` | **Comune / Sistema** | refactor: test e commenti senza i nomi degli sprint (T3-08) |
| `2026-10-14 14:47:42` | `bbad9ed` | blulime7 | `[DOCS]` | **Comune / Sistema** | docs: procedura di sicurezza riscritta; README e roadmap aggiornati (T3-08) |
| `2026-10-14 14:47:40` | `2d17ffd` | blulime7 | `[DOCS]` | **Comune / Sistema** | docs: plan §1-§5 con la colonna Stato al posto di Sprint (T3-08) |
| `2026-10-14 14:47:38` | `a5db634` | blulime7 | `[DOCS]` | **Comune / Sistema** | docs: spec con le regole e i criteri fuori MVP nel §7 (T3-08) |
| `2026-10-14 14:47:33` | `5509030` | blulime7 | `[DOCS]` | **Corsia 2 · Campagne & Foto** | docs: tasks e converge con il solo sprint 3; la storia in archivio (T3-08) |
| `2026-10-14 14:26:07` | `f18a75a` | GiorgiTechAi | `[TEST]` | **Comune / Sistema** | test: isola gli appunti nella prova browser di T3-54 |
| `2026-10-14 14:24:56` | `578e047` | Nilton | `[MERGE]` | **Corsia 4 · Meta & Pubblicazione** | Merge pull request #111 from Full-Stack-AI-ADFlow-Suite-Project/feature/T3-41-configurazione-meta-brief |
| `2026-10-14 14:23:37` | `3ca9701` | blulime7 | `[MERGE]` | **Corsia 2 · Campagne & Foto** | Merge pull request #118 from Full-Stack-AI-ADFlow-Suite-Project/chore/archivio-unico |
| `2026-10-14 14:21:45` | `9df2782` | GiorgiTechAi | `[CHORE]` | **Comune / Sistema** | chore: integra la proposta tecnica aggiornata in T3-54 |
| `2026-10-14 14:20:57` | `5fc4364` | NiL87AI | `[DOCS]` | **Corsia 4 · Meta & Pubblicazione** | docs: spunta T3-41 dopo la pubblicazione di prova su Facebook e Instagram |
| `2026-10-14 14:20:57` | `e01dcc3` | blulime7 | `[MERGE]` | **Corsia 2 · Campagne & Foto** | Merge remote-tracking branch 'origin/main' into chore/archivio-unico |
| `2026-10-14 14:20:22` | `252b2da` | GiorgiTechAi | `[CHORE]` | **Comune / Sistema** | chore: allinea T3-54 alla pulizia MVP integrata |
| `2026-10-14 14:19:16` | `ce53d19` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge pull request #117 from Full-Stack-AI-ADFlow-Suite-Project/feature/T3-02-proposta-tecnica |
| `2026-10-14 14:19:00` | `2965673` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge pull request #116 from Full-Stack-AI-ADFlow-Suite-Project/chore/pulizia-mvp |
| `2026-10-14 14:18:54` | `5c279ec` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge pull request #115 from Full-Stack-AI-ADFlow-Suite-Project/feature/T3-03-pagine-statiche-mvp |
| `2026-10-14 14:18:12` | `7d00a74` | GiorgiTechAi | `[FEAT]` | **Corsia 5 · Frontend & Interfaccia** | feat: aggiungi la pagina Nuovo artigiano MVP (T3-54) |
| `2026-10-14 14:00:55` | `5fd5b1b` | blulime7 | `[DOCS]` | **Corsia 2 · Campagne & Foto** | docs: brief e task T3-08, sistemazione definitiva di codice e documenti |
| `2026-10-14 14:00:25` | `4192c7b` | blulime7 | `[DOCS]` | **Corsia 2 · Campagne & Foto** | docs: un solo archivio; pagine statiche in docs/pagine e ADR in docs (ADR-115) |
| `2026-10-14 13:54:55` | `40ab72a` | blulime7 | `[MERGE]` | **Corsia 2 · Campagne & Foto** | Merge branch 'feature/T3-02-proposta-tecnica' into chore/archivio-unico |
| `2026-10-14 13:54:55` | `e3cf353` | blulime7 | `[MERGE]` | **Corsia 2 · Campagne & Foto** | Merge branch 'feature/T3-03-pagine-statiche-mvp' into chore/archivio-unico |
| `2026-10-14 13:28:26` | `61d60e6` | blulime7 | `[DOCS]` | **Comune / Sistema** | docs: proposta tecnica dell'MVP in tre capitoli (T3-02) |
| `2026-10-14 13:26:59` | `14c8807` | blulime7 | `[DOCS]` | **Comune / Sistema** | docs: allinea README, plan, converge e VS Code all'MVP |
| `2026-10-14 13:26:57` | `2a93e0d` | blulime7 | `[DOCS]` | **Corsia 2 · Campagne & Foto** | docs: sposta in docs/archivio note, brief e script dei task chiusi |
| `2026-10-14 13:26:53` | `8ee5f4b` | blulime7 | `[CHORE]` | **Corsia 5 · Frontend & Interfaccia** | chore: togli file inutili e il logo di Vite |
| `2026-10-14 13:26:51` | `a91ba6d` | blulime7 | `[REFACTOR]` | **Comune / Sistema** | refactor: togli i job senza codice e il codice morto del backend |
| `2026-10-14 13:19:44` | `bcfef89` | GiorgiTechAi | `[CHORE]` | **Corsia 1 · Accesso & Artigiani** | chore: allinea il nuovo artigiano al perimetro integrato (#108) |
| `2026-10-14 13:14:03` | `a02328c` | blulime7 | `[DOCS]` | **Comune / Sistema** | docs: spunta T3-03 in tasks.md |
| `2026-10-14 13:13:45` | `189e223` | blulime7 | `[DOCS]` | **Comune / Sistema** | docs: mappa delle pagine con MVP e roadmap (T3-03) |
| `2026-10-14 13:13:44` | `aeb5c96` | blulime7 | `[DOCS]` | **Comune / Sistema** | docs: pagine statiche dell'operatore all'MVP (T3-03) |
| `2026-10-14 13:13:12` | `1205302` | blulime7 | `[DOCS]` | **Corsia 1 · Accesso & Artigiani** | docs: pagine statiche dell'artigiano all'MVP (T3-03) |
| `2026-10-14 13:11:55` | `98d2891` | GiorgiTechAi | `[CHORE]` | **Comune / Sistema** | chore: allinea il calendario MVP al perimetro integrato (#108) |
| `2026-10-14 02:38:33` | `74e4ea9` | tresilvia83-wq | `[FEAT]` | **Corsia 2 · Campagne & Foto** | feat: invio MVP senza minimo di foto e con dichiarazione obbligatoria (T3-22) |
| `2026-10-14 01:02:19` | `1dc8af8` | tresilvia83-wq | `[FEAT]` | **Corsia 2 · Campagne & Foto** | feat: indirizzo pubblico della foto con firma a tempo per Instagram (T3-23) |
| `2026-10-13 23:23:55` | `616ef5a` | NiL87AI | `[DOCS]` | **Comune / Sistema** | docs: aggiorna la versione finta della Graph API a v26.0 |
| `2026-10-13 23:21:47` | `7807418` | NiL87AI | `[DOCS]` | **Corsia 4 · Meta & Pubblicazione** | docs: aggiungi la configurazione della pagina Meta di prova |
| `2026-10-13 23:10:28` | `71a6f52` | Nilton | `[MERGE]` | **Comune / Sistema** | Merge pull request #108 from Full-Stack-AI-ADFlow-Suite-Project/feature/T3-01-perimetro-nel-codice |
| `2026-10-13 23:04:16` | `d9bca3e` | tresilvia83-wq | `[FEAT]` | **Corsia 2 · Campagne & Foto** | feat: sistemazione delle foto per anteprima e pubblicazione (T3-21, CA-81) |
| `2026-10-13 14:39:22` | `1cd414e` | GiorgiTechAi | `[FEAT]` | **Comune / Sistema** | feat: mostra il calendario approvato della campagna (T3-12) |
| `2026-10-13 14:38:30` | `df61007` | blulime7 | `[DOCS]` | **Comune / Sistema** | docs: spunta T3-01 in tasks.md |
| `2026-10-13 14:38:15` | `6a1ab24` | blulime7 | `[CHORE]` | **Corsia 0 · Core, Coda & Architettura** | chore: segna il codice congelato per l'MVP (ADR-114) |
| `2026-10-13 14:36:08` | `f00b36c` | blulime7 | `[REFACTOR]` | **Corsia 2 · Campagne & Foto** | refactor: togli la stella dalle foto (ADR-114, A11) |
| `2026-10-13 14:33:50` | `deb4a94` | GiorgiTechAi | `[FEAT]` | **Corsia 1 · Accesso & Artigiani** | feat: crea il nuovo artigiano nel perimetro MVP (T3-11) |
| `2026-10-13 14:28:16` | `166be34` | blulime7 | `[REFACTOR]` | **Corsia 0 · Core, Coda & Architettura** | refactor: togli il logo della bottega (ADR-114, A7) |
| `2026-10-13 14:17:36` | `c3ed9d3` | blulime7 | `[REFACTOR]` | **Corsia 0 · Core, Coda & Architettura** | refactor: togli il piano debole e Prosegui (ADR-114, A3) |
| `2026-10-13 13:42:19` | `b63906a` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge pull request #107 from Full-Stack-AI-ADFlow-Suite-Project/docs/perimetro-mvp |
| `2026-10-13 13:35:49` | `7d66f4e` | blulime7 | `[TEST]` | **Comune / Sistema** | test: lo sprint 3 MVP non ha la colonna Tocca |
| `2026-10-13 13:31:56` | `b26d01f` | blulime7 | `[CHORE]` | **Corsia 0 · Core, Coda & Architettura** | chore: toglie da main l'apertura dello sprint 3 (T3-01 vecchio), sostituita dal perimetro MVP (ADR-114) |
| `2026-10-13 13:26:47` | `2e06cc1` | Nilton | `[MERGE]` | **Comune / Sistema** | Merge pull request #105 from Full-Stack-AI-ADFlow-Suite-Project/docs/T3-01-spunta |
| `2026-10-13 13:16:22` | `649eeeb` | blulime7 | `[DOCS]` | **Corsia 0 · Core, Coda & Architettura** | docs: perimetro MVP e sprint 3 (ADR-114) |
| `2026-10-13 12:51:40` | `a578d2f` | NiL87AI | `[DOCS]` | **Comune / Sistema** | docs: spunta T3-01 dopo il merge e l'approvazione delle firme |
| `2026-10-13 12:30:08` | `d1a5a84` | Nilton | `[MERGE]` | **Comune / Sistema** | Merge pull request #104 from Full-Stack-AI-ADFlow-Suite-Project/feature/T3-01-apertura |
| `2026-10-13 12:21:34` | `b845982` | NiL87AI | `[FEAT]` | **Corsia 2 · Campagne & Foto** | feat: apre lo sprint 3 con versioni foto e anagrafica |
| `2026-10-13 10:58:37` | `bdc02a6` | Nilton | `[MERGE]` | **Comune / Sistema** | Merge pull request #103 from Full-Stack-AI-ADFlow-Suite-Project/feature/T2b-07-chiusura |
| `2026-10-13 10:55:45` | `6229033` | Nilton | `[MERGE]` | **Corsia 2 · Campagne & Foto** | Merge pull request #102 from Full-Stack-AI-ADFlow-Suite-Project/fix/T2b-53-foto-da-rifare |
| `2026-10-13 10:15:37` | `9682017` | GiorgiTechAi | `[MERGE]` | **Comune / Sistema** | Merge remote-tracking branch 'origin/feature/T2b-07-chiusura' into feature/T2b-07-chiusura |
| `2026-10-13 10:15:36` | `6fadda9` | GiorgiTechAi | `[TEST]` | **Comune / Sistema** | test: separa le verifiche dei CA dal percorso continuo |
| `2026-10-13 10:14:09` | `0c095a4` | GiorgiTechAi | `[DOCS]` | **Comune / Sistema** | docs: registra la verifica della chiusura dello sprint 2b |
| `2026-10-13 10:09:09` | `8c382c0` | NiL87AI | `[TEST]` | **Comune / Sistema** | test: chiudi lo sprint 2b con il percorso di revisione |
| `2026-10-13 09:56:49` | `dea65f4` | GiorgiTechAi | `[MERGE]` | **Corsia 2 · Campagne & Foto** | Merge branch 'fix/T2b-53-foto-da-rifare' into feature/T2b-07-chiusura |
| `2026-10-13 09:56:42` | `b1bde5b` | GiorgiTechAi | `[FIX]` | **Corsia 2 · Campagne & Foto** | fix: mostra le foto da rifare nella campagna respinta |
| `2026-10-13 09:52:38` | `b42b1de` | GiorgiTechAi | `[TEST]` | **Comune / Sistema** | test: verifica il percorso completo della revisione 2b |
| `2026-10-13 09:43:36` | `52a707d` | GiorgiTechAi | `[MERGE]` | **Comune / Sistema** | Merge remote-tracking branch 'origin/main' into feature/T2b-07-chiusura |
| `2026-10-13 09:34:22` | `aa8800b` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge pull request #100 from Full-Stack-AI-ADFlow-Suite-Project/feature/T2b-12-email |
| `2026-10-13 09:33:29` | `efff2b5` | blulime7 | `[MERGE]` | **Corsia 5 · Frontend & Interfaccia** | Merge pull request #101 from Full-Stack-AI-ADFlow-Suite-Project/fix/T2b-stato-task-frontend |
| `2026-10-13 09:23:03` | `26850d2` | GiorgiTechAi | `[MERGE]` | **Corsia 5 · Frontend & Interfaccia** | Merge branch 'fix/T2b-stato-task-frontend' into feature/T2b-07-chiusura |
| `2026-10-13 09:22:09` | `6ceb9cf` | GiorgiTechAi | `[DOCS]` | **Corsia 5 · Frontend & Interfaccia** | docs: normalizza le caselle frontend dello sprint 2b |
| `2026-10-12 18:42:59` | `2b04152` | NiL87AI | `[FEAT]` | **Comune / Sistema** | feat: invia le email transazionali |
| `2026-10-12 17:08:49` | `55fba6d` | Nilton | `[MERGE]` | **Corsia 3 · Motore AI & Testi** | Merge pull request #99 from Full-Stack-AI-ADFlow-Suite-Project/feature/T2b-34-notifiche-generazione |
| `2026-10-12 17:04:28` | `af23b31` | NiL87AI | `[FEAT]` | **Corsia 3 · Motore AI & Testi** | feat: notifica gli operatori alla fine della generazione |
| `2026-10-12 16:55:43` | `bd4f99c` | Nilton | `[MERGE]` | **Comune / Sistema** | Merge pull request #98 from Full-Stack-AI-ADFlow-Suite-Project/feature/T2b-45-da-approvare |
| `2026-10-12 16:53:41` | `2cdcfef` | NiL87AI | `[MERGE]` | **Comune / Sistema** | merge: porta main in feature/T2b-45-da-approvare |
| `2026-10-12 16:50:42` | `4d7d5a4` | Nilton | `[MERGE]` | **Comune / Sistema** | Merge pull request #97 from Full-Stack-AI-ADFlow-Suite-Project/feature/T2b-41-decisioni |
| `2026-10-12 16:48:42` | `2886c8d` | NiL87AI | `[MERGE]` | **Comune / Sistema** | Merge remote-tracking branch 'origin/main' into feature/T2b-45-da-approvare |
| `2026-10-12 16:48:03` | `aaa4bd1` | NiL87AI | `[MERGE]` | **Comune / Sistema** | Merge remote-tracking branch 'origin/main' into feature/T2b-41-decisioni |
| `2026-10-12 16:45:48` | `61e8b13` | NiL87AI | `[MERGE]` | **Comune / Sistema** | Merge remote-tracking branch 'origin/main' into feature/T2b-41-decisioni |
| `2026-10-12 16:42:43` | `d473931` | NiL87AI | `[FEAT]` | **Comune / Sistema** | feat: aggiungi campagne da approvare e notifica post_fallito |
| `2026-10-12 16:40:39` | `f2e2271` | Nilton | `[MERGE]` | **Corsia 1 · Accesso & Artigiani** | Merge pull request #96 from Full-Stack-AI-ADFlow-Suite-Project/feature/T2b-22-viste-artigiano |
| `2026-10-12 16:38:54` | `c13449c` | NiL87AI | `[MERGE]` | **Comune / Sistema** | Merge branch 'feature/T2b-21-funzioni-campagne' into feature/T2b-45-da-approvare |
| `2026-10-12 16:37:28` | `0ff681b` | Nilton | `[MERGE]` | **Comune / Sistema** | Merge pull request #95 from Full-Stack-AI-ADFlow-Suite-Project/feature/T2b-21-funzioni-campagne |
| `2026-10-12 16:34:03` | `577bc36` | NiL87AI | `[FEAT]` | **Comune / Sistema** | feat: nota interna, respingi e togli il canale in revisione (T2b-41) |
| `2026-10-12 16:27:44` | `38ea57d` | Nilton | `[MERGE]` | **Comune / Sistema** | Merge pull request #86 from Full-Stack-AI-ADFlow-Suite-Project/feature/T2a-52-rifiniture-logo |
| `2026-10-12 16:24:22` | `6a0304b` | Nilton | `[MERGE]` | **Comune / Sistema** | Merge pull request #94 from Full-Stack-AI-ADFlow-Suite-Project/feature/T2b-44-scadenze |
| `2026-10-12 16:23:49` | `4e7d203` | NiL87AI | `[MERGE]` | **Comune / Sistema** | Merge branch 'feature/T2b-21-funzioni-campagne' into feature/T2b-41-decisioni |
| `2026-10-12 16:22:36` | `5cb778c` | NiL87AI | `[FEAT]` | **Corsia 1 · Accesso & Artigiani** | feat: viste della campagna per l'artigiano (T2b-22, prestito) |
| `2026-10-12 16:15:33` | `9011bfd` | NiL87AI | `[MERGE]` | **Comune / Sistema** | merge: porta main in feature/T2b-44-scadenze |
| `2026-10-12 16:10:17` | `efabcd3` | NiL87AI | `[FEAT]` | **Comune / Sistema** | feat: corpi di togli_canale, ultima_nota e campagne_di (T2b-21, prestito) |
| `2026-10-12 16:09:31` | `9370386` | Nilton | `[MERGE]` | **Comune / Sistema** | Merge pull request #93 from Full-Stack-AI-ADFlow-Suite-Project/feature/T2b-43-sospendi-riattiva-annulla |
| `2026-10-12 16:05:17` | `612d38a` | NiL87AI | `[MERGE]` | **Comune / Sistema** | Merge remote-tracking branch 'origin/main' into feature/T2b-44-scadenze |
| `2026-10-12 16:04:54` | `3f43ba4` | NiL87AI | `[MERGE]` | **Comune / Sistema** | merge: porta main in feature/T2b-43-sospendi-riattiva-annulla |
| `2026-10-12 16:00:04` | `40a2957` | Nilton | `[MERGE]` | **Comune / Sistema** | Merge pull request #92 from Full-Stack-AI-ADFlow-Suite-Project/feature/T2b-42-interventi-sul-post |
| `2026-10-12 15:46:34` | `e6e068d` | NiL87AI | `[FEAT]` | **Corsia 4 · Meta & Pubblicazione** | feat: scadenze del tick per post e campagne ferme (T2b-44) |
| `2026-10-12 15:22:33` | `a076ea5` | NiL87AI | `[FEAT]` | **Comune / Sistema** | feat: sospendi, riattiva e annulla la campagna dalla revisione (T2b-43) |
| `2026-10-12 15:09:19` | `b00c3e0` | Nilton | `[MERGE]` | **Comune / Sistema** | Merge pull request #88 from Full-Stack-AI-ADFlow-Suite-Project/feature/T2b-11-notifiche |
| `2026-10-12 14:54:46` | `b53647b` | NiL87AI | `[FEAT]` | **Comune / Sistema** | feat: interventi sul post da revisione, con modifica, spunta, rigenera e riprogramma (T2b-42) |
| `2026-10-12 13:18:11` | `4a0568a` | blulime7 | `[MERGE]` | **Corsia 1 · Accesso & Artigiani** | Merge pull request #91 from Full-Stack-AI-ADFlow-Suite-Project/feature/T2b-53-viste-artigiano |
| `2026-10-12 13:15:39` | `dad32bf` | blulime7 | `[FEAT]` | **Corsia 5 · Frontend & Interfaccia** | feat: pagina Campagna dell'artigiano con più campagne, canale tolto e campagne passate (T2b-53) |
| `2026-10-12 13:10:27` | `902cc14` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge pull request #90 from Full-Stack-AI-ADFlow-Suite-Project/feature/T2b-52-decisioni |
| `2026-10-12 13:08:08` | `349c12c` | blulime7 | `[FEAT]` | **Comune / Sistema** | feat: decisioni sulla campagna in Vedi campagna e Campagne da approvare con conteggi (T2b-52) |
| `2026-10-12 13:01:49` | `ce6a733` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge pull request #89 from Full-Stack-AI-ADFlow-Suite-Project/feature/T2b-51-azioni-sul-post |
| `2026-10-12 12:59:33` | `5d2d74c` | blulime7 | `[FEAT]` | **Comune / Sistema** | feat: azioni sul post in Vedi campagna, con modifica, spunta e rigenera (T2b-51) |
| `2026-10-12 12:48:10` | `349c50a` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge pull request #87 from Full-Stack-AI-ADFlow-Suite-Project/feature/T2b-33-rigenera |
| `2026-10-12 12:46:52` | `9d4df16` | GiorgiTechAi | `[MERGE]` | **Comune / Sistema** | Merge remote-tracking branch 'origin/main' into feature/T2b-11-notifiche |
| `2026-10-12 12:46:51` | `9232bb9` | GiorgiTechAi | `[FEAT]` | **Comune / Sistema** | feat: crea le notifiche per destinatario senza doppioni (T2b-11) |
| `2026-10-12 12:45:24` | `e836ec8` | blulime7 | `[FEAT]` | **Comune / Sistema** | feat: rigenera il testo di un post, da zero o da un testo proposto (T2b-33) |
| `2026-10-12 12:38:37` | `a394551` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge pull request #85 from Full-Stack-AI-ADFlow-Suite-Project/feature/T2b-32-modifica-mano |
| `2026-10-12 12:36:15` | `68567d5` | blulime7 | `[FEAT]` | **Comune / Sistema** | feat: modifica a mano del post come nuova versione dell'operatore (T2b-32) |
| `2026-10-12 12:32:28` | `84005ac` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge pull request #84 from Full-Stack-AI-ADFlow-Suite-Project/feature/T2b-31-funzioni-sui-post |
| `2026-10-12 12:32:22` | `120b59c` | GiorgiTechAi | `[MERGE]` | **Comune / Sistema** | Merge remote-tracking branch 'origin/main' into feature/T2a-52-rifiniture-logo |
| `2026-10-12 12:32:21` | `351e986` | GiorgiTechAi | `[FIX]` | **Comune / Sistema** | fix: aggiorna anteprima logo e guida il primo salvataggio del profilo |
| `2026-10-12 12:31:20` | `b9301e0` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge pull request #83 from Full-Stack-AI-ADFlow-Suite-Project/feature/T2b-01-apertura |
| `2026-10-12 12:30:17` | `18ff208` | blulime7 | `[FEAT]` | **Corsia 3 · Motore AI & Testi** | feat: scrivi le funzioni sui post e l'arresto della generazione (T2b-31) |
| `2026-10-12 12:22:17` | `0fd66f5` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge pull request #82 from Full-Stack-AI-ADFlow-Suite-Project/feature/T2a-07-chiusura-sprint-2a |
| `2026-10-12 12:21:41` | `db74160` | blulime7 | `[FEAT]` | **Comune / Sistema** | feat: apri lo sprint 2b con la migrazione 011, le firme della revisione e le fabbriche (T2b-01) |

---

## 🚀 Sprint 2a · Profilo Bottega, Gruppi Foto e Invio Bozza (8–10 Ottobre 2026)

Totale modifiche registrate nella fase: **170**

| Data e Ora | Commit | Autore | Tipo | Corsia / Modulo | Descrizione Dettagliata della Modifica |
|---|:---:|---|:---:|---|---|
| `2026-10-10 19:25:00` | `b2f5bb5` | blulime7 | `[FEAT]` | **Comune / Sistema** | feat: chiusura dello sprint 2a con percorso completo e api reali (T2a-07) |
| `2026-10-10 19:09:09` | `ef5da0f` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge pull request #81 from Full-Stack-AI-ADFlow-Suite-Project/fix/ritocchi-navigazione-operatore |
| `2026-10-10 19:06:49` | `3b3f74e` | blulime7 | `[FIX]` | **Comune / Sistema** | fix: abilita navigazione profilo in sidebar e rifinisce dettagli operatore |
| `2026-10-10 19:00:27` | `fefe7f7` | blulime7 | `[MERGE]` | **Corsia 5 · Frontend & Interfaccia** | Merge pull request #77 from Full-Stack-AI-ADFlow-Suite-Project/feature/76-frontend-nuovo-stile |
| `2026-10-10 18:57:37` | `0eca212` | blulime7 | `[MERGE]` | **Corsia 5 · Frontend & Interfaccia** | Merge pull request #80 from Full-Stack-AI-ADFlow-Suite-Project/feature/T2a-53-pagina-campagna-completa |
| `2026-10-10 18:53:13` | `2f434ba` | blulime7 | `[FEAT]` | **Corsia 5 · Frontend & Interfaccia** | feat: completa la pagina Campagna con Bentornato, modifica bozza e avvisi (T2a-53) |
| `2026-10-10 18:36:40` | `40782af` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge pull request #79 from Full-Stack-AI-ADFlow-Suite-Project/feature/T2a-52-passo-7-profilo |
| `2026-10-10 18:32:37` | `2701305` | blulime7 | `[FEAT]` | **Corsia 2 · Campagne & Foto** | feat: aggiungi logo e archivio della bottega al passo 7 del profilo (T2a-52) |
| `2026-10-10 18:25:49` | `8eee375` | blulime7 | `[MERGE]` | **Corsia 5 · Frontend & Interfaccia** | Merge pull request #70 from Full-Stack-AI-ADFlow-Suite-Project/feature/T2a-51-pagina-profilo-passi |
| `2026-10-10 18:22:42` | `12a79f6` | blulime7 | `[REFACTOR]` | **Corsia 5 · Frontend & Interfaccia** | refactor: allinea la pagina Profilo allo stile delle pagine statiche e decomprimi il layout |
| `2026-10-10 18:13:30` | `8c4db91` | blulime7 | `[MERGE]` | **Corsia 5 · Frontend & Interfaccia** | Merge branch 'main' into feature/T2a-51-pagina-profilo-passi |
| `2026-10-10 18:12:07` | `5181e29` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge pull request #78 from Full-Stack-AI-ADFlow-Suite-Project/docs/pagine-nuovo-stile |
| `2026-10-10 17:51:29` | `5f979c7` | blulime7 | `[DOCS]` | **Corsia 0 · Core, Coda & Architettura** | docs: porta le pagine statiche nel nuovo stile (ADR-113) |
| `2026-10-10 17:27:17` | `d2abd2f` | blulime7 | `[FEAT]` | **Corsia 5 · Frontend & Interfaccia** | feat: allinea tema e cornice del frontend al nuovo stile delle pagine (#76) |
| `2026-10-10 16:54:55` | `49a5f08` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge pull request #74 from Full-Stack-AI-ADFlow-Suite-Project/fix/63-422-frase-in-italiano |
| `2026-10-10 16:54:49` | `b264fc8` | blulime7 | `[MERGE]` | **Corsia 2 · Campagne & Foto** | Merge pull request #73 from Full-Stack-AI-ADFlow-Suite-Project/docs/plan-foto-d-archivio-nel-piano |
| `2026-10-10 16:54:46` | `61d895b` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge pull request #72 from Full-Stack-AI-ADFlow-Suite-Project/feature/T2a-32-logo-nelle-cartoline |
| `2026-10-10 16:52:40` | `fc43c05` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge remote-tracking branch 'origin/main' into feature/T2a-32-logo-nelle-cartoline |
| `2026-10-10 16:49:14` | `b0597fe` | blulime7 | `[FIX]` | **Comune / Sistema** | fix: rispondi al 422 dello schema con una frase in italiano (#63) |
| `2026-10-10 16:45:11` | `b34c9d2` | blulime7 | `[DOCS]` | **Corsia 2 · Campagne & Foto** | docs: allinea plan §4 e §5 alle foto d'archivio nel piano |
| `2026-10-10 16:42:37` | `0ea4169` | blulime7 | `[MERGE]` | **Corsia 2 · Campagne & Foto** | Merge pull request #71 from Full-Stack-AI-ADFlow-Suite-Project/feature/T2a-31-foto-d-archivio |
| `2026-10-10 16:41:56` | `c9be478` | blulime7 | `[CHORE]` | **Comune / Sistema** | chore: porta T2a-31 nel branch di T2a-32 e tieni spuntate le due caselle |
| `2026-10-10 16:31:02` | `5f3a77b` | blulime7 | `[FEAT]` | **Comune / Sistema** | feat: metti il logo della bottega sulle cartoline (T2a-32) |
| `2026-10-10 16:23:41` | `019cddf` | blulime7 | `[MERGE]` | **Corsia 2 · Campagne & Foto** | Merge pull request #68 from Full-Stack-AI-ADFlow-Suite-Project/feature/T2a-41-foto-pubblicate |
| `2026-10-10 16:23:25` | `f012f6f` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge pull request #69 from Full-Stack-AI-ADFlow-Suite-Project/feature/T2a-12-logo |
| `2026-10-10 16:03:14` | `49f8311` | blulime7 | `[FEAT]` | **Corsia 2 · Campagne & Foto** | feat: usa le foto d'archivio nel piano della campagna (T2a-31) |
| `2026-10-10 15:54:03` | `64f17fe` | GiorgiTechAi | `[FIX]` | **Comune / Sistema** | fix: esegui il caricamento del logo nel thread di lavoro |
| `2026-10-10 15:38:20` | `7d15da7` | GiorgiTechAi | `[FEAT]` | **Comune / Sistema** | feat: completa i nove passi del profilo della bottega (T2a-51) |
| `2026-10-10 15:13:56` | `cc9bcb0` | GiorgiTechAi | `[FEAT]` | **Comune / Sistema** | feat: gestisci il logo della bottega T2a-12 |
| `2026-10-10 14:23:22` | `328fe86` | NiL87AI | `[FEAT]` | **Corsia 2 · Campagne & Foto** | feat: segna le foto pubblicate per canale |
| `2026-10-10 14:01:53` | `5940cfb` | Nilton | `[MERGE]` | **Corsia 2 · Campagne & Foto** | Merge pull request #67 from Full-Stack-AI-ADFlow-Suite-Project/feature/T2a-22-archivio |
| `2026-10-10 14:01:01` | `397dfce` | Nilton | `[MERGE]` | **Comune / Sistema** | Merge pull request #66 from Full-Stack-AI-ADFlow-Suite-Project/feature/T2a-21-modifica-bozza |
| `2026-10-10 13:21:24` | `b2dd333` | tresilvia83-wq | `[FIX]` | **Comune / Sistema** | fix: normalizza in UTC in segna_pubblicata, usa import relativi e spunta T2a-22 |
| `2026-10-10 13:17:05` | `b5c0842` | Nilton | `[MERGE]` | **Comune / Sistema** | Merge pull request #46 from Full-Stack-AI-ADFlow-Suite-Project/feature/s2a-profilo-bottega |
| `2026-10-10 13:08:02` | `fcaaf81` | tresilvia83-wq | `[MERGE]` | **Corsia 2 · Campagne & Foto** | Merge branch 'feature/T2a-21-modifica-bozza' into feature/T2a-22-archivio |
| `2026-10-10 13:06:30` | `795d9d2` | tresilvia83-wq | `[FIX]` | **Comune / Sistema** | fix: usa import relativi in bozza.py e spunta T2a-21 in tasks.md |
| `2026-10-10 12:58:53` | `8179eff` | Nilton | `[MERGE]` | **Comune / Sistema** | Merge pull request #65 from Full-Stack-AI-ADFlow-Suite-Project/feature/T2a-01-apertura |
| `2026-10-10 12:17:18` | `428d1cd` | tresilvia83-wq | `[FIX]` | **Comune / Sistema** | fix: allinea 404 per profilo bottega assente in modifica bozza (T2a-21) |
| `2026-10-10 12:13:57` | `c5f469e` | tresilvia83-wq | `[MERGE]` | **Comune / Sistema** | Merge remote-tracking branch 'origin/feature/T2a-01-apertura' into feature/T2a-21-modifica-bozza |
| `2026-10-10 12:06:28` | `0570899` | tresilvia83-wq | `[FIX]` | **Corsia 2 · Campagne & Foto** | fix: perfeziona robustezza concorrenza e casi limite archivio e bozza (T2a-21, T2a-22) |
| `2026-10-10 11:51:41` | `67dc9d0` | tresilvia83-wq | `[FEAT]` | **Corsia 2 · Campagne & Foto** | feat: implementa archivio della bottega e contratti foto_di_archivio (T2a-22) |
| `2026-10-10 10:46:20` | `8514e10` | tresilvia83-wq | `[CHORE]` | **Corsia 2 · Campagne & Foto** | chore: integra T2a-01-apertura in feature/T2a-22-archivio |
| `2026-10-10 10:43:33` | `9fa80d8` | tresilvia83-wq | `[FEAT]` | **Comune / Sistema** | feat: implementa modifica della bozza PATCH /campagne/{id} (T2a-21) |
| `2026-10-10 09:59:50` | `0c634d9` | blulime7 | `[DOCS]` | **Corsia 2 · Campagne & Foto** | docs: fissa forma di logo e archivio, contratti e percorso a mano dello sprint 2a e spunta T2a-01 |
| `2026-10-10 09:59:45` | `348e66e` | blulime7 | `[FEAT]` | **Corsia 2 · Campagne & Foto** | feat: apri lo sprint 2a con la migrazione 010, le firme dell'archivio e le fabbriche |
| `2026-10-10 09:46:02` | `b3fe00e` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge pull request #62 from Full-Stack-AI-ADFlow-Suite-Project/feature/T1-07-chiusura |
| `2026-10-10 09:45:56` | `247aef2` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge pull request #61 from Full-Stack-AI-ADFlow-Suite-Project/chore/allinea-npm-windows |
| `2026-10-10 09:40:02` | `0d5aa23` | blulime7 | `[DOCS]` | **Corsia 0 · Core, Coda & Architettura** | docs: spunta T1-07 e porta in plan, converge e README orologio di prova, worker e partenza dei job |
| `2026-10-10 09:39:59` | `abd3012` | blulime7 | `[FIX]` | **Corsia 0 · Core, Coda & Architettura** | fix: fa partire i job qualche secondo dopo l'accodamento, quando chi accoda ha salvato |
| `2026-10-10 09:31:21` | `bc00b3b` | blulime7 | `[FEAT]` | **Corsia 2 · Campagne & Foto** | feat: porta il frontend sulle API vere, con la fotografia del profilo com'è nel backend |
| `2026-10-10 09:31:05` | `5260bf5` | blulime7 | `[FIX]` | **Corsia 0 · Core, Coda & Architettura** | fix: il worker carica il modello intero, così i job salvano righe con chiavi verso gli altri moduli |
| `2026-10-10 09:22:55` | `d3c2e65` | blulime7 | `[TEST]` | **Comune / Sistema** | test: percorso completo dello sprint 1 via API, dal seed alla campagna conclusa |
| `2026-10-10 09:22:51` | `5bde630` | blulime7 | `[FEAT]` | **Corsia 0 · Core, Coda & Architettura** | feat: manda avanti l'orologio di API e worker per le prove a mano (OROLOGIO_GIORNI_AVANTI) |
| `2026-10-10 09:14:35` | `3017b35` | blulime7 | `[FIX]` | **Corsia 5 · Frontend & Interfaccia** | fix: lancia npm con il percorso intero, così allinea.py installa il frontend anche su Windows |
| `2026-10-09 15:33:21` | `71d8b86` | GiorgiTechAi | `[MERGE]` | **Comune / Sistema** | Merge remote-tracking branch 'origin/main' into feature/s2a-profilo-bottega |
| `2026-10-09 15:32:42` | `bc3f03f` | Nilton | `[MERGE]` | **Comune / Sistema** | Merge pull request #59 from Full-Stack-AI-ADFlow-Suite-Project/feature/T1-24-invio-riprova |
| `2026-10-09 15:20:28` | `95c79ee` | Nilton | `[MERGE]` | **Comune / Sistema** | Merge pull request #60 from Full-Stack-AI-ADFlow-Suite-Project/feature/T1-53-operatore |
| `2026-10-09 15:11:41` | `a3b0feb` | NiL87AI | `[FEAT]` | **Corsia 5 · Frontend & Interfaccia** | feat: realizza la pagina operatore Campagne da approvare e Vedi campagna |
| `2026-10-09 15:00:11` | `592d50a` | GiorgiTechAi | `[FIX]` | **Corsia 2 · Campagne & Foto** | fix: uniforma le foto all invio e completa i test della riprova |
| `2026-10-09 14:55:11` | `63bfbaa` | GiorgiTechAi | `[MERGE]` | **Comune / Sistema** | Merge remote-tracking branch 'origin/main' into feature/T1-24-invio-riprova |
| `2026-10-09 14:41:38` | `7eb0f6a` | GiorgiTechAi | `[DOCS]` | **Comune / Sistema** | docs: registra il profilo completato come T2a-11 |
| `2026-10-09 14:37:41` | `7a2e4d4` | GiorgiTechAi | `[MERGE]` | **Comune / Sistema** | Merge remote-tracking branch 'origin/main' into feature/s2a-profilo-bottega |
| `2026-10-09 14:34:40` | `49990ef` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge pull request #58 from Full-Stack-AI-ADFlow-Suite-Project/docs/sprint-2-3-pianificazione |
| `2026-10-09 14:34:33` | `44efbe1` | blulime7 | `[MERGE]` | **Corsia 1 · Accesso & Artigiani** | Merge pull request #57 from Full-Stack-AI-ADFlow-Suite-Project/feature/T1-52-campagna-artigiano |
| `2026-10-09 14:34:29` | `39e86be` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge pull request #56 from Full-Stack-AI-ADFlow-Suite-Project/feature/T1-34-genera-campagna |
| `2026-10-09 14:31:22` | `af3b2ea` | GiorgiTechAi | `[FEAT]` | **Comune / Sistema** | feat: implementa invio e riprova delle campagne T1-24 |
| `2026-10-09 14:25:06` | `e3e2a5b` | blulime7 | `[DOCS]` | **Comune / Sistema** | docs: T1-52 è già nella PR #57 di Nilton |
| `2026-10-09 14:23:49` | `5a4e4c1` | blulime7 | `[DOCS]` | **Comune / Sistema** | docs: pianifica gli sprint 2a, 2b e 3 e assegna i task |
| `2026-10-09 14:23:37` | `31924ea` | blulime7 | `[CHORE]` | **Comune / Sistema** | chore: allinea.py legge più sprint, le sigle come T2a-11 e la colonna Tocca |
| `2026-10-09 14:17:53` | `5e5bb91` | NiL87AI | `[FEAT]` | **Corsia 5 · Frontend & Interfaccia** | feat: realizza la pagina Campagna dell'artigiano |
| `2026-10-09 14:04:39` | `57b7353` | Nilton | `[MERGE]` | **Corsia 5 · Frontend & Interfaccia** | Merge pull request #55 from Full-Stack-AI-ADFlow-Suite-Project/feature/T1-51-base-frontend |
| `2026-10-09 14:00:44` | `eb5a19d` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge pull request #54 from Full-Stack-AI-ADFlow-Suite-Project/feature/T1-35-cartoline |
| `2026-10-09 14:00:38` | `4e497ed` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge pull request #53 from Full-Stack-AI-ADFlow-Suite-Project/chore/pillow |
| `2026-10-09 13:59:24` | `6e6f492` | blulime7 | `[DOCS]` | **Comune / Sistema** | docs: spunta T1-34 in tasks.md |
| `2026-10-09 13:58:51` | `d9f354f` | blulime7 | `[FEAT]` | **Comune / Sistema** | feat: aggiungi il job genera_campagna a tappe (T1-34) |
| `2026-10-09 13:54:34` | `247e3a8` | NiL87AI | `[MERGE]` | **Corsia 5 · Frontend & Interfaccia** | Merge remote-tracking branch 'origin/main' into feature/T1-51-base-frontend |
| `2026-10-09 13:49:39` | `91d5388` | blulime7 | `[DOCS]` | **Comune / Sistema** | docs: spunta T1-35 in tasks.md |
| `2026-10-09 13:49:31` | `0567531` | blulime7 | `[FEAT]` | **Comune / Sistema** | feat: aggiungi le cartoline dei post riempitivo (T1-35) |
| `2026-10-09 13:48:04` | `bf59b89` | NiL87AI | `[FEAT]` | **Corsia 5 · Frontend & Interfaccia** | feat: aggiungi la base del frontend con accesso e rotte per ruolo (T1-51) |
| `2026-10-09 13:42:00` | `9197bc2` | blulime7 | `[CHORE]` | **Comune / Sistema** | chore: dichiara pillow per le cartoline (corsia 0) |
| `2026-10-09 13:37:08` | `c2acfef` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge pull request #52 from Full-Stack-AI-ADFlow-Suite-Project/feature/T1-33-validatore-regole-due |
| `2026-10-09 13:33:25` | `71dc478` | blulime7 | `[DOCS]` | **Comune / Sistema** | docs: spunta T1-33 in tasks.md |
| `2026-10-09 13:33:23` | `311de9b` | blulime7 | `[FEAT]` | **Comune / Sistema** | feat: aggiungi il validatore a regole a due livelli (T1-33) |
| `2026-10-09 13:27:35` | `4743a41` | blulime7 | `[MERGE]` | **Corsia 3 · Motore AI & Testi** | Merge pull request #51 from Full-Stack-AI-ADFlow-Suite-Project/chore/litellm |
| `2026-10-09 13:26:01` | `dfd49ab` | blulime7 | `[CHORE]` | **Corsia 3 · Motore AI & Testi** | chore: dichiara litellm per il provider AI vero (corsia 0) |
| `2026-10-09 13:21:06` | `c6fba15` | GiorgiTechAi | `[MERGE]` | **Comune / Sistema** | Merge remote-tracking branch 'origin/main' into feature/s2a-profilo-bottega |
| `2026-10-09 13:18:01` | `6816388` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge pull request #49 from Full-Stack-AI-ADFlow-Suite-Project/feature/T1-31-adattatore-ai |
| `2026-10-09 13:14:57` | `5276c53` | blulime7 | `[DOCS]` | **Comune / Sistema** | docs: spunta T1-31 in tasks.md |
| `2026-10-09 13:14:52` | `8424eb3` | blulime7 | `[FEAT]` | **Comune / Sistema** | feat: aggiungi l'adattatore AI con il provider finto (T1-31) |
| `2026-10-09 13:12:06` | `9ad9830` | GiorgiTechAi | `[MERGE]` | **Comune / Sistema** | Merge remote-tracking branch 'origin/main' into feature/s2a-profilo-bottega |
| `2026-10-09 13:04:56` | `4bc5f00` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge pull request #48 from Full-Stack-AI-ADFlow-Suite-Project/feature/T1-32-limiti-controllo-piano |
| `2026-10-09 13:04:49` | `303e641` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge pull request #47 from Full-Stack-AI-ADFlow-Suite-Project/feature/44-45-post-chiesti-e-stelle |
| `2026-10-09 12:56:45` | `13b9ce0` | blulime7 | `[REFACTOR]` | **Comune / Sistema** | refactor: usa campagne.post_chiesti() e la regola nuova sulle stelle nel controllo del piano |
| `2026-10-09 12:53:08` | `0e808bf` | blulime7 | `[DOCS]` | **Comune / Sistema** | docs: spunta T1-32 in tasks.md |
| `2026-10-09 12:53:08` | `9e560dd` | blulime7 | `[FEAT]` | **Comune / Sistema** | feat: aggiungi limiti e controllo del piano (T1-32) |
| `2026-10-09 12:53:01` | `c2a7694` | blulime7 | `[DOCS]` | **Comune / Sistema** | docs: limita R-23 ai post chiesti quando le stelle sono di più (#45) |
| `2026-10-09 12:52:56` | `dff5153` | blulime7 | `[FEAT]` | **Corsia 0 · Core, Coda & Architettura** | feat: aggiungi il contratto campagne.post_chiesti() (#44) |
| `2026-10-09 12:42:11` | `ccc28fb` | GiorgiTechAi | `[FEAT]` | **Comune / Sistema** | feat: leggi e salva il profilo della bottega |
| `2026-10-09 12:07:05` | `311737b` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge pull request #43 from Full-Stack-AI-ADFlow-Suite-Project/docs/allineamento-con-un-comando |
| `2026-10-09 12:07:00` | `e6bab3d` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge pull request #42 from Full-Stack-AI-ADFlow-Suite-Project/feature/39-41-chiusura-revisione |
| `2026-10-09 12:01:41` | `9c2c6da` | blulime7 | `[DOCS]` | **Comune / Sistema** | docs: riallinea AGENTS, README e canale agenti allo stato di main |
| `2026-10-09 12:01:38` | `3d55292` | blulime7 | `[CHORE]` | **Comune / Sistema** | chore: aggiungi allinea.py, un comando per allinearsi e sapere quale task prendere |
| `2026-10-09 11:55:56` | `006de78` | blulime7 | `[CHORE]` | **Comune / Sistema** | chore: togli i file md da prettier |
| `2026-10-09 11:54:33` | `2c09b36` | blulime7 | `[DOCS]` | **Corsia 0 · Core, Coda & Architettura** | docs: porta in plan, constitution e tasks i contratti, il 413 e il gruppo obbligatorio (#39-41) |
| `2026-10-09 11:54:29` | `dde5e9e` | blulime7 | `[REFACTOR]` | **Corsia 0 · Core, Coda & Architettura** | refactor: campagne legge artigiani dai contratti e chiede il gruppo al caricamento (#39, #41) |
| `2026-10-09 11:54:26` | `bad57ba` | blulime7 | `[FEAT]` | **Comune / Sistema** | feat: rifiuta con 413 le richieste oltre RICHIESTA_MAX_BYTE (#40) |
| `2026-10-09 11:54:23` | `a2fa516` | blulime7 | `[CHORE]` | **Comune / Sistema** | chore: togli i file md da prettier |
| `2026-10-09 11:40:58` | `32cbe18` | blulime7 | `[MERGE]` | **Corsia 2 · Campagne & Foto** | Merge pull request #24 from Full-Stack-AI-ADFlow-Suite-Project/feature/T1-23-foto-e-gruppi |
| `2026-10-09 11:32:43` | `0a70194` | blulime7 | `[DOCS]` | **Comune / Sistema** | docs: spunta T1-22 e T1-23 in tasks.md |
| `2026-10-09 11:32:35` | `22667ce` | blulime7 | `[CHORE]` | **Corsia 2 · Campagne & Foto** | chore: integra main in feature/T1-23-foto-e-gruppi |
| `2026-10-09 11:29:21` | `ab7a080` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge pull request #38 from Full-Stack-AI-ADFlow-Suite-Project/chore/python-multipart |
| `2026-10-09 11:29:16` | `f4c05e2` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge branch 'main' into chore/python-multipart |
| `2026-10-09 11:29:08` | `51f9b88` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge pull request #37 from Full-Stack-AI-ADFlow-Suite-Project/chore/ambiente-multipiattaforma |
| `2026-10-09 11:20:40` | `7ba2081` | blulime7 | `[CHORE]` | **Corsia 2 · Campagne & Foto** | chore: dichiara python-multipart per il caricamento delle foto |
| `2026-10-09 11:20:09` | `5607d9a` | blulime7 | `[DOCS]` | **Comune / Sistema** | docs: aggiorna la nota delle novità di T1-23 al limite per gruppo |
| `2026-10-09 11:18:59` | `5f47ba0` | blulime7 | `[TEST]` | **Corsia 2 · Campagne & Foto** | test: prova i 93 giorni e le 20 foto per gruppo (T1-22, T1-23) |
| `2026-10-09 11:18:38` | `f658ef4` | blulime7 | `[FIX]` | **Comune / Sistema** | fix: riporta le funzioni comuni di campagne a main e togli i residui (T1-22, T1-23) |
| `2026-10-09 10:56:12` | `391dd7c` | blulime7 | `[CHORE]` | **Comune / Sistema** | chore: lancia migrazioni, test e black a ogni PR con GitHub Actions |
| `2026-10-09 10:56:11` | `5e65681` | blulime7 | `[CHORE]` | **Comune / Sistema** | chore: fissa il fine riga LF per tutti con .gitattributes |
| `2026-10-09 10:56:10` | `f6d6e25` | blulime7 | `[DOCS]` | **Comune / Sistema** | docs: usa uv per avere gli stessi comandi su Windows, macOS e Linux |
| `2026-10-09 00:35:19` | `3f75616` | tresilvia83-wq | `[TEST]` | **Comune / Sistema** | test: debug approfondito ed edge case per T1-22 e T1-23 (261 test verdi) |
| `2026-10-09 00:17:25` | `67508ee` | tresilvia83-wq | `[FEAT]` | **Corsia 2 · Campagne & Foto** | feat: integra T1-22 e adatta gruppi, foto e stella ai contratti T1-08/T1-09 (T1-23) |
| `2026-10-08 23:28:07` | `29fab18` | tresilvia83-wq | `[TEST]` | **Comune / Sistema** | test: aggiorna suite test_api_bozza con canali, avvisi e filtri multi-stato (T1-22) |
| `2026-10-08 23:16:39` | `bdf5fce` | tresilvia83-wq | `[CHORE]` | **Comune / Sistema** | chore: integra main in feature/T1-22-api-bozza |
| `2026-10-08 21:17:55` | `39d6f70` | tresilvia83-wq | `[CHORE]` | **Corsia 2 · Campagne & Foto** | chore: integra main in feature/T1-23-foto-e-gruppi |
| `2026-10-08 18:01:52` | `cc434a5` | Nilton | `[MERGE]` | **Corsia 5 · Frontend & Interfaccia** | Merge pull request #36 from Full-Stack-AI-ADFlow-Suite-Project/feature/16-19-sicurezza-accesso |
| `2026-10-08 17:52:18` | `9d26046` | GiorgiTechAi | `[TEST]` | **Corsia 0 · Core, Coda & Architettura** | test: accetta localhost nei controlli del database locale |
| `2026-10-08 17:21:29` | `6b145a4` | GiorgiTechAi | `[TEST]` | **Comune / Sistema** | test: verifica i canali con autenticazione reale e aggiorna il riesame |
| `2026-10-08 17:17:18` | `48fd151` | GiorgiTechAi | `[CHORE]` | **Corsia 4 · Meta & Pubblicazione** | chore: riallinea la sicurezza a canali e pubblicazione integrati |
| `2026-10-08 17:12:30` | `0731a5f` | Nilton | `[MERGE]` | **Comune / Sistema** | Merge pull request #33 from Full-Stack-AI-ADFlow-Suite-Project/feature/T1-14-canali-collegati |
| `2026-10-08 17:11:58` | `b2a7ea2` | Nilton | `[MERGE]` | **Corsia 4 · Meta & Pubblicazione** | Merge pull request #35 from Full-Stack-AI-ADFlow-Suite-Project/feature/T1-43-pubblicazione |
| `2026-10-08 17:11:43` | `dac43f3` | GiorgiTechAi | `[DOCS]` | **Comune / Sistema** | docs: chiarisci lo stato della sicurezza su main |
| `2026-10-08 17:07:39` | `60bc0f7` | GiorgiTechAi | `[DOCS]` | **Comune / Sistema** | docs: aggiorna le dipendenze dopo il merge degli accessi |
| `2026-10-08 17:07:08` | `6b0c3eb` | GiorgiTechAi | `[CHORE]` | **Comune / Sistema** | chore: riallinea la sicurezza agli accessi integrati |
| `2026-10-08 17:07:07` | `a55aadc` | GiorgiTechAi | `[CHORE]` | **Corsia 5 · Frontend & Interfaccia** | chore: integra le prove di accesso sulle API di revisione |
| `2026-10-08 17:04:44` | `7da8e38` | GiorgiTechAi | `[CHORE]` | **Comune / Sistema** | chore: riallinea i canali ai permessi integrati |
| `2026-10-08 17:00:02` | `e108c66` | GiorgiTechAi | `[CHORE]` | **Comune / Sistema** | chore: riallinea i canali alle API di main |
| `2026-10-08 16:59:56` | `7a36d28` | GiorgiTechAi | `[TEST]` | **Corsia 1 · Accesso & Artigiani** | test: verifica le sessioni reali sulle API di revisione |
| `2026-10-08 16:57:44` | `812c2ad` | GiorgiTechAi | `[CHORE]` | **Corsia 1 · Accesso & Artigiani** | chore: riallinea utenti e sessioni alle API di main |
| `2026-10-08 16:57:43` | `b86ad53` | Nilton | `[MERGE]` | **Comune / Sistema** | Merge pull request #30 from Full-Stack-AI-ADFlow-Suite-Project/feature/T1-13-utenti-password |
| `2026-10-08 16:57:43` | `12293f6` | GiorgiTechAi | `[CHORE]` | **Comune / Sistema** | chore: riallinea la sicurezza alle API di main |
| `2026-10-08 16:48:03` | `d6bebbd` | Nilton | `[MERGE]` | **Corsia 1 · Accesso & Artigiani** | Merge pull request #31 from Full-Stack-AI-ADFlow-Suite-Project/feature/T1-12-permessi-sessioni |
| `2026-10-08 16:40:33` | `d0f8783` | NiL87AI | `[FEAT]` | **Comune / Sistema** | feat: pubblica_dovuti con tentativo idempotente e chiusura campagna (T1-43) |
| `2026-10-08 16:28:58` | `5d9a63a` | Nilton | `[MERGE]` | **Comune / Sistema** | Merge pull request #34 from Full-Stack-AI-ADFlow-Suite-Project/feature/T1-42-revisione |
| `2026-10-08 16:26:36` | `dc0782f` | NiL87AI | `[CHORE]` | **Comune / Sistema** | chore: merge di main in T1-42, risolto il conflitto in tasks.md |
| `2026-10-08 16:19:49` | `599f8e3` | GiorgiTechAi | `[DOCS]` | **Comune / Sistema** | docs: rifinisci la procedura di sicurezza |
| `2026-10-08 16:18:28` | `ef854dd` | GiorgiTechAi | `[FIX]` | **Corsia 5 · Frontend & Interfaccia** | fix: riallinea la sicurezza al nuovo accesso e alla migrazione 009 |
| `2026-10-08 16:18:03` | `2d0b960` | Nilton | `[MERGE]` | **Corsia 4 · Meta & Pubblicazione** | Merge pull request #32 from Full-Stack-AI-ADFlow-Suite-Project/feature/T1-41-adattatore-social |
| `2026-10-08 16:11:33` | `960a55e` | NiL87AI | `[FEAT]` | **Comune / Sistema** | feat: vedi campagna, approva e prosegui per l'operatore (T1-42) |
| `2026-10-08 16:03:58` | `86c59d5` | GiorgiTechAi | `[CHORE]` | **Comune / Sistema** | chore: integra T1-13 e risolvi i conflitti di T1-12 |
| `2026-10-08 16:02:08` | `104d05e` | GiorgiTechAi | `[FEAT]` | **Comune / Sistema** | feat: mostra i canali collegati in T1-14 |
| `2026-10-08 15:53:06` | `96e43da` | NiL87AI | `[FEAT]` | **Corsia 2 · Campagne & Foto** | feat: adattatore social simulato con pubblica() multi-foto (T1-41) |
| `2026-10-08 15:52:40` | `08b1afe` | GiorgiTechAi | `[FEAT]` | **Corsia 1 · Accesso & Artigiani** | feat: verifica permessi e rinnova le sessioni in T1-12 |
| `2026-10-08 15:41:49` | `06991b1` | GiorgiTechAi | `[MERGE]` | **Comune / Sistema** | Merge remote-tracking branch 'origin/main' into feature/T1-13-utenti-password |
| `2026-10-08 15:39:09` | `cc9b417` | Nilton | `[MERGE]` | **Corsia 1 · Accesso & Artigiani** | Merge pull request #28 from Full-Stack-AI-ADFlow-Suite-Project/feature/T1-11-login-sessioni |
| `2026-10-08 15:31:18` | `3506cca` | Nilton | `[MERGE]` | **Comune / Sistema** | Merge pull request #29 from Full-Stack-AI-ADFlow-Suite-Project/chore/pulizia-file-locali |
| `2026-10-08 15:30:40` | `e68ab22` | Nilton | `[MERGE]` | **Comune / Sistema** | Merge pull request #27 from Full-Stack-AI-ADFlow-Suite-Project/docs/spunta-t1-08 |
| `2026-10-08 15:28:54` | `848666a` | Nilton | `[MERGE]` | **Corsia 2 · Campagne & Foto** | Merge pull request #15 from Full-Stack-AI-ADFlow-Suite-Project/feature/T1-21-adattatore-archivio |
| `2026-10-08 15:27:11` | `4e83882` | NiL87AI | `[CHORE]` | **Comune / Sistema** | chore: merge di main in T1-21, risolto il conflitto in tasks.md |
| `2026-10-08 15:24:47` | `079fcad` | NiL87AI | `[DOCS]` | **Corsia 2 · Campagne & Foto** | docs: spunta T1-21, adattatore archivio pronto alla revisione |
| `2026-10-08 15:23:26` | `e5acffa` | GiorgiTechAi | `[TEST]` | **Corsia 1 · Accesso & Artigiani** | test: verifica cambio password con login e CLI concorrenti |
| `2026-10-08 15:19:15` | `3318691` | GiorgiTechAi | `[FEAT]` | **Corsia 1 · Accesso & Artigiani** | feat: crea utenti e cambia password con revoca delle sessioni |
| `2026-10-08 15:14:08` | `07b2c05` | GiorgiTechAi | `[FIX]` | **Corsia 1 · Accesso & Artigiani** | fix: serializza il login con il cambio della password |
| `2026-10-08 15:12:22` | `ce73e24` | NiL87AI | `[CHORE]` | **Comune / Sistema** | chore: aggiungi il README del backend e ignora i file locali |
| `2026-10-08 15:11:06` | `ba980db` | GiorgiTechAi | `[FEAT]` | **Corsia 1 · Accesso & Artigiani** | feat: riallinea login e sessioni per ruolo in T1-11 |
| `2026-10-08 15:08:53` | `4a4599f` | NiL87AI | `[DOCS]` | **Comune / Sistema** | docs: spunta T1-08, unito con la PR #25 |
| `2026-10-08 15:05:03` | `d34c97d` | Nilton | `[MERGE]` | **Corsia 0 · Core, Coda & Architettura** | Merge pull request #26 from Full-Stack-AI-ADFlow-Suite-Project/feature/T1-09-stati-contratti |
| `2026-10-08 14:34:13` | `1d3dbf6` | GiorgiTechAi | `[REFACTOR]` | **Corsia 2 · Campagne & Foto** | refactor: chiarisci proporzioni e legami delle foto in T1-09 |
| `2026-10-08 09:52:27` | `a83fc91` | GiorgiTechAi | `[FEAT]` | **Comune / Sistema** | feat: completa le schede dei canali per T1-09 |
| `2026-10-08 09:27:02` | `26038e1` | GiorgiTechAi | `[FIX]` | **Comune / Sistema** | fix: nascondi i valori negli errori di configurazione |

---

## 🚀 Sprint 1 · Fondamenta Modulari, Tabelle PostgreSQL e Contratti (1–7 Ottobre 2026)

Totale modifiche registrate nella fase: **56**

| Data e Ora | Commit | Autore | Tipo | Corsia / Modulo | Descrizione Dettagliata della Modifica |
|---|:---:|---|:---:|---|---|
| `2026-10-07 20:33:58` | `331bc4f` | GiorgiTechAi | `[FEAT]` | **Corsia 0 · Core, Coda & Architettura** | feat: riallinea stati e contratti di T1-09 |
| `2026-10-07 20:11:17` | `47e9d68` | Nilton | `[MERGE]` | **Corsia 0 · Core, Coda & Architettura** | Merge pull request #25 from Full-Stack-AI-ADFlow-Suite-Project/feature/T1-08-riallineamento-tabelle |
| `2026-10-07 19:34:33` | `aaac983` | NiL87AI | `[FIX]` | **Corsia 2 · Campagne & Foto** | fix: indicizza gruppo_foto.campagna_id come le altre chiavi esterne |
| `2026-10-07 19:10:41` | `e6f7a38` | NiL87AI | `[FIX]` | **Corsia 0 · Core, Coda & Architettura** | fix: fai girare il test della coda su Windows |
| `2026-10-07 19:03:04` | `5290ca9` | NiL87AI | `[FEAT]` | **Corsia 0 · Core, Coda & Architettura** | feat: riallinea le tabelle dello sprint 1 (T1-08) |
| `2026-10-07 17:49:24` | `18295df` | Nilton | `[MERGE]` | **Comune / Sistema** | Merge pull request #22 from Full-Stack-AI-ADFlow-Suite-Project/docs/riordino-appunti |
| `2026-10-07 17:30:31` | `0c86e9b` | tresilvia83-wq | `[FEAT]` | **Corsia 2 · Campagne & Foto** | feat: introduce tetto massimo di 20 foto per campagna e documenta domande corsia 0 (T1-23) |
| `2026-10-07 17:09:27` | `9e58b63` | blulime7 | `[DOCS]` | **Comune / Sistema** | docs: assorbi nel canale agenti le decisioni 89–112 |
| `2026-10-07 17:09:27` | `625c83e` | blulime7 | `[DOCS]` | **Comune / Sistema** | docs: chiudi le domande delle pagine statiche e riordina gli appunti |
| `2026-10-07 16:43:55` | `78fd9da` | tresilvia83-wq | `[FIX]` | **Corsia 2 · Campagne & Foto** | fix: cancella e compensa i file foto solo a esito reale della transazione (T1-23) |
| `2026-10-07 16:29:22` | `df4710b` | tresilvia83-wq | `[TEST]` | **Comune / Sistema** | test: espande suite di debug con parser webp, anti-spoofing e concorrenza multi-thread (T1-23) |
| `2026-10-07 16:04:53` | `615a91f` | tresilvia83-wq | `[TEST]` | **Corsia 2 · Campagne & Foto** | test: aggiunge suite di debug e stress test su immagini e gruppi (T1-23) |
| `2026-10-07 15:41:49` | `93857b9` | tresilvia83-wq | `[FEAT]` | **Corsia 2 · Campagne & Foto** | feat: implementa caricamento foto, gestione gruppi e file per campagne in bozza (T1-23) |
| `2026-10-07 13:42:31` | `d19f5ed` | tresilvia83-wq | `[FEAT]` | **Comune / Sistema** | feat: implementa API bozza, elenco e dettaglio campagne (T1-22) |
| `2026-10-07 12:44:53` | `c86a24a` | GiorgiTechAi | `[FEAT]` | **Corsia 5 · Frontend & Interfaccia** | feat: proteggi accesso con limiti condivisi e log sicuri |
| `2026-10-07 12:13:46` | `cca1ab5` | GiorgiTechAi | `[DOCS]` | **Comune / Sistema** | docs: prepara la revisione di T1-11 T1-12 e T1-13 |
| `2026-10-07 11:56:24` | `a3b7700` | tresilvia83-wq | `[FIX]` | **Corsia 2 · Campagne & Foto** | fix: propaga PermissionError in elimina dell'adattatore archivio (T1-21) |
| `2026-10-07 11:15:52` | `9d3155a` | tresilvia83-wq | `[FIX]` | **Comune / Sistema** | fix: aggiungi limite payload, verifica magic bytes e risolvi toctou (T1-21) |
| `2026-10-07 10:47:51` | `2121bbf` | GiorgiTechAi | `[FIX]` | **Corsia 1 · Accesso & Artigiani** | fix: rifiuta identita ambigue e verifica auth via HTTP reale |
| `2026-10-07 10:37:02` | `0cb89b7` | GiorgiTechAi | `[FIX]` | **Corsia 1 · Accesso & Artigiani** | fix: proteggi gli errori auth e verifica transazioni e concorrenza |
| `2026-10-07 10:25:38` | `edd0d96` | GiorgiTechAi | `[FEAT]` | **Comune / Sistema** | feat: crea utenti con email unica e scrypt per T1-13 |
| `2026-10-07 10:22:57` | `93dff7f` | GiorgiTechAi | `[FEAT]` | **Comune / Sistema** | feat: autentica le richieste e verifica i permessi per T1-12 |
| `2026-10-07 10:20:45` | `a2f0f27` | GiorgiTechAi | `[FEAT]` | **Corsia 1 · Accesso & Artigiani** | feat: implementa login e sessioni per T1-11 |
| `2026-10-07 09:02:36` | `3be9769` | tresilvia83-wq | `[FEAT]` | **Corsia 2 · Campagne & Foto** | feat: implementa adattatore archivio foto reale e finto con test (T1-21) |
| `2026-10-03 11:35:58` | `3a44053` | blulime7 | `[MERGE]` | **Corsia 0 · Core, Coda & Architettura** | Merge pull request #14 from Full-Stack-AI-ADFlow-Suite-Project/feature/T1-05-fix-coda-e-worker |
| `2026-10-03 11:14:03` | `a1f28b0` | blulime7 | `[DOCS]` | **Comune / Sistema** | docs: aggiungi la nota delle novità di T1-05 e spunta il task |
| `2026-10-03 11:14:03` | `338037e` | blulime7 | `[FIX]` | **Corsia 0 · Core, Coda & Architettura** | fix: fai partire la coda e il worker di T1-05 |
| `2026-10-03 10:29:36` | `c83b406` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge pull request #12 from Full-Stack-AI-ADFlow-Suite-Project/feature/T1-04-stati-e-letture |
| `2026-10-02 20:03:45` | `3f88f64` | blulime7 | `[FIX]` | **Comune / Sistema** | fix: rifiuta gli hash con parametri fuori misura, togli la copia dei ruoli dalla CLI |
| `2026-10-02 19:57:44` | `81c6cab` | blulime7 | `[FEAT]` | **Corsia 1 · Accesso & Artigiani** | feat: aggiungi seed, scrypt e token, fixture utente_di_prova (T1-06) |
| `2026-10-02 19:37:53` | `8064076` | blulime7 | `[DOCS]` | **Comune / Sistema** | docs: allinea plan, spec e tasks a T1-04 e alle correzioni |
| `2026-10-02 19:37:53` | `d858714` | blulime7 | `[CHORE]` | **Comune / Sistema** | chore: allinea docstring e segnaposto delle fabbriche a T1-04 |
| `2026-10-02 19:37:53` | `624e97c` | blulime7 | `[FIX]` | **Corsia 4 · Meta & Pubblicazione** | fix: esegui il test del tick senza plugin async |
| `2026-10-02 19:36:25` | `ceb5f4e` | blulime7 | `[MERGE]` | **Comune / Sistema** | Merge remote-tracking branch 'origin/main' into feature/T1-04-stati-e-letture |
| `2026-10-02 19:19:06` | `f5a2d31` | blulime7 | `[DOCS]` | **Comune / Sistema** | docs: aggiungi la nota delle novità di T1-04 e spunta il task |
| `2026-10-02 19:19:06` | `e7bf42b` | blulime7 | `[TEST]` | **Comune / Sistema** | test: prova ogni transizione e ogni funzione di T1-04, completa le fabbriche |
| `2026-10-02 19:19:06` | `4888e7d` | blulime7 | `[FEAT]` | **Comune / Sistema** | feat: aggiungi stati, transizioni e letture comuni (T1-04) |
| `2026-10-02 19:15:29` | `e4c9acb` | blulime7 | `[FIX]` | **Comune / Sistema** | fix: completa lo schema di T1-03 (indici, tentativo unico, campi AI facoltativi) |
| `2026-10-02 19:14:48` | `08c73c2` | blulime7 | `[FIX]` | **Corsia 1 · Accesso & Artigiani** | fix: correggi i contratti di T1-02 (tipi, db semplice, richiede_ruolo) |
| `2026-10-02 19:14:48` | `1c4a17f` | blulime7 | `[FIX]` | **Corsia 0 · Core, Coda & Architettura** | fix: fissa il fuso UTC sulla connessione al database |
| `2026-10-02 17:03:03` | `76a3861` | Nilton | `[MERGE]` | **Corsia 0 · Core, Coda & Architettura** | Merge pull request #10 from Full-Stack-AI-ADFlow-Suite-Project/feature/T1-05-coda-e-worker |
| `2026-10-02 16:48:54` | `32accd4` | NiL87AI | `[FIX]` | **Comune / Sistema** | fix: integra T1-05 con main |
| `2026-10-02 16:15:58` | `3cd9499` | Nilton | `[MERGE]` | **Corsia 0 · Core, Coda & Architettura** | Merge pull request #9 from Full-Stack-AI-ADFlow-Suite-Project/feature/T1-02-contratti |
| `2026-10-02 16:08:37` | `d0cd595` | GiorgiTechAi | `[MERGE]` | **Corsia 0 · Core, Coda & Architettura** | Merge pull request #8 from Full-Stack-AI-ADFlow-Suite-Project/feature/T1-03-tabelle |
| `2026-10-02 15:49:02` | `510df4a` | tresilvia83-wq | `[FEAT]` | **Corsia 0 · Core, Coda & Architettura** | feat: aggiungi firme dei contratti e core/coda.py (T1-02) |
| `2026-10-02 15:28:53` | `a5628e1` | NiL87AI | `[FEAT]` | **Corsia 0 · Core, Coda & Architettura** | feat: implementa T1-05 coda e worker |
| `2026-10-02 15:04:54` | `6ffe1ee` | GiorgiTechAi | `[FEAT]` | **Corsia 0 · Core, Coda & Architettura** | feat: crea le tabelle e le migrazioni dello sprint 1 (T1-03) |
| `2026-10-02 14:21:56` | `42a4274` | Nilton | `[MERGE]` | **Comune / Sistema** | Merge pull request #7 from Full-Stack-AI-ADFlow-Suite-Project/feature/T1-01-struttura |
| `2026-10-02 14:15:40` | `161977a` | blulime7 | `[DOCS]` | **Comune / Sistema** | docs: allinea il canale agenti alla base comune e aggiunge la nota delle novità |
| `2026-10-02 14:15:40` | `3b0d222` | blulime7 | `[FEAT]` | **Comune / Sistema** | feat: crea la struttura del backend (T1-01) |
| `2026-10-01 16:55:00` | `fae4535` | NiL87AI | `[MERGE]` | **Corsia 0 · Core, Coda & Architettura** | Merge: risolto conflitto README, unendo reset docs (ADR-51) e istruzioni backend modulare |
| `2026-10-01 16:31:40` | `316fbdc` | NiL87AI | `[DOCS]` | **Corsia 0 · Core, Coda & Architettura** | docs: corregge comando uvicorn e aggiunge step migrazione alembic nel README |
| `2026-10-01 13:31:22` | `e8088fc` | NiL87AI | `[FEAT]` | **Corsia 0 · Core, Coda & Architettura** | feat: struttura backend modulare, fix config pydantic e migrazione alembic |
| `2026-10-01 13:26:37` | `3196baf` | Nilton | `[MERGE]` | **Comune / Sistema** | Merge pull request #6 from Full-Stack-AI-ADFlow-Suite-Project/feature/reset-documentazione-v5 |
| `2026-10-01 13:07:30` | `fc623c8` | blulime7 | `[CHORE]` | **Corsia 5 · Frontend & Interfaccia** | chore: cancella l'impalcatura iniziale di backend e frontend (ADR-51) |
| `2026-10-01 13:07:30` | `8d824e9` | blulime7 | `[DOCS]` | **Corsia 2 · Campagne & Foto** | docs: reset v5.0 della documentazione (pagine Profilo e Campagna, immagini AI, moduli, sei corsie) |

---

## 🚀 Setup Iniziale, Architettura e Reset Documentale (25–30 Settembre 2026)

Totale modifiche registrate nella fase: **14**

| Data e Ora | Commit | Autore | Tipo | Corsia / Modulo | Descrizione Dettagliata della Modifica |
|---|:---:|---|:---:|---|---|
| `2026-09-30 17:08:47` | `2245185` | Nilton | `[MERGE]` | **Comune / Sistema** | Merge pull request #3 from Full-Stack-AI-ADFlow-Suite-Project/feature/revisione-esiti-campagna |
| `2026-09-30 17:01:17` | `8a62d70` | blulime7 | `[DOCS]` | **Comune / Sistema** | docs: revisione finale dei due canali |
| `2026-09-30 16:57:24` | `f2d5f13` | blulime7 | `[DOCS]` | **Comune / Sistema** | docs: rinomina il canale umano in appunti, note e lavori aperti |
| `2026-09-30 16:32:45` | `339edda` | blulime7 | `[DOCS]` | **Corsia 0 · Core, Coda & Architettura** | docs: divide la documentazione in canale umano e canale agenti (ADR-46) |
| `2026-09-30 13:51:36` | `2d67979` | blulime7 | `[DOCS]` | **Comune / Sistema** | docs: decisioni sui task (A-01 in parallelo allo sprint 1, sprint senza date) |
| `2026-09-30 13:47:17` | `7e400ae` | blulime7 | `[DOCS]` | **Corsia 0 · Core, Coda & Architettura** | docs: riorganizza la documentazione in constitution, spec, plan, tasks e converge (ADR-45) |
| `2026-09-30 13:10:14` | `f9780a5` | blulime7 | `[DOCS]` | **Corsia 2 · Campagne & Foto** | docs: diagrammi e pagine statiche per motivi del No e ritocco foto (v4.7) |
| `2026-09-30 13:05:11` | `cac4073` | blulime7 | `[DOCS]` | **Corsia 0 · Core, Coda & Architettura** | docs: motivi del No e cicli di revisione (ADR-40…44, flusso v4.7) |
| `2026-09-30 13:01:19` | `a67080f` | blulime7 | `[DOCS]` | **Comune / Sistema** | docs: collega la documentazione nel README e ne corregge la codifica |
| `2026-09-30 12:02:00` | `ca8410a` | Nilton | `[MERGE]` | **Comune / Sistema** | Merge pull request #2 from Full-Stack-AI-ADFlow-Suite-Project/feature/documentazione |
| `2026-09-30 10:37:39` | `d4009af` | blulime7 | `[DOCS]` | **Corsia 0 · Core, Coda & Architettura** | docs: aggiunge documentazione tecnica del progetto (ADR, SPEC-CODICE, architettura v4.6) |
| `2026-09-28 16:55:46` | `b7ce136` | Nilton | `[MERGE]` | **Comune / Sistema** | Merge pull request #1 from Full-Stack-AI-ADFlow-Suite-Project/initial-setup |
| `2026-09-28 16:50:17` | `9822571` | NiL87AI | `[CHORE]` | **Comune / Sistema** | chore: setup iniziale struttura progetto, env example e linee guida per il team |
| `2026-09-25 16:04:13` | `67cc528` | Nilton | `[CHORE]` | **Comune / Sistema** | Initial commit |

---
