/** Dati di esempio del modulo artigiani: canali, profilo ed elenco botteghe. */
import {
  datiScrittura,
  erroriProfilo,
  type ArtigianoElenco,
  type CampagnaSezione,
  type CanaleCollegato,
  type DatiProfilo,
  type ProfiloBottega,
  type ProfiloPubblico,
  type SchedaArtigiano,
} from "../artigiani";
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
  id: 1,
  nome: "Falegnameria Bianchi",
  referente: "Mario Bianchi",
  citta: "Bra (CN)",
  tipo_prodotto: "legno_mobili",
  clienti_ideali: "Coppie che stanno arredando casa",
  obiettivo: "notorieta",
  canali: ["facebook", "instagram"],
  anni_attivita: 20,
  sito: null,
  storia: "Mobili fatti a mano nella nostra bottega.",
  origine: null,
  valori: ["artigianalita", "su_misura"],
  gamma: null,
  fascia_prezzo: "media",
  stagionalita: null,
  zona: "Cuneo e Torino",
  tono: ["caldo"],
  cortesia: "tu",
  vincoli: "Niente sconti non autorizzati",
  frequenza: "f3_4",
  orari: null,
  social_esistenti: null,
  foto_policy: { quantita_mese: "da5_a12" },
  eventi_ricorrenti: null,
  chiusure: null,
  aggiornato_il: "2026-10-10T00:00:00Z",
};
function chiaveProfilo(): { chiave: string; id: number } {
  const u = sessioneEsempio();
  if (USA_ESEMPI && !u) throw new ApiErrore(401, "Sessione assente.");
  if (u && u.ruolo !== "artigiano")
    throw new ApiErrore(403, "Accesso riservato agli artigiani.");
  // In modalità API la pagina resta su esempi fino alla chiusura: un archivio distinto.
  return {
    chiave: `adflow_profilo_esempio_${u?.id ?? "anteprima"}`,
    id: u?.id ?? 1,
  };
}
export function leggiProfiloEsempio(): ProfiloPubblico | null {
  const { chiave, id } = chiaveProfilo();
  const grezzo = localStorage.getItem(chiave);
  if (grezzo === null) return id === 1 ? structuredClone(PROFILO_BASE) : null;
  try {
    const p = JSON.parse(grezzo) as ProfiloPubblico | null;
    if (p === null) return null;
    if (
      !p ||
      typeof p !== "object" ||
      [
        p.nome,
        p.referente,
        p.citta,
        p.tipo_prodotto,
        p.clienti_ideali,
        p.obiettivo,
      ].some((v) => typeof v !== "string") ||
      !Array.isArray(p.canali) ||
      typeof p.id !== "number" ||
      typeof p.aggiornato_il !== "string"
    )
      throw new Error("Formato non valido.");
    return p;
  } catch {
    throw new ApiErrore(422, "Il profilo di esempio salvato non è leggibile.");
  }
}
export function salvaProfiloEsempio(dati: DatiProfilo): ProfiloPubblico {
  const { chiave, id } = chiaveProfilo();
  if (Object.keys(erroriProfilo(dati)).length)
    throw new ApiErrore(422, "Completa i campi obbligatori del profilo.");
  const precedente = leggiProfiloEsempio();
  const p: ProfiloPubblico = {
    ...datiScrittura(dati),
    id: precedente?.id ?? id,
    aggiornato_il: new Date().toISOString(),
  };
  try {
    localStorage.setItem(chiave, JSON.stringify(p));
  } catch {
    throw new ApiErrore(
      422,
      "Il profilo non è stato salvato. Libera spazio nel browser e riprova.",
    );
  }
  return structuredClone(p);
}

/** Elenco e scheda degli artigiani (l'operatore): stesse botteghe di `profiliEsempio`. */

const ACCOUNT_ESEMPIO: Record<number, { email: string; attivo: boolean }> = {
  1: { email: "mario@falegnameriabianchi.it", attivo: true },
  2: { email: "anna@ceramicheolivero.it", attivo: true },
  3: { email: "giulia@pelletteriaferrero.it", attivo: true },
  4: { email: "paolo@tessituragallo.it", attivo: true },
};

function campagnaSezione(
  id: number,
  titolo: string,
  stato: string,
  inizio: string,
  fine: string,
  parziale?: Partial<CampagnaSezione>,
): CampagnaSezione {
  return {
    id,
    titolo,
    stato,
    inizio,
    fine,
    canali: ["facebook", "instagram"],
    inviata_il: null,
    chiusa_il: null,
    n_post: 0,
    n_pubblicati: 0,
    n_falliti: 0,
    n_foto: 0,
    ...parziale,
  };
}

/** Il profilo in sola lettura della bottega 1 (ProfiloArtigiano di schemas.py). */
const PROFILO_BOTTEGA_ESEMPIO: SchedaArtigiano["profilo"] = {
  id: 1,
  nome: "Falegnameria Bianchi",
  referente: "Mario Bianchi",
  citta: "Bra (CN)",
  tipo_prodotto: "Mobili in legno massello su misura",
  clienti_ideali:
    "Famiglie del territorio e giovani coppie che arredano la prima casa.",
  obiettivo: "Far conoscere il laboratorio e portare richieste di preventivo.",
  canali: ["facebook", "instagram"],
  anni_attivita: 38,
  sito: "https://www.falegnameriabianchi.it",
  storia:
    "Laboratorio aperto nel 1987 dal nonno Giovanni; oggi lo portano avanti Mario e la figlia Elena.",
  origine:
    "Tutto è nato in una cascina di famiglia, tra piallatura e restauro di mobili antichi.",
  valori: ["artigianalità", "legno certificato", "riparazione", "territorio"],
  gamma: "Su misura e piccola serie",
  fascia_prezzo: "media-alta",
  stagionalita: "Forte a Natale e in primavera",
  zona: "Langa e Roero",
  tono: ["caldo", "professionale"],
  cortesia: "diamo del tu",
  vincoli:
    "Niente promesse di sconti aggressivi e niente foto di clienti senza consenso.",
  frequenza: "2 post a settimana",
  orari: {
    giorni: "lun–ven",
    mattina: "8:30–12:30",
    pomeriggio: "14:30–18:30",
  },
  social_esistenti: { facebook: "falegnameriabianchi", follower: 1800 },
  foto_policy: { foto_proprie: true, foto_mensili: "4–6" },
  eventi_ricorrenti: [
    { nome: "Fiera del Tartufo di Alba", periodo: "ottobre" },
    { nome: "Mercatino di Natale di Bra", periodo: "dicembre" },
  ],
  chiusure: "Ferie ad agosto, dal 10 al 25.",
  aggiornato_il: "2026-09-15T09:30:00Z",
};

const SCHEDE_ESEMPIO: Record<number, SchedaArtigiano> = {
  1: {
    artigiano: {
      id: 1,
      email: "mario@falegnameriabianchi.it",
      nome: "Mario Bianchi",
      attivo: true,
    },
    profilo: PROFILO_BOTTEGA_ESEMPIO,
    canali_collegati: ["facebook", "instagram"],
    bozza: campagnaSezione(
      101,
      "Campagna Novembre 2026",
      "bozza",
      "2026-11-01",
      "2026-11-30",
      { n_foto: 3 },
    ),
    da_approvare: [
      {
        id: 102,
        profilo_id: 1,
        titolo: "Campagna Ottobre 2026",
        inizio: "2026-10-01",
        fine: "2026-10-31",
        stato: "in_revisione",
        canali: ["facebook", "instagram"],
        bottega: "Falegnameria Bianchi",
        citta: "Bra (CN)",
        conteggi: {
          totale: 26,
          da_approvare: 26,
          da_rivedere: 1,
          riempitivi: { facebook: 3 },
        },
        entro_quando: "2026-10-01T18:30:00+02:00",
        ultima_nota: "Aspetto conferma delle date del mercatino.",
        richiesta: null,
      },
    ],
    in_corso: [
      campagnaSezione(
        103,
        "Campagna Settembre 2026",
        "attiva",
        "2026-09-01",
        "2026-09-30",
        {
          canali: ["facebook"],
          n_post: 12,
          n_pubblicati: 10,
          n_falliti: 1,
          n_foto: 8,
          inviata_il: "2026-08-25T10:00:00Z",
        },
      ),
    ],
    chiuse: [
      campagnaSezione(
        104,
        "Campagna Agosto 2026",
        "scaduta",
        "2026-08-01",
        "2026-08-31",
        {
          canali: ["facebook"],
          n_post: 8,
          n_foto: 8,
          chiusa_il: "2026-08-01T00:00:00Z",
        },
      ),
      campagnaSezione(
        105,
        "Campagna Luglio 2026",
        "conclusa",
        "2026-07-01",
        "2026-07-31",
        {
          canali: ["facebook"],
          n_post: 13,
          n_pubblicati: 12,
          n_falliti: 1,
          n_foto: 9,
          chiusa_il: "2026-08-01T00:00:00Z",
          inviata_il: "2026-06-20T10:00:00Z",
        },
      ),
      campagnaSezione(
        106,
        "Campagna Luglio 2026 · primo invio",
        "respinta",
        "2026-07-01",
        "2026-07-31",
        {
          canali: ["facebook"],
          n_post: 13,
          n_foto: 6,
          chiusa_il: "2026-06-22T00:00:00Z",
        },
      ),
    ],
    totale_chiuse: 4,
  },
  2: {
    artigiano: {
      id: 2,
      email: "anna@ceramicheolivero.it",
      nome: "Anna Olivero",
      attivo: true,
    },
    profilo: {
      ...PROFILO_BOTTEGA_ESEMPIO,
      id: 2,
      nome: "Ceramiche Olivero",
      referente: "Anna Olivero",
      citta: "Albissola Marina (SV)",
      tipo_prodotto: "Ceramiche artistiche e maioliche dipinte a mano",
      canali: ["instagram"],
      sito: null,
      anni_attivita: null,
    },
    canali_collegati: ["instagram"],
    bozza: null,
    da_approvare: [],
    in_corso: [],
    chiuse: [],
    totale_chiuse: 0,
  },
};

export function elencoArtigianiEsempio(): Promise<ArtigianoElenco[]> {
  const righe: ArtigianoElenco[] = Object.entries(profiliEsempio).map(
    ([profiloId, bottega]) => {
      const id = Number(profiloId);
      const scheda = SCHEDE_ESEMPIO[id];
      return {
        id,
        email: ACCOUNT_ESEMPIO[id]?.email ?? `${id}@example.test`,
        nome: bottega.referente,
        attivo: ACCOUNT_ESEMPIO[id]?.attivo ?? true,
        profilo_id: id,
        bottega: bottega.bottega,
        citta: bottega.citta,
        tipo_prodotto: bottega.tipo_prodotto,
        canali_collegati: scheda?.canali_collegati ?? [],
        n_da_approvare: scheda?.da_approvare.length ?? 0,
        n_in_corso: scheda?.in_corso.length ?? 0,
        prossima_scadenza: scheda?.da_approvare[0]?.entro_quando ?? null,
        prossima_campagna_id: scheda?.da_approvare[0]?.id ?? null,
      };
    },
  );
  righe.push({
    id: 5,
    email: "luca@pelletteriaferrero.it",
    nome: "Luca Ferrero",
    attivo: true,
    profilo_id: null,
    bottega: null,
    citta: null,
    tipo_prodotto: null,
    canali_collegati: [],
    n_da_approvare: 0,
    n_in_corso: 0,
    prossima_scadenza: null,
    prossima_campagna_id: null,
  });
  return Promise.resolve(righe);
}

export function schedaArtigianoEsempio(
  utenteId: number,
): Promise<SchedaArtigiano> {
  const scheda = SCHEDE_ESEMPIO[utenteId];
  if (scheda) return Promise.resolve(structuredClone(scheda));
  const bottega = profiliEsempio[utenteId];
  if (!bottega) throw new ApiErrore(404, "Artigiano non trovato.");
  return Promise.resolve({
    artigiano: {
      id: utenteId,
      email: ACCOUNT_ESEMPIO[utenteId]?.email ?? `${utenteId}@example.test`,
      nome: bottega.referente,
      attivo: ACCOUNT_ESEMPIO[utenteId]?.attivo ?? true,
    },
    profilo: null,
    canali_collegati: [],
    bozza: null,
    da_approvare: [],
    in_corso: [],
    chiuse: [],
    totale_chiuse: 0,
  });
}
