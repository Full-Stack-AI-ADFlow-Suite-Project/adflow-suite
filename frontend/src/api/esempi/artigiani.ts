/** Dati di esempio del modulo artigiani: canali e profilo (2a). */
import type { CanaleCollegato, ProfiloBottega } from "../artigiani";

export { USA_ESEMPI } from "./accesso";

export const canaliEsempio: CanaleCollegato[] = [
  { canale: "facebook", collegato: true },
  { canale: "instagram", collegato: true },
];

export const profiloEsempio: ProfiloBottega = {
  bottega: "Falegnameria Bianchi",
  referente: "Mario Bianchi",
  citta: "Bra (CN)",
  tipo_prodotto: "Legno e mobili",
  obiettivo: "Farmi conoscere",
  canali_preferiti: ["facebook", "instagram"],
  frequenza: "f3_4",
  foto_policy: { quantita_mese: "da5_a12" },
};

/**
 * Le botteghe del consorzio, per l'elenco dell'operatore (GET /campagne
 * aggiunge bottega e città) e per il profilo_snapshot delle campagne inviate.
 * La chiave è il profilo_id; 1 è la bottega di Mario (l'artigiano di esempio).
 */
export interface BottegaEsempio {
  bottega: string;
  referente: string;
  citta: string;
  tipo_prodotto: string;
  obiettivo: string;
  frequenza: string;
  tono: string;
  clienti: string;
  da_non_dire: string;
}

export const profiliEsempio: Record<number, BottegaEsempio> = {
  1: {
    bottega: "Falegnameria Bianchi",
    referente: "Mario Bianchi",
    citta: "Bra (CN)",
    tipo_prodotto: "Legno e mobili",
    obiettivo: "Farmi conoscere",
    frequenza: "f3_4",
    tono: "Caldo e familiare, do del tu",
    clienti: "Coppie che stanno arredando casa, zona Cuneo e Torino",
    da_non_dire: "Niente prezzi dei concorrenti, niente sconti non autorizzati",
  },
  2: {
    bottega: "Ceramiche Olivero",
    referente: "Anna Olivero",
    citta: "Mondovì (CN)",
    tipo_prodotto: "Ceramica da tavola",
    obiettivo: "Vendere di più",
    frequenza: "f3_4",
    tono: "Semplice e curato",
    clienti: "Famiglie e ristoranti della zona",
    da_non_dire: "Non promettere spedizioni fuori regione",
  },
  3: {
    bottega: "Pelletteria Ferrero",
    referente: "Giulia Ferrero",
    citta: "Alba (CN)",
    tipo_prodotto: "Borse e accessori in pelle",
    obiettivo: "Riempire l'agenda ordini",
    frequenza: "f1_2",
    tono: "Elegante ma diretto",
    clienti: "Donne 30-60 anni, regali e occasioni",
    da_non_dire: "Mai parlare di pelle sintetica come pelle",
  },
  4: {
    bottega: "Tessitura Gallo",
    referente: "Paolo Gallo",
    citta: "Saluzzo (CN)",
    tipo_prodotto: "Tessuti e capi in lana",
    obiettivo: "Farmi conoscere",
    frequenza: "f1_2",
    tono: "Calmo e raccontato",
    clienti: "Chi cerca capi che durano",
    da_non_dire: "Niente confronti con la grande distribuzione",
  },
};
