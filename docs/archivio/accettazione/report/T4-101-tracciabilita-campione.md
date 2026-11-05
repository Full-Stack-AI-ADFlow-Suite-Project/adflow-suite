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
