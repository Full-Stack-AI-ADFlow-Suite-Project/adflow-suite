# T4-107 · Dati personali e AI Act

Analisi delle lacune (§5.1 e §5.5): **non** è una consulenza legale e non
sostituisce il titolare del trattamento né un consulente privacy (D-03, D-04:
Giovanni per la simulazione, nessun budget esterno). Ogni lacuna è un rilievo
con la proposta.

## 1. Registro dei trattamenti (GDPR art. 30)

**Che cosa l'app tratta:**

| Dato | Dove | Perché | Per quanto |
|---|---|---|---|
| email, nome, ruolo, password (hash scrypt) | `utente` | accesso e ruoli | finché l'account esiste |
| profilo bottega (referente, città, clienti ideali, vincoli) | `profilo_bottega` + **snapshot** di ogni campagna | generazione dei contenuti | le campagne restano (nessuna cancellazione) |
| foto e immagini AI | disco + `foto` | il prodotto | le foto restano (R-47) |
| testi generati, decisioni, approvazioni | `versione_post`, `decisione_campagna`, `approvazione` | revisione e storico | restano (costituzione §1.2) |
| **prompt e risposte dell'AI** | `chiamata_ai` (migrazione 013) | storico, voto, costo | **senza regola: cresce per sempre (RL-019)** |
| eventi di sicurezza (senza dati personali) | log JSONL | sicurezza | rotazione dei log non definita |
| id esterni Meta e costo | `pubblicazione`, `chiamata_ai` | pubblicazione e conti | restano |

**Lacuna:** non esiste un registro dei trattamenti scritto (né in `docs/` né
nel prodotto): RL-040. **Proposta:** un documento di una pagina con la tabella
qui sopra, tempi di conservazione inclusi, approvato dal titolare.

## 2. Diritto alla cancellazione (art. 17) contro «niente si cancella»

La costituzione §1.2 impone che foto, versioni, decisioni e campagne restino.
Non è compatibile, così com'è, con una richiesta di cancellazione dei dati
personali. **Proposta (RL-041, D-05):** anonimizzare, non cancellare — sostituire
i dati personali (nome, email, referente, testi) con valori neutri conservando
la struttura storica; un comando amministrativo con traccia. Da decidere prima
di aprire il prodotto a clienti veri.

## 3. Fornitori e trasferimenti (artt. 28 e capo V)

Fornitori che ricevono dati: **OpenAI/OpenRouter** (profilo, testi, foto per
l'analisi) e **Meta** (testi e foto alla pubblicazione).

**Lacune:** nessun DPA firmato (art. 28), nessuna verifica dei trasferimenti
fuori dall'UE (capo V), nessuna informativa al cliente finale (RL-042).
**Proposta:** DPA con i due fornitori, valutazione dei trasferimenti
(clausole standard), informativa breve da mostrare all'artigiano al primo
accesso.

## 4. DPIA (art. 35)

Dati di persone riconoscibili **nelle foto** (artigiani, clienti delle botteghe)
trattati con AI generativa e conservati senza cancellazione: è un trattamento
che può richiedere una DPIA. **Proposta (RL-043):** valutazione d'impatto
semplificata prima della produzione, con la dichiarazione delle foto (R-41) che
resta la base del consenso dell'artigiano per le persone ritratte.

## 5. AI Act, art. 50 (in vigore dal 2/8/2026)

- **Immagini AI:** il post porta «Immagine creata con AI» (R-43) ✓. L'articolo
  50 chiede che il contenuto generato sia **riconoscibile come tale**: la
  dicitura nel testo soddisfa la trasparenza verso il pubblico; non c'è
  un'etichetta nei **metadati** dell'immagine (proposta in RL-044: un campo
  XMP/EXIF «AI-generated» nella foto creata, così la dicitura sopravvive al
  download).
- **Testi:** generati dall'AI e approvati da una persona: la revisione umana
  (R-14) rende l'operatore responsabile del contenuto; resta la trasparenza
  verso l'artigiano (sa che l'AI scrive: è nel prodotto).
- **Classificazione:** non è un sistema vietato né ad alto rischio (non decide
  su persone, non è infrastruttura critica): gli obblighi di trasparenza
  dell'art. 50 sono la parte applicabile.
- **Lacuna:** nessuna dichiarazione scritta di classificazione AI Act
  (RL-044), nessuna menzione nella proposta al cliente.

## 6. Dati nei log e segreti

Vedi `T4-107-log-segreti.md`: **nessun dato personale o token nei log
dell'applicazione** (prova con valori riconoscibili). Lo storico AI, invece,
conserva i dati della bottega: è coperto da RL-019.

## 7. Rilievi di questo report

| ID | Rilievo | Gravità | Classe proposta |
|---|---|---|---|
| RL-040 | Nessun registro dei trattamenti scritto (art. 30) | Media | correggere/roadmap |
| RL-041 | «Niente si cancella» senza procedura di anonimizzazione (art. 17, D-05) | Media | roadmap |
| RL-042 | Nessun DPA, verifica dei trasferimenti o informativa (artt. 28, capo V) | Media | roadmap |
| RL-043 | DPIA non valutata per foto di persone + AI generativa (art. 35) | Media | roadmap |
| RL-044 | AI Act art. 50: dicitura nel testo ma non nei metadati; classificazione non scritta | Bassa | correggere |
| RL-019 | Storico AI senza conservazione (già in T4-102) | Media | correggere |
