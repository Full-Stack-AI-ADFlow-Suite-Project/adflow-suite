/**
 * Gli stati di campagna e post come si leggono nelle pagine (brief-richieste
 * §1.1). Il valore che arriva dal backend non cambia: cambiano l'etichetta,
 * la spiegazione e il colore. Un valore che non è in tabella si mostra com'è.
 */

export type TipoStato = "campagna" | "post";
export type Ruolo = "artigiano" | "operatore";

interface Voce {
  etichetta: string;
  spiegazione: string;
}

/** Campagna, vista dell'operatore. */
export const STATI_CAMPAGNA: Record<string, Voce> = {
  bozza: {
    etichetta: "Bozza",
    spiegazione: "L'artigiano la sta ancora preparando.",
  },
  inviata: {
    etichetta: "In coda",
    spiegazione: "Inviata dall'artigiano: l'AI la prende tra poco.",
  },
  in_generazione: {
    etichetta: "L'AI la prepara",
    spiegazione: "L'AI analizza le foto e scrive piano e post.",
  },
  generazione_fallita: {
    etichetta: "Preparazione non riuscita",
    spiegazione: "L'AI si è fermata: leggi l'errore e usa Riprova.",
  },
  piano_da_rivedere: {
    etichetta: "Piano da rivedere",
    spiegazione: "Stato delle campagne di prima dell'MVP.",
  },
  in_revisione: {
    etichetta: "Da rivedere",
    spiegazione: "Piano e post pronti: sistemali, poi approva o respingi.",
  },
  respinta: {
    etichetta: "Respinta",
    spiegazione: "Respinta dal consorzio: l'artigiano ne crea una nuova.",
  },
  scaduta: { etichetta: "Scaduta", spiegazione: "Non approvata in tempo." },
  attiva: {
    etichetta: "In pubblicazione",
    spiegazione: "Approvata: i post escono alla loro data.",
  },
  sospesa: {
    etichetta: "Sospesa",
    spiegazione: "Le pubblicazioni sono ferme finché non la riattivi.",
  },
  annullata: {
    etichetta: "Annullata",
    spiegazione: "Chiusa dal consorzio: i post rimasti non escono.",
  },
  conclusa: {
    etichetta: "Conclusa",
    spiegazione: "Tutti i post sono usciti o chiusi.",
  },
};

/** Post, vista dell'operatore. */
export const STATI_POST: Record<string, Voce> = {
  da_approvare: {
    etichetta: "Da approvare",
    spiegazione: "Esce con l'approvazione della campagna.",
  },
  approvato: {
    etichetta: "In programma",
    spiegazione: "Approvato: esce alla sua data.",
  },
  pubblicato: {
    etichetta: "Pubblicato",
    spiegazione: "Uscito sulla pagina.",
  },
  fallito: {
    etichetta: "Non pubblicato",
    spiegazione: "La pubblicazione non è riuscita: riprogrammalo.",
  },
  annullato: {
    etichetta: "Annullato",
    spiegazione: "Annullato dal consorzio: non esce.",
  },
  scartato: {
    etichetta: "Scartato",
    spiegazione: "Tolto con il suo canale o con la campagna.",
  },
  scaduto: {
    etichetta: "Scaduto",
    spiegazione: "La sua data è passata prima dell'approvazione.",
  },
};

/** Il post con un blocco del validatore (`da_rivedere` vero). */
export const POST_DA_CORREGGERE: Voce = {
  etichetta: "Da correggere",
  spiegazione: "Ha un blocco: si sblocca con una versione senza blocchi.",
};

/** Post, vista dell'artigiano (spec §4). */
const POST_ARTIGIANO: Record<string, string> = {
  approvato: "In programma",
  pubblicato: "Pubblicato",
  fallito: "Non pubblicato",
  annullato: "Non pubblicato",
};

/** Colore del badge per lo stato della campagna. */
export function coloreCampagna(stato: string): string {
  if (
    stato === "in_revisione" ||
    stato === "piano_da_rivedere" ||
    stato === "sospesa"
  )
    return "yellow";
  if (
    stato === "generazione_fallita" ||
    stato === "respinta" ||
    stato === "scaduta" ||
    stato === "annullata"
  )
    return "red";
  if (stato === "attiva" || stato === "conclusa") return "verde";
  return "gray";
}

/** Colore del badge per lo stato del post. */
export function colorePost(stato: string): string {
  if (stato === "approvato" || stato === "pubblicato") return "verde";
  if (
    stato === "fallito" ||
    stato === "scaduto" ||
    stato === "scartato" ||
    stato === "annullato"
  )
    return "red";
  return "yellow";
}

/** L'etichetta di uno stato per chi guarda; il valore ignoto resta com'è. */
export function etichettaStato(
  tipo: TipoStato,
  valore: string,
  ruolo: Ruolo = "operatore",
): string {
  if (tipo === "post" && ruolo === "artigiano")
    return POST_ARTIGIANO[valore] ?? STATI_POST[valore]?.etichetta ?? valore;
  const tabella = tipo === "campagna" ? STATI_CAMPAGNA : STATI_POST;
  return tabella[valore]?.etichetta ?? valore;
}

/** La spiegazione di uno stato, se c'è (solo per l'operatore). */
export function spiegazioneStato(
  tipo: TipoStato,
  valore: string,
): string | undefined {
  return (tipo === "campagna" ? STATI_CAMPAGNA : STATI_POST)[valore]
    ?.spiegazione;
}
