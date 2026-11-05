# Spec · cosa fa il prodotto

Versione corta (ADR-122). Il testo completo, con ogni dettaglio delle regole e il testo di tutti i criteri di accettazione, è in `docs/archivio/completi/spec.md`; ciò che non entra nell'MVP è in `docs/archivio/fuori-mvp.md` e `docs/ROADMAP.md`. Dove questa pagina non torna con il codice, vale il codice. I numeri stanno nelle regole (§5); i numeri delle sezioni sono quelli del testo completo.

## 0–1. Perimetro e attori
AdFlow prepara e pubblica le campagne social degli artigiani di un consorzio. L'artigiano descrive la bottega una volta (profilo) e per ogni campagna sceglie periodo, canali (Facebook, Instagram) e, se vuole, carica foto a gruppi. L'AI analizza le foto, scrive il piano e i testi; le foto che mancano diventano immagini AI. L'operatore del consorzio rivede, sistema, chiede all'artigiano ciò che può dare solo lui, approva o respinge. Il worker pubblica i post approvati alla loro data, nell'MVP su una sola pagina di prova Meta.

- **Attori**: artigiano; operatore (rivede, decide, crea gli artigiani, R-37); admin (crea gli operatori da riga di comando, nelle pagine vale come operatore, R-29); sistema (genera, controlla le scadenze, pubblica, scrive le notifiche). Un solo consorzio.
- **Congelato** (codice e test restano, l'interfaccia lo nasconde): archivio come rimpiazzo (R-27), caroselli (R-21), spunta (R-30), nota interna (R-32), togli canale.

## 2. Flusso
**2.1 Profilo e campagna.** **Profilo** (passi 1–9, una volta; ai rientri il Bentornato: "Va bene così" o "Modifica", R-10). **Campagna** (passi 10–12): bozza con titolo, periodo, descrizione e canali collegati (R-08, R-12, R-22); gruppi di foto facoltativi (R-13); riepilogo con gli avvisi che non bloccano (R-25), dichiarazione (R-41) e invio, che salva la fotografia del profilo (R-11).

**2.2 Generazione** a tappe salvate (R-24): analisi delle foto → piano con i post chiesti dalla frequenza (R-05, R-26), mai fermo per mancanza di foto → immagini AI per i post scoperti (R-28, R-43) e foto sistemate (R-42) → testo e hashtag per canale, con il validatore (R-09, R-21). Fine: post `da_approvare`, campagna `in_revisione`, notifica agli operatori. Errori: R-35. Costi e storico: R-44, R-50.

**2.3 Revisione** in Vedi campagna: modifica a mano, Rigenera testo, Rigenera immagine, Cambia immagine (con «Rifai il post»), Sposta (R-16, R-30, R-03, R-49, R-36); **Chiedi all'artigiano** (R-46); poi **Approva** la campagna intera (R-14) o **Respingi** con motivo e nota (R-18). Un post non si toglie: si sistema. Nessuna modifica fa partire l'AI da sola.

**2.3 (dopo l'approvazione)**: sui post che escono tra almeno 15 minuti modifica a mano, cambia immagine, sposta, annulla (R-16), riprogramma un post fallito (R-34); sulla campagna sospendi, riattiva, annulla (R-33). Mai AI.

**2.4 Pubblicazione** (tick ogni minuto): i post approvati alla loro data, con la foto sistemata; errori temporanei ritentati, un post `fallito` notificato; campagna `conclusa` quando ogni post è chiuso (R-34). Scadenza morbida: R-06.

## 3. Motivi del No
**Quando respingere**: solo ciò che l'operatore non può sistemare: foto non pubblicabili e non sostituibili (non della bottega, persone senza consenso, marchi altrui, contenuti vietati), affermazioni che l'artigiano non conferma (prezzi, sconti, concorsi, certificazioni), fuori contratto. Mai per testo, tono o hashtag. Ogni intervento crea una versione nuova con il suo autore, che ripassa il validatore (R-02, R-04).

## 4. Cosa vede chi
- **Artigiano**: barra con Ingresso, Campagne, Calendario, Archivio foto, Profilo bottega, Esci (ADR-117). Mai post `da_approvare`, `scartato` o `scaduto`, mai note interne; in revisione nessun piano e nessun post, solo la richiesta del consorzio se c'è (R-46). Respinta: motivo, nota e foto da rifare; dopo l'approvazione il calendario della campagna (R-45). La pagina Campagna mostra una campagna alla volta e apre quella che chiede qualcosa. Il testo dei post si legge senza pulsanti: "Qualcosa non va? Chiama il consorzio".
- **Operatore**: barra con Da approvare, Artigiani, Calendario, Storico AI, Nuovo artigiano, Esci. Campagne da approvare dalla più urgente (R-38); elenco e pagina degli artigiani (R-38), archivio foto (R-47), calendario settimanale (R-48), storico dell'AI (R-50). Si decide solo in Vedi campagna, con i pulsanti che il server dice ammessi adesso.

## 5. Regole
| ID | Regola |
|---|---|
| R-01 | Si pubblica solo un post approvato. |
| R-02 | Ogni intervento crea una versione nuova; le precedenti restano. |
| R-03 | Max **3** rigenerazioni del testo per post (da zero o da un testo di partenza); la modifica a mano non consuma cicli. Le immagini si contano a parte (R-49). |
| R-04 | Le versioni rifiutate vanno all'AI come "cosa non rifare". |
| R-05 | Post chiesti per canale = post/settimana × giorni ÷ **7**, per difetto. Il codice passa all'AI solo le foto migliori per punteggio fino ai post chiesti; i post scoperti hanno un'immagine AI (R-28). Una foto al massimo in **1** post per canale. |
| R-06 | Scadenza morbida: un post `da_approvare` scade quando passa la sua data; la campagna con un piano scade quando restano meno della **metà** dei post chiesti; senza piano alle **00:00** (Europe/Rome) del giorno di inizio. |
| R-08 | Inizio ≥ oggi + **3** giorni; durata da **7** a **92** giorni; ogni post dentro il periodo e ≥ adesso + **15** min. |
| R-09 | Validatore a due livelli: **blocco** (prezzi o premi non nei dati, parole vietate, "cose da non dire", testo vuoto, limiti della piattaforma) e **avviso** (limiti editoriali). Max **3** riscritture, poi con un blocco il post è `da_rivedere`. Piano non valido: **3** riscritture, poi errore tecnico. |
| R-10 · R-11 | Profilo compilato una volta, confermato ai rientri; all'invio la campagna ne salva la fotografia, usata da generazione e rigenerazioni. |
| R-12 | Una sola bozza per artigiano; campagne sovrapposte ammesse, con l'avviso e il piano che evita gli orari occupati (ADR-119). |
| R-13 | Gruppo: da **1** a **20** foto, descrizione obbligatoria all'invio; foto JPG/PNG/WEBP, ≤ **10 MB**, lato corto ≥ **1080 px**; nessun minimo di foto. Dopo l'invio foto nuove solo con una richiesta (R-46). |
| R-14 | Si approva la campagna intera: i post `da_approvare` con la data passata scadono, gli altri si approvano. Mai con un post `da_rivedere`, un intervento in corso o nessun post da approvare. |
| R-15 | Respinta o scaduta = chiusa; l'artigiano ne crea una nuova. |
| R-16 | Interventi ammessi per stato (`INTERVENTI_AMMESSI` in `contenuti/domain.py`): in revisione modifica, rigenera, rigenera immagine, cambia foto, sposta; in attiva o sospesa, su un post che esce tra almeno **15** minuti, modifica, cambia foto, sposta, annulla (con nota); su un `fallito` riprogramma. Dopo l'approvazione la versione dell'operatore nasce approvata e nessuna AI. |
| R-18 | Le foto non idonee restano fuori dai post. Respingi vuole motivo (`foto` / `altro`) e nota. Un post non si toglie. |
| R-21 | Scheda per canale: avviso oltre Facebook **500** caratteri e **3** hashtag, Instagram **600** e **5**; blocco oltre Facebook **5000** e **30**, Instagram **2200** e **30**. Un post = **1** foto; foto da **4:5** a **1,91:1**, immagini AI **1:1**. |
| R-22 | Canali della campagna: almeno uno, solo con account `collegato` (422 in bozza, 409 all'invio). Frequenza per canale. |
| R-24 | Generazione a tappe salvate; Riprova non rifà ciò che è salvato. |
| R-25 | Avvisi che non bloccano: `foto_poche`, `riempitivi_molti` (più di **1** post scoperto ogni **2** foto), `frequenza_alta` (post/settimana × **4** oltre la fascia di foto al mese del profilo), `campagne_sovrapposte`. |
| R-26 | La frequenza è un impegno: escono i post chiesti, non meno. Prezzo e fatturazione fuori MVP. |
| R-27 | Congelato come rimpiazzo nel piano. Archivio della bottega: le foto idonee delle campagne chiuse e dei gruppi senza campagna, meno quelle segnate in una respinta; una foto già uscita su un canale torna lì dopo **90** giorni. Dall'ADR-119 si propone in Cambia immagine. |
| R-28 | I post scoperti hanno un'immagine AI quadrata **1:1** (foto `creata_ai`), la stessa per l'uscita sui due canali; nessun tetto. |
| R-29 | Dopo l'accesso: artigiano → Ingresso (Profilo se non ce l'ha); operatore e admin → Da approvare. Sessione senza uso: **7** giorni artigiano, **12** ore operatore e admin. Contatto del consorzio dalla configurazione. Nessun recupero password per email. |
| R-30 | Modifica a mano dove R-16 la ammette: versione `modifica_operatore`, validata; con un blocco o senza cambiamenti → 422. Spunta congelata. |
| R-31 | Intervento in corso: tipo e ora sul post; si spegne alla versione nuova o alla terza esecuzione fallita (ciclo non contato); dopo **10** minuti vale come fallito. Con un intervento in corso nessun altro → 409. |
| R-32 | Nota interna (congelata): solo per gli operatori, nessuno stato, nessuna email. |
| R-33 | Sospendi (nota facoltativa, interna), riattiva (gli arretrati scelti si pubblicano, gli altri `annullato`), annulla (i post approvati `annullato`). |
| R-34 | Riprogramma un post `fallito` dentro il periodo, ≥ adesso + **15** min. La campagna è `conclusa` quando ogni post è chiuso; con un `fallito`, solo a periodo finito. |
| R-35 | Errori dell'AI: `temporaneo` e `risposta` → **3** esecuzioni, poi `generazione_fallita`; `configurazione` → subito; `richiesta` o `rifiuto` su una foto → foto non idonea, sul testo → versione vuota con un blocco. Ferma da **30** minuti in `inviata` o `in_generazione` → `generazione_fallita`. |
| R-36 | Cambia foto (in pagina «Cambia immagine»): foto del gruppo, poi della campagna, poi dell'archivio, non già in un altro post dello stesso canale; stesso testo; con «Riscrivi anche il testo», in revisione, segue una rigenerazione («Rifai il post»). Sposta: nuova data nel periodo, ≥ **15** min, diversa da prima. |
| R-37 | Nuovo artigiano: email e nome; password generata e mostrata una volta; email già usata → 409. |
| R-38 | Da approvare ordinate per "entro quando". Elenco degli artigiani con canali, campagne e prossima scadenza; pagina e campagne dell'artigiano (ADR-117). |
| R-41 | Dichiarazione obbligatoria all'invio e su ogni foto di una richiesta: prodotti della bottega, consenso delle persone. |
| R-42 | Sistemazione locale delle foto: rotazione, GPS tolto, lato corto **1080 px**, JPEG; da 4:5 a 1,91:1 nessun taglio; fuori, ritaglio sul soggetto se toglie al più il **35%**, al centro se al più il **10%**, altrimenti bordi sfocati. Mai deformata; l'originale resta. |
| R-43 | Immagini AI: ambienti, materiali, lavorazioni, atmosfere; mai un prodotto presentato come della bottega, persone, testi, marchi. Il testo porta "Immagine creata con AI". |
| R-44 | Ogni chiamata all'AI registra tipo, modello e costo stimato; Vedi campagna mostra il totale. Nessun tetto di spesa nel codice. |
| R-45 | Calendario della campagna: i post approvati, pubblicati, falliti o annullati, per giorno, dopo l'approvazione. |
| R-46 | Richiesta all'artigiano, in revisione: una domanda e da **0** a **3** foto da sostituire; l'artigiano carica una foto per ognuna e risponde. Stato `aperta`, `inviata` o `decaduta`, ricavato dalle decisioni. Non blocca Approva né Respingi; nessuna email. |
| R-47 | Archivio foto in sola lettura, a blocchi per campagna; all'artigiano le immagini AI solo delle campagne approvate. |
| R-48 | Calendario settimanale da lunedì a domenica (Europe/Rome): l'artigiano i suoi post, l'operatore quelli di tutti. |
| R-49 | Rigenera immagine, solo in revisione, max **3** per post, con una nota facoltativa; con «Riscrivi anche il testo» segue una rigenerazione (R-03). |
| R-50 | Storico dell'AI: ogni chiamata, riuscita o fallita, con prompt, richiesta (foto come id), risposta, esito, durata; numeri per versione del prompt e voto da 1 a 5. Mai nei log. |

## 6. Criteri di accettazione
Ogni criterio è un test che porta l'ID nel nome (`test_ca09_…`): il test è il contratto, il testo completo di ogni criterio è in `docs/archivio/completi/spec.md` §6.

| Area | Criteri |
|---|---|
| Accesso e ruoli | CA-01…CA-05, CA-61…CA-63, CA-79 |
| Profilo e campagna dell'artigiano | CA-06…CA-16, CA-48, CA-54, CA-70, CA-100 |
| Generazione e AI | CA-17…CA-20, CA-50, CA-57…CA-60, CA-68, CA-80, CA-82, CA-101, CA-106…CA-109, CA-113, CA-115 |
| Revisione e interventi | CA-21…CA-31, CA-64…CA-67, CA-69, CA-71, CA-72, CA-84, CA-85, CA-102…CA-105 |
| Richiesta all'artigiano | CA-86…CA-91 |
| Pubblicazione e calendario | CA-32, CA-36…CA-39, CA-55, CA-56, CA-83, CA-97, CA-98 |
| Foto e archivio | CA-81, CA-95, CA-96, CA-114 |
| Pagine dell'operatore e storico AI | CA-92…CA-94, CA-99, CA-110…CA-112, CA-116 |
| Congelati (restano verdi) | CA-23, CA-53, CA-65 |
