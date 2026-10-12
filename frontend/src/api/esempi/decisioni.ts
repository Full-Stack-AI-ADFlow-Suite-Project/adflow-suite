/**
 * Dati di esempio delle decisioni sulla campagna e di Campagne da approvare
 * (plan §3, spec R-18, R-32, R-33, R-34, R-38). Lavorano sugli stessi
 * magazzini di `esempi/campagne.ts` e `esempi/revisione.ts`, così Vedi campagna
 * rilegge subito il risultato.
 */
import { ApiErrore } from "../http";
import type { CampagnaDettaglio } from "../campagne";
import type { CampagnaDaApprovare, MotivoRespinta } from "../decisioni";
import type { PostVista, Uscita } from "../revisione";
import { sessioneEsempio } from "./accesso";
import { esempiCampagne, leggiCampagna, salvaCampagna } from "./campagne";

const CHIAVE = "adflow_esempi_revisione";
const MARGINE_MINUTI = 15;

const STATI_DA_APPROVARE = [
  "inviata",
  "in_generazione",
  "piano_da_rivedere",
  "generazione_fallita",
  "in_revisione",
];

type Magazzino = Record<number, { uscite: Uscita[] }>;

function leggi(): Magazzino {
  const grezzo = localStorage.getItem(CHIAVE);
  if (!grezzo) return {};
  try {
    return JSON.parse(grezzo) as Magazzino;
  } catch {
    return {};
  }
}

function scrivi(dati: Magazzino): void {
  localStorage.setItem(CHIAVE, JSON.stringify(dati));
}

function operatore(): void {
  const utente = sessioneEsempio();
  if (!utente || (utente.ruolo !== "operatore" && utente.ruolo !== "admin"))
    throw new ApiErrore(403, "Non hai i permessi per questa operazione.");
}

function postDi(dati: Magazzino, campagnaId: number): PostVista[] {
  return (dati[campagnaId]?.uscite ?? []).flatMap((u) => u.post);
}

/** Registra una decisione sulla campagna, come `registra_decisione()`. */
function decisione(
  c: CampagnaDettaglio,
  esito: string,
  extra: {
    motivo?: string | null;
    nota?: string | null;
    canale?: string | null;
    post_id?: number | null;
  } = {},
): void {
  const id = (c.decisioni ?? []).reduce((m, d) => Math.max(m, d.id), 0) + 1;
  (c.decisioni ??= []).push({
    id,
    esito,
    canale: extra.canale ?? null,
    post_id: extra.post_id ?? null,
    motivo: extra.motivo ?? null,
    nota: extra.nota ?? null,
  });
}

function dopoInvio(c: CampagnaDettaglio): void {
  if (c.stato === "bozza")
    throw new ApiErrore(409, "La campagna è ancora una bozza.");
}

function nota(testo: string): string {
  const pulita = testo.trim();
  if (!pulita) throw new ApiErrore(422, "Scrivi la nota.");
  return pulita;
}

function inArretrato(p: PostVista, adesso: string): boolean {
  return p.stato === "approvato" && p.data_ora < adesso;
}

export const esempiDecisioni = {
  /** CA-69: conteggi, entro quando e ultima nota, dalla più urgente. */
  async daApprovare(): Promise<CampagnaDaApprovare[]> {
    operatore();
    const dati = leggi();
    const righe = (await esempiCampagne.elenco())
      .filter((c) => STATI_DA_APPROVARE.includes(c.stato))
      .map((c): CampagnaDaApprovare => {
        const post = postDi(dati, c.id);
        const daApp = post.filter((p) => p.stato === "da_approvare");
        const riempitivi: Record<string, number> = {};
        for (const p of post)
          if (p.riempitivo)
            riempitivi[p.canale] = (riempitivi[p.canale] ?? 0) + 1;
        const date = daApp.map((p) => p.data_ora).sort();
        const note = (leggiCampagna(c.id).decisioni ?? []).filter(
          (d) => d.esito === "nota",
        );
        return {
          ...c,
          conteggi: {
            totale: post.length,
            da_approvare: daApp.length,
            da_rivedere: daApp.filter((p) => p.da_rivedere).length,
            riempitivi,
          },
          entro_quando: date[0] ?? `${c.inizio}T00:00`,
          ultima_nota: note[note.length - 1]?.nota ?? null,
        };
      });
    return righe.sort((a, b) =>
      (a.entro_quando ?? "").localeCompare(b.entro_quando ?? ""),
    );
  },

  /** CA-23: stato invariato, decisione `nota`, nessuna email. */
  async nota(campagnaId: number, testo: string): Promise<void> {
    operatore();
    const c = leggiCampagna(campagnaId);
    dopoInvio(c);
    decisione(c, "nota", { nota: nota(testo) });
    salvaCampagna(c);
  },

  /** CA-24, CA-25: motivo e nota obbligatori, post scartati, foto segnate. */
  async respingi(
    campagnaId: number,
    motivo: MotivoRespinta,
    testo: string,
    fotoSegnate: number[],
  ): Promise<void> {
    operatore();
    const c = leggiCampagna(campagnaId);
    if (!["in_revisione", "piano_da_rivedere"].includes(c.stato))
      throw new ApiErrore(
        409,
        "Si respinge solo una campagna in revisione o con il piano da rivedere.",
      );
    if (motivo !== "foto" && motivo !== "altro")
      throw new ApiErrore(422, "Scegli il motivo.");
    const notaPulita = nota(testo);
    const sue = new Set(c.gruppi.flatMap((g) => g.foto.map((f) => f.id)));
    if (fotoSegnate.some((f) => !sue.has(f)))
      throw new ApiErrore(422, "Una foto segnata non è di questa campagna.");
    const dati = leggi();
    for (const p of postDi(dati, campagnaId))
      if (p.stato === "da_approvare") p.stato = "scartato";
    c.stato = "respinta";
    c.chiusa_il = new Date().toISOString();
    c.esito_respinta = {
      motivo,
      nota: notaPulita,
      foto_segnate: fotoSegnate,
    };
    decisione(c, "respinta", { motivo, nota: notaPulita });
    salvaCampagna(c);
    scrivi(dati);
  },

  /** CA-53: i post del canale scartati; mai l'ultimo canale. */
  async togliCanale(
    campagnaId: number,
    canale: string,
    testo: string,
  ): Promise<void> {
    operatore();
    const c = leggiCampagna(campagnaId);
    if (
      !["generazione_fallita", "piano_da_rivedere", "in_revisione"].includes(
        c.stato,
      )
    )
      throw new ApiErrore(
        409,
        "Il canale si toglie solo da una campagna ferma, con il piano da rivedere o in revisione.",
      );
    const rimasti = (c.canali ?? []).filter(
      (x) => !(c.canali_tolti ?? []).includes(x),
    );
    if (!rimasti.includes(canale))
      throw new ApiErrore(422, "Il canale non è tra quelli della campagna.");
    if (rimasti.length <= 1)
      throw new ApiErrore(409, "Non si può togliere l'ultimo canale.");
    const notaPulita = nota(testo);
    const dati = leggi();
    for (const p of postDi(dati, campagnaId))
      if (p.canale === canale && p.stato === "da_approvare")
        p.stato = "scartato";
    c.canali_tolti = [...(c.canali_tolti ?? []), canale];
    if (c.stato === "generazione_fallita") c.stato = "inviata";
    decisione(c, "canale_tolto", { canale, nota: notaPulita });
    salvaCampagna(c);
    scrivi(dati);
  },

  /** CA-32: attiva → sospesa. */
  async sospendi(campagnaId: number): Promise<void> {
    operatore();
    const c = leggiCampagna(campagnaId);
    if (c.stato !== "attiva")
      throw new ApiErrore(409, "Si sospende solo una campagna attiva.");
    c.stato = "sospesa";
    decisione(c, "sospesa");
    salvaCampagna(c);
  },

  /** CA-32: gli arretrati scelti escono adesso, gli altri diventano annullati. */
  async riattiva(campagnaId: number, pubblicaOra: number[]): Promise<void> {
    operatore();
    const c = leggiCampagna(campagnaId);
    if (c.stato !== "sospesa")
      throw new ApiErrore(409, "Si riattiva solo una campagna sospesa.");
    const adesso = new Date().toISOString();
    const dati = leggi();
    const arretrati = postDi(dati, campagnaId).filter((p) =>
      inArretrato(p, adesso),
    );
    const ids = new Set(arretrati.map((p) => p.post_id));
    if (pubblicaOra.some((id) => !ids.has(id)))
      throw new ApiErrore(422, "Un post scelto non è tra quelli in arretrato.");
    for (const p of arretrati)
      if (!pubblicaOra.includes(p.post_id)) p.stato = "annullato";
    c.stato = "attiva";
    decisione(c, "riattivata");
    salvaCampagna(c);
    scrivi(dati);
  },

  /** CA-32: i post approvati diventano annullati. */
  async annulla(campagnaId: number): Promise<void> {
    operatore();
    const c = leggiCampagna(campagnaId);
    if (!["attiva", "sospesa"].includes(c.stato))
      throw new ApiErrore(
        409,
        "Si annulla solo una campagna attiva o sospesa.",
      );
    const dati = leggi();
    for (const p of postDi(dati, campagnaId))
      if (p.stato === "approvato") p.stato = "annullato";
    c.stato = "annullata";
    c.chiusa_il = new Date().toISOString();
    decisione(c, "annullata");
    salvaCampagna(c);
    scrivi(dati);
  },

  /** CA-67: un post fallito torna approvato, dentro il periodo e nel futuro. */
  async riprogramma(postId: number, dataOra: string): Promise<void> {
    operatore();
    const dati = leggi();
    const trovato = Object.entries(dati)
      .flatMap(([id, r]) =>
        r.uscite.flatMap((u) =>
          u.post.map((p) => ({ campagnaId: Number(id), post: p })),
        ),
      )
      .find((x) => x.post.post_id === postId);
    if (!trovato) throw new ApiErrore(404, "Post non trovato.");
    const { campagnaId, post } = trovato;
    const c = leggiCampagna(campagnaId);
    if (post.stato !== "fallito")
      throw new ApiErrore(409, "Si riprogramma solo un post fallito.");
    if (!["attiva", "sospesa"].includes(c.stato))
      throw new ApiErrore(
        409,
        "Si riprogramma solo in una campagna attiva o sospesa.",
      );
    const nuova = new Date(dataOra);
    if (Number.isNaN(nuova.getTime()))
      throw new ApiErrore(422, "Scegli data e ora.");
    if (nuova.getTime() < Date.now() + MARGINE_MINUTI * 60 * 1000)
      throw new ApiErrore(
        422,
        `La nuova data deve essere almeno ${MARGINE_MINUTI} minuti da adesso.`,
      );
    const giorno = `${nuova.getFullYear()}-${String(
      nuova.getMonth() + 1,
    ).padStart(2, "0")}-${String(nuova.getDate()).padStart(2, "0")}`;
    if (giorno < c.inizio || giorno > c.fine)
      throw new ApiErrore(
        422,
        `La nuova data deve cadere dentro il periodo della campagna (dal ${c.inizio} al ${c.fine}).`,
      );
    post.stato = "approvato";
    post.data_ora = dataOra;
    decisione(c, "riprogrammato", { post_id: postId });
    salvaCampagna(c);
    scrivi(dati);
  },
};
