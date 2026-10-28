/**
 * Dati di esempio dello storico dell'AI, con la forma degli schemi di
 * brief-richieste §1.3. Si usano finché `GET /storico-ai` non è su `main`.
 */
import { ApiErrore } from "../http";
import type {
  ChiamataAIDettaglio,
  ChiamataAIRiga,
  FiltriStorico,
  PaginaChiamateAI,
  TipoChiamata,
} from "../storico";

const PER_PAGINA = 50;

const CAMPAGNE = [
  { id: 11, titolo: "Autunno in bottega", bottega: "Ceramiche Rossi" },
  { id: 12, titolo: "Natale a mano", bottega: "Legni di Anna" },
  { id: 13, titolo: "Porte aperte di novembre", bottega: "Ceramiche Rossi" },
];
const TIPI: TipoChiamata[] = ["analisi", "piano", "testo", "testo", "immagine"];
const MODELLI: Record<TipoChiamata, string> = {
  analisi: "gpt-visione-5",
  piano: "gpt-testo-5",
  testo: "gpt-testo-5-mini",
  immagine: "gpt-immagine-2",
};
const VERSIONI: Record<TipoChiamata, string[]> = {
  analisi: ["analisi_v2", "analisi_v3"],
  piano: ["piano_v2"],
  testo: ["post_v2", "post_v3"],
  immagine: ["immagine_v2"],
};
const ERRORI = ["temporaneo", "risposta", "rifiuto"];

function riga(n: number): ChiamataAIRiga {
  const tipo = TIPI[n % TIPI.length];
  const campagna = CAMPAGNE[n % CAMPAGNE.length];
  const versioni = VERSIONI[tipo];
  const fallita = n % 9 === 4;
  const data = new Date(Date.UTC(2026, 9, 27, 16, 40) - n * 37 * 60_000);
  return {
    id: 200 - n,
    creata_il: data.toISOString(),
    campagna_id: campagna.id,
    campagna_titolo: campagna.titolo,
    bottega: campagna.bottega,
    post_id: tipo === "testo" || tipo === "immagine" ? 300 + n : null,
    foto_id: tipo === "analisi" ? 40 + (n % 7) : null,
    tipo,
    modello_ai: MODELLI[tipo],
    versione_prompt: versioni[n % versioni.length],
    esito: fallita ? ERRORI[n % ERRORI.length] : "ok",
    durata_ms: fallita ? 1200 + n * 11 : 2400 + ((n * 373) % 9000),
    costo_usd: fallita ? "0" : (0.004 + (n % 6) * 0.011).toFixed(4),
    token_ingresso: fallita ? 900 : 1200 + ((n * 91) % 3000),
    token_uscita: fallita ? null : 150 + ((n * 53) % 700),
    voto_medio: !fallita && n % 4 === 0 ? 3 + (n % 3) * 0.5 : null,
  };
}

const TUTTE: ChiamataAIRiga[] = Array.from({ length: 120 }, (_, n) => riga(n));

function giornoRoma(iso: string): string {
  return new Date(iso).toLocaleDateString("sv-SE", {
    timeZone: "Europe/Rome",
  });
}

function filtra(filtri: FiltriStorico): ChiamataAIRiga[] {
  return TUTTE.filter(
    (c) =>
      (!filtri.campagna_id || c.campagna_id === Number(filtri.campagna_id)) &&
      (!filtri.tipo || c.tipo === filtri.tipo) &&
      (!filtri.modello || c.modello_ai === filtri.modello) &&
      (!filtri.versione_prompt ||
        c.versione_prompt === filtri.versione_prompt) &&
      (!filtri.esito || c.esito === filtri.esito) &&
      (!filtri.dal || giornoRoma(c.creata_il) >= filtri.dal) &&
      (!filtri.al || giornoRoma(c.creata_il) <= filtri.al),
  );
}

function dettaglio(base: ChiamataAIRiga): ChiamataAIDettaglio {
  const fallita = base.esito !== "ok";
  return {
    ...base,
    richiesta: {
      bottega: { nome: base.bottega, tono: "caldo e semplice", forma: "tu" },
      campagna: { titolo: base.campagna_titolo, obiettivo: "far conoscere" },
      ...(base.foto_id ? { foto: `<foto ${base.foto_id}>` } : {}),
      ...(base.tipo === "testo"
        ? { altri_post: ["Nel laboratorio odora di terra bagnata."] }
        : {}),
    },
    risposta: fallita
      ? null
      : base.tipo === "testo"
      ? "Ogni tazza nasce da due mani e un po' di pazienza. Passa a vederle da vicino."
      : '{"esito": "ok"}',
    errore: fallita ? "Il provider non ha risposto in tempo." : null,
    tentativo: fallita ? 2 : 1,
    valutazioni: base.voto_medio
      ? [
          {
            id: 1,
            utente_nome: "Chiara",
            voto: Math.round(base.voto_medio),
            nota: null,
            creata_il: base.creata_il,
          },
        ]
      : [],
  };
}

export const esempiStorico = {
  async elenco(
    filtri: FiltriStorico,
    pagina: number,
  ): Promise<PaginaChiamateAI> {
    const tutte = filtra(filtri);
    const da = (pagina - 1) * PER_PAGINA;
    return {
      voci: tutte.slice(da, da + PER_PAGINA),
      totale: tutte.length,
      pagina,
      per_pagina: PER_PAGINA,
    };
  },
  async dettaglio(id: number): Promise<ChiamataAIDettaglio> {
    const base = TUTTE.find((c) => c.id === id);
    if (!base) throw new ApiErrore(404, "Chiamata non trovata.");
    return dettaglio(base);
  },
  campagne: CAMPAGNE,
  modelli: Object.values(MODELLI),
  versioni: [...new Set(Object.values(VERSIONI).flat())],
};
