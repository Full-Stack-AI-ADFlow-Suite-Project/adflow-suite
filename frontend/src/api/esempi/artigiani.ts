/** Dati di esempio del modulo artigiani: canali e profilo (2a). */
import { datiScrittura, erroriProfilo, type CanaleCollegato, type DatiProfilo, type ProfiloBottega, type ProfiloPubblico } from "../artigiani";
import { ApiErrore } from "../http";
import { sessioneEsempio, USA_ESEMPI } from "./accesso";

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

/** Archivio locale del profilo completo, separato per utente. T2a-07 collega le API. */
const PROFILO_BASE: ProfiloPubblico = {
  id: 1, nome: "Falegnameria Bianchi", referente: "Mario Bianchi", citta: "Bra (CN)",
  tipo_prodotto: "legno_mobili", clienti_ideali: "Coppie che stanno arredando casa",
  obiettivo: "notorieta", canali: ["facebook", "instagram"], anni_attivita: 20,
  sito: null, storia: "Mobili fatti a mano nella nostra bottega.", origine: null,
  valori: ["artigianalita", "su_misura"], gamma: null, fascia_prezzo: "media",
  stagionalita: null, zona: "Cuneo e Torino", tono: ["caldo"], cortesia: "tu",
  vincoli: "Niente sconti non autorizzati", frequenza: "f3_4", orari: null,
  social_esistenti: null, foto_policy: { quantita_mese: "da5_a12" },
  eventi_ricorrenti: null, chiusure: null, logo: null,
  aggiornato_il: "2026-10-10T00:00:00Z",
};
function chiaveProfilo(): { chiave: string; id: number } {
  const u = sessioneEsempio();
  if (USA_ESEMPI && !u) throw new ApiErrore(401, "Sessione assente.");
  if (u && u.ruolo !== "artigiano") throw new ApiErrore(403, "Accesso riservato agli artigiani.");
  // In modalità API la pagina resta su esempi fino alla chiusura: un archivio distinto.
  return { chiave: `adflow_profilo_esempio_${u?.id ?? "anteprima"}`, id: u?.id ?? 1 };
}
export function leggiProfiloEsempio(): ProfiloPubblico | null {
  const { chiave, id } = chiaveProfilo();
  const grezzo = localStorage.getItem(chiave);
  if (grezzo === null) return id === 1 ? structuredClone(PROFILO_BASE) : null;
  try {
    const p = JSON.parse(grezzo) as ProfiloPubblico | null;
    if (p === null) return null;
    if (!p || typeof p !== "object" ||
      [p.nome, p.referente, p.citta, p.tipo_prodotto, p.clienti_ideali, p.obiettivo].some((v) => typeof v !== "string") ||
      !Array.isArray(p.canali) || typeof p.id !== "number" || typeof p.aggiornato_il !== "string")
      throw new Error("Formato non valido.");
    return p;
  }
  catch { throw new ApiErrore(422, "Il profilo di esempio salvato non è leggibile."); }
}
export function salvaProfiloEsempio(dati: DatiProfilo): ProfiloPubblico {
  const { chiave, id } = chiaveProfilo();
  if (Object.keys(erroriProfilo(dati)).length)
    throw new ApiErrore(422, "Completa i campi obbligatori del profilo.");
  const precedente = leggiProfiloEsempio();
  const p: ProfiloPubblico = {
    ...datiScrittura(dati), id: precedente?.id ?? id,
    logo: precedente?.logo ?? null, aggiornato_il: new Date().toISOString(),
  };
  try { localStorage.setItem(chiave, JSON.stringify(p)); }
  catch { throw new ApiErrore(422, "Il profilo non è stato salvato. Libera spazio nel browser e riprova."); }
  return structuredClone(p);
}
