/**
 * Dati di esempio dello storico dell'AI, con la forma degli schemi di
 * brief-richieste §1.3. Si usano finché `GET /storico-ai` non è su `main`.
 */
import { ApiErrore } from "../http";
import type {
  ChiamataAIDettaglio,
  ChiamataAIRiga,
  FiltriStorico,
  NumeriAI,
  NumeriVersione,
  PaginaChiamateAI,
  TipoChiamata,
  ValutazioneAI,
  VotoAI,
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

// I voti dati nella sessione, per chiamata: si aggiungono ai voti di esempio.
const VOTATE = new Map<number, ValutazioneAI[]>();

function media(valori: number[]): number | null {
  return valori.length
    ? valori.reduce((somma, v) => somma + v, 0) / valori.length
    : null;
}

function voti(base: ChiamataAIRiga): ValutazioneAI[] {
  const iniziali: ValutazioneAI[] = base.voto_medio
    ? [
        {
          id: 1,
          utente_nome: "Chiara",
          voto: Math.round(base.voto_medio),
          nota: null,
          creata_il: base.creata_il,
        },
      ]
    : [];
  return [...iniziali, ...(VOTATE.get(base.id) ?? [])];
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
    valutazioni: voti(base),
  };
}

function numeri(filtri: FiltriStorico): NumeriAI {
  const righe = filtra(filtri).map((c) => ({
    ...c,
    voto_medio: media(voti(c).map((v) => v.voto)),
  }));
  const durate = righe.flatMap((c) =>
    c.durata_ms === null ? [] : [c.durata_ms],
  );
  const ordinate = [...durate].sort((a, b) => a - b);
  const sbagliate = (lista: ChiamataAIRiga[]) =>
    lista.filter((c) => c.esito !== "ok").length;
  const per = new Map<string, ChiamataAIRiga[]>();
  for (const c of righe) {
    const chiave = `${c.tipo}|${c.versione_prompt}`;
    per.set(chiave, [...(per.get(chiave) ?? []), c]);
  }
  const per_versione: NumeriVersione[] = [...per.values()].map((lista) => {
    const tempi = lista.flatMap((c) =>
      c.durata_ms === null ? [] : [c.durata_ms],
    );
    const media_tempi = media(tempi);
    return {
      tipo: lista[0].tipo,
      versione_prompt: lista[0].versione_prompt,
      chiamate: lista.length,
      tasso_errore: sbagliate(lista) / lista.length,
      durata_media_ms: media_tempi === null ? null : Math.round(media_tempi),
      costo_usd: lista.reduce((s, c) => s + Number(c.costo_usd), 0).toFixed(4),
      voto_medio: media(
        lista.flatMap((c) => (c.voto_medio === null ? [] : [c.voto_medio])),
      ),
    };
  });
  const ordine = ["analisi", "piano", "testo", "immagine"];
  per_versione.sort(
    (a, b) =>
      ordine.indexOf(a.tipo) - ordine.indexOf(b.tipo) ||
      (a.versione_prompt ?? "").localeCompare(b.versione_prompt ?? ""),
  );
  const media_durate = media(durate);
  return {
    chiamate: righe.length,
    costo_usd: righe.reduce((s, c) => s + Number(c.costo_usd), 0).toFixed(4),
    durata_media_ms: media_durate === null ? null : Math.round(media_durate),
    durata_p95_ms: ordinate.length
      ? ordinate[Math.max(0, Math.ceil(ordinate.length * 0.95) - 1)]
      : null,
    tasso_errore: righe.length ? sbagliate(righe) / righe.length : 0,
    voto_medio: media(voti_di(righe)),
    testi_approvati: 42,
    testi_approvati_come_ai: 31,
    modifiche_a_mano: 7,
    rigenerazioni_testo: 9,
    immagini_create: righe.filter(
      (c) => c.tipo === "immagine" && c.esito === "ok",
    ).length,
    immagini_non_create: righe.filter(
      (c) => c.tipo === "immagine" && c.esito !== "ok",
    ).length,
    immagini_rigenerate: 3,
    per_versione,
  };
}

function voti_di(righe: ChiamataAIRiga[]): number[] {
  return righe.flatMap((c) => voti(c).map((v) => v.voto));
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
  async numeri(filtri: FiltriStorico): Promise<NumeriAI> {
    return numeri(filtri);
  },
  async vota(id: number, voto: VotoAI): Promise<ValutazioneAI> {
    if (!TUTTE.some((c) => c.id === id))
      throw new ApiErrore(404, "Chiamata non trovata.");
    const nuovo: ValutazioneAI = {
      id: Date.now(),
      utente_nome: "Tu",
      voto: voto.voto,
      nota: voto.nota || null,
      creata_il: new Date().toISOString(),
    };
    VOTATE.set(id, [...(VOTATE.get(id) ?? []), nuovo]);
    return nuovo;
  },
  campagne: CAMPAGNE,
  modelli: Object.values(MODELLI),
  versioni: [...new Set(Object.values(VERSIONI).flat())],
};
