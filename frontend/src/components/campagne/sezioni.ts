/**
 * Le sezioni dell'elenco delle campagne, per lato (spec §4, brief-pagine.md
 * §1.1). Gli stati di ogni sezione stanno solo qui; nel backend i conteggi
 * dell'elenco artigiani li ripetono in `revisione/letture.py`.
 */
import type { CampagnaElencoItem } from "../../api/campagne";

export type Lato = "artigiano" | "operatore";

export interface Sezione {
  chiave: "in_corso" | "in_lavorazione" | "da_approvare" | "bozza" | "passate";
  titolo: string;
  campagne: CampagnaElencoItem[];
  /** Una riga che informa e non si apre (la bozza vista dall'operatore). */
  informativa?: boolean;
}

const IN_CORSO = ["attiva", "sospesa"];
/** Dall'invio all'approvazione. `piano_da_rivedere` resta per le righe vecchie. */
const DA_APPROVARE = [
  "inviata",
  "in_generazione",
  "generazione_fallita",
  "piano_da_rivedere",
  "in_revisione",
];
const PASSATE = ["conclusa", "annullata", "scaduta", "respinta"];

/** Dalla più recente: l'ordine di creazione è l'id. */
const recenti = (lista: CampagnaElencoItem[], stati: string[]) =>
  lista.filter((c) => stati.includes(c.stato)).sort((a, b) => b.id - a.id);

/**
 * Le sezioni non vuote, nell'ordine della pagina. L'artigiano ha la bozza in
 * cima a "In lavorazione"; l'operatore la vede come una riga che non si apre.
 */
export function sezioniDi(lato: Lato, lista: CampagnaElencoItem[]): Sezione[] {
  const bozze = recenti(lista, ["bozza"]);
  const sezioni: Sezione[] =
    lato === "artigiano"
      ? [
          {
            chiave: "in_corso",
            titolo: "In corso",
            campagne: recenti(lista, IN_CORSO),
          },
          {
            chiave: "in_lavorazione",
            titolo: "In lavorazione",
            campagne: [...bozze, ...recenti(lista, DA_APPROVARE)],
          },
          {
            chiave: "passate",
            titolo: "Passate",
            campagne: recenti(lista, PASSATE),
          },
        ]
      : [
          {
            chiave: "in_corso",
            titolo: "In corso",
            campagne: recenti(lista, IN_CORSO),
          },
          {
            chiave: "da_approvare",
            titolo: "Da approvare",
            campagne: recenti(lista, DA_APPROVARE),
          },
          {
            chiave: "bozza",
            titolo: "In bozza",
            campagne: bozze,
            informativa: true,
          },
          {
            chiave: "passate",
            titolo: "Storico",
            campagne: recenti(lista, PASSATE),
          },
        ];
  return sezioni.filter((s) => s.campagne.length > 0);
}
