# Sintesi della simulazione di accettazione (T4-108)

> Il piano della simulazione (`accettazione-post-mvp.md`), il brief della corsia 10 e i report `T4-1xx-*` citati qui sono archiviati in `docs/archivio/accettazione/` e `docs/archivio/brief/` (ADR-122). Questa pagina e il registro `rilievi.md` restano il riferimento sullo stato della qualità.

La simulazione ha prodotto **44 rilievi** (RL-001…RL-044), classificati:
**27 correggere**, **7 proposta**, **7 roadmap**, **3 limite MVP**. Un solo
**blocco assoluto** è confermato.

## 1. Blocchi assoluti

| Blocco di §8 | Esito | Rilievo |
|---|---|---|
| Un artigiano vede o modifica i dati di un altro | **smentito**: matrice 57 × 5 e test BOLA verdi | RL-020 |
| Un post viene pubblicato senza approvazione | **smentito**: invarianti §1.1 e §1.6 verdi | — |
| **Lo stesso post viene pubblicato due volte su Meta** | **CONFERMATO**: con un processo morto dopo la risposta di Meta e prima del commit, il tick successivo ripubblica (2 chiamate al social; D-07) | **RL-025** |
| Un segreto valido è nella storia di git | **smentito**: solo falsi positivi su PNG d'archivio | RL-007 |
| La foto originale viene modificata o persa | **smentito**: hash identico dopo sistemazione, cambio foto e pubblicazione | — |
| Dati personali o token nei log | **smentito**: prova con valori riconoscibili, solo un artefatto di `httpx` nei test | — |

**Il blocco è uno: RL-025.** Non è un errore nel percorso normale (due worker
sani non raddoppiano, indice unico `ok` alla mano): è il caso D-07, il più
insidioso, quello che in produzione capita quando il database o il processo
cade nel momento peggiore. Va corretto prima della produzione, non dell'MVP.

## 2. I criteri di §8, uno per uno

### Prodotto

| Casella | Esito | Perché |
|---|---|---|
| Ogni CA del perimetro tracciato e verde | **soddisfatto** | 95/96 CA hanno un test col nome del contratto (CA-83 ce l'ha senza il nome, RL-010); la suite intera è verde (T4-101) |
| Gli 11 invarianti con test che provano a violarli | **soddisfatto** (ma 3 violazioni trovate) | un test per invariante (T4-104); §1.7 (RL-025), §1.9 in parallelo (RL-023) e §1.1 in parallelo (RL-021) falliscono |
| Test con stato senza controesempi | **non provato** | 300 sequenze per macchina senza controesempi; le 10 000 richieste non sono state completate (limite di tempo e di lock del database) |
| Demo da database vuoto automatica | **non soddisfatto** | l'E2E copre accesso, viste e navigazione; i passi con foto e caricamenti mancano (RL-036) |

### Sicurezza

| Casella | Esito | Perché |
|---|---|---|
| Matrice dei permessi esaustiva | **soddisfatto** | 57 operazioni × 5 ruoli conformi (T4-102) |
| Dipendenze, analisi statica, segreti e ZAP senza risultati alti | **non soddisfatto** | pillow: 39 vulnerabilità, 3 critiche (RL-004); ZAP non eseguito |
| Header di sicurezza e controllo di Origin | **non soddisfatto** | mancano le intestazioni (RL-015); il controllo di Origin c'è in produzione (RL-016 smentito) |
| Issue #17 verificata su un proxy di staging | **non soddisfatto** | la issue resta aperta per lo staging (RL-033) |
| Checklist ASVS 5.0 L2 compilata | **soddisfatto** | `T4-107-asvs-l2.md`, ogni requisito con prova o rilievo |
| Lacune GDPR e AI Act elencate, con una proposta | **soddisfatto** | RL-040…RL-044 |

### Affidabilità

| Casella | Esito | Perché |
|---|---|---|
| Obiettivi di servizio rispettati | **non provato** | solo uno smoke di 30 secondi: p95 ≤ 110 ms, ma nessuna prova di volume (RL-031) |
| Prova di durata senza perdite | **non provato** | nessuna prova di 2–8 ore |
| Scenari di concorrenza e guasto con l'esito atteso | **non soddisfatto** | 4 scenari su 13 hanno un esito diverso dall'atteso (RL-021…RL-024); guasti: DB e disco → 500 (RL-028/029) |
| Backup e ripristino di database e foto provati | **soddisfatto** | dump 0,3 s, 228 foto copiate, restore 0,5 s, conteggi identici (T4-105) |
| Misure e allarmi su sicurezza, coda e spesa AI | **non soddisfatto** | il costo AI si vede (storico); mancano latenza aggregata, coda e allarmi (RL-031) |

### Processo

| Casella | Esito | Perché |
|---|---|---|
| Dipendenze bloccate; runtime e test separati | **non soddisfatto** | nessun lockfile, runtime e test nello stesso file, `httpx` non dichiarato (RL-001/002/006) |
| Rilascio riproducibile e rollback descritti | **non soddisfatto** | nessun artefatto di rilascio (RL-032) |
| Documentazione seguita da chi non l'ha scritta | **soddisfatto con tre rilievi bassi** | la ricostruzione da zero arriva a 2000 test verdi; mancano `createdb`, il vincolo su `adflow_test` e la cartella foto della demo (RL-012/013/014) |

## 3. I limiti dell'MVP, in parole semplici per il cliente

- **La demo funziona e il percorso si regge**, con i permessi al posto giusto:
  nessun artigiano vede i dati di un altro e nessun post esce senza
  approvazione.
- **Per andare in produzione mancano quattro mestieri**, non quattro righe di
  codice: le intestazioni di sicurezza (e HTTPS con HSTS), un rilascio
  riproducibile con rollback, uno staging vero per provare il proxy, e
  misure/allarmi per accorgersi dei guasti. Sono i rilievi RL-015, RL-032,
  RL-033 e RL-031.
- **Ci sono tre corse** che oggi possono produrre due approvazioni, due
  versioni con la stessa foto sullo stesso canale, o due interventi AI
  insieme: RL-021, RL-022, RL-023, RL-024. Non capita tutti i giorni (servono
  due operatori nello stesso istante), ma capita appena il prodotto cresce.
- **La pubblicazione non è blindata contro un crash**: se il processo muore
  tra la risposta di Meta e il salvataggio, il post può uscire due volte
  (RL-025). È il difetto più serio trovato.
- **Le immagini AI, oggi, non escono**: il modello configurato consuma la
  chiamata e non restituisce l'immagine (RL-037). Se la demo ha una campagna
  con foto mancanti, va sistemato il modello prima del 6/11.
- **Le foto stanno su un disco locale**: il backup è due cose (database e
  cartella), due istanze non condividono i file (RL-034). Per la produzione
  serve uno storage condiviso.
- **Privacy e AI Act sono un lavoro da fare con chi firma**: registro dei
  trattamenti, accordi con i fornitori, valutazione d'impatto e una procedura
  per le richieste di cancellazione che conviva con «niente si cancella»
  (RL-040…RL-044).
- **La demo del pitch dipende da una cartella di foto che non è in git**
  (RL-014): se quella cartella si perde, il percorso della demo non si
  ricostruisce da un clone.

## 4. Task di correzione proposti (in ordine di gravità)

Ogni task è indipendente, ha il suo rilievo e il test che oggi lo documenta
(`xfail(strict=True)` che diventa verde quando si corregge).

| # | Task | Rilievi | Test che lo chiude | Gravità |
|---|---|---|---|---|
| C1 | **Pubblicazione idempotente**: commit del tentativo prima della chiamata al social, ripresa dal tentativo `in_corso` | RL-025 | `invarianti/test_07_pubblicazione_idempotente.py` | Alta (blocco assoluto) |
| C2 | **Approvazione e respinta atomiche**: blocco della riga o `UPDATE … WHERE stato = 'in_revisione'` con 409 | RL-021, RL-022 | `concorrenza/test_approvazione.py`, `concorrenza/test_interventi.py` | Alta |
| C3 | **Una foto una volta anche in parallelo**: blocco della foto o vincolo sulle versioni correnti per canale | RL-023 | `concorrenza/test_interventi.py` | Alta |
| C4 | **Dipendenze**: pillow 13, `httpx` dichiarato, lockfile, runtime e test separati | RL-001, RL-002, RL-004, RL-005, RL-006 | `scansioni` (pip-audit a zero alte) | Alta |
| C5 | **Intestazioni di sicurezza** (app e proxy) e limiti degli id, 422 coerente | RL-015, RL-026, RL-027 | `test_intestazioni.py`, `test_input_estremi.py` | Alta |
| C6 | **Rilascio e staging**: container, compose, proxy, rollback; chiusura issue #17 | RL-032, RL-033 | prova su staging (non un test) | Alta |
| C7 | **Modello di immagini AI**: scegliere un modello che restituisca l'immagine e rifare la prova | RL-037 | `T4-107-ai-vera.md` rifatto | Media |
| C8 | **Guasti ordinati**: 503 con database giù, errore chiaro con disco pieno | RL-028, RL-029 | `guasti/test_database_giu.py`, `guasti/test_disco_pieno.py` | Media |
| C9 | **Osservabilità e carico**: misure, allarmi, e le prove di §7.2 | RL-031 | report di carico completo | Media |
| C10 | **Interventi AI atomici** (R-31/R-04) | RL-024 | `concorrenza/test_interventi.py` | Media |
| C11 | **Frontend**: contrasto e link (RL-035), vitest e percorso E2E completo (RL-036) | RL-035, RL-036 | `frontend/e2e`, `test_intestazioni` no — prova axe e vitest | Media |
| C12 | **Privacy e AI Act**: registro, DPA, DPIA, anonimizzazione, metadati AI; conservazione dello storico AI | RL-019, RL-040…RL-044 | documenti e una procedura | Media |
| C13 | **CI**: audit, segreti, mypy, copertura, E2E (in un workflow non bloccante prima) | RL-003, RL-008, RL-030 | workflow | Media |
| C14 | **Segreti separati** (login vs indirizzi pubblici) | RL-038 | `T4-107-log-segreti.md` | Bassa |
| C15 | **Documentazione**: `createdb`, vincolo `adflow_test`, cartella foto della demo, nomi dei test CA, collegamento R→CA | RL-012, RL-013, RL-014, RL-010, RL-011 | ricostruzione rifatta | Bassa |
| C16 | **Roadmap**: storage delle foto condiviso, cifratura dei token social, rotte congelate | RL-017, RL-034, RL-039 | roadmap | Bassa |

## 5. Che cosa è andato bene (da non perdere)

- **Matrice dei permessi**: tutte e 57 le operazioni conformi alla
  costituzione, BOLA assente su tutta la superficie.
- **Invarianti**: nove su undici reggono agli attacchi, anche con testi ostili
  (prompt injection) e upload ostili.
- **Pubblicazione nel percorso normale**: due worker non raddoppiano (indice
  unico e tentativo riusato); il post esce una volta.
- **Backup e ripristino**: semplici e verificati, con i conteggi uguali.
- **Il costo AI è trasparente**: 5 centesimi per una campagna di prova, letto
  dallo storico, con i token per chiamata.
- **La ricostruzione da zero funziona**: un clone pulito arriva a 2000 test
  verdi e all'app avviata seguendo i README, con tre passi non scritti.

## 6. Che cosa la simulazione insegna sul metodo

- **I difetti veri stanno nelle corse e nei guasti**, non nei percorsi scritti
  a mano: T4-103 e T4-104 hanno trovato i rilievi più gravi.
- **Il fuzzing dallo schema costa poco e trova molto**: schemathesis ha
  trovato da sola i 500 degli input estremi e il contratto degli errori.
- **Le prove con barriera devono essere ripetute**: 49/50 non è 0/50; la
  percentuale va scritta nel rilievo.
- **I test di accettazione possono vivere nel repository** senza toccare
  l'app: `xfail(strict=True)` tiene la suite verde e il difetto alla luce.
- **Le scelte fatte con l'AI vera** (una campagna, 5 centesimi) bastano a
  trovare il problema del modello di immagini: la prova a mano ha un valore
  che le prove finte non hanno.
