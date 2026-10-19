/**
 * Dati di esempio degli interventi sul post (plan §3, spec R-03, R-16, R-30,
 * R-31, R-36).
 * Lavorano sullo stesso magazzino di `esempi/revisione.ts` (stessa chiave di
 * localStorage), così Vedi campagna rilegge subito il risultato. La
 * rigenerazione accende l'intervento in corso e, dopo pochi secondi, fa nascere
 * la nuova versione, come farebbe il job `rigenera_post`.
 */
import { ApiErrore } from "../http";
import type {
  ErroreValidazione,
  FotoPossibile,
  Intervento,
  PostVista,
  Uscita,
} from "../revisione";
import type { ModalitaRigenerazione } from "../interventi";
import { sessioneEsempio, USA_ESEMPI } from "./accesso";
import { leggiCampagna, salvaCampagna } from "./campagne";

const CHIAVE = "adflow_esempi_revisione";
const CHIAVE_RICHIESTE = "adflow_esempi_interventi_richieste";
const ATTESA_RIGENERAZIONE_MS = 3000;
const MAX_RIGENERAZIONI = 3;
const SCADENZA_INTERVENTO_MS = 10 * 60 * 1000;
const RIGENERAZIONI = ["rigenera_totale", "rigenera_da_proposta"];
const MARGINE_MINUTI = 15;

/** (stato della campagna, stato del post) → interventi ammessi (spec R-16). */
const AMMESSI: Record<string, Intervento[]> = {
  "in_revisione|da_approvare": [
    "modifica",
    "rigenera",
    "cambia_foto",
    "sposta",
  ],
  "attiva|approvato": ["modifica", "cambia_foto", "sposta", "annulla"],
  "sospesa|approvato": ["modifica", "cambia_foto", "sposta", "annulla"],
  "attiva|fallito": ["riprogramma"],
  "sospesa|fallito": ["riprogramma"],
};
/** Stati dei post che tengono occupata una foto sul loro canale (costituzione §1.9). */
const STATI_CHE_USANO_LA_FOTO = [
  "da_approvare",
  "approvato",
  "pubblicato",
  "fallito",
];

/** Limiti della scheda del canale (spec R-21): editoriali = avviso, piattaforma = blocco. */
const SCHEDE: Record<
  string,
  {
    max_caratteri: number;
    max_hashtag: number;
    limite_caratteri: number;
    limite_hashtag: number;
  }
> = {
  facebook: {
    max_caratteri: 500,
    max_hashtag: 3,
    limite_caratteri: 5000,
    limite_hashtag: 30,
  },
  instagram: {
    max_caratteri: 600,
    max_hashtag: 5,
    limite_caratteri: 2200,
    limite_hashtag: 30,
  },
};

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

/** Testo proposto e nota di una rigenerazione, finché il job non la esegue. */
type Richieste = Record<
  number,
  { testo_proposto: string | null; nota: string | null }
>;

function leggiRichieste(): Richieste {
  try {
    return JSON.parse(
      localStorage.getItem(CHIAVE_RICHIESTE) ?? "{}",
    ) as Richieste;
  } catch {
    return {};
  }
}

function operatore() {
  const utente = sessioneEsempio();
  if (!utente || (utente.ruolo !== "operatore" && utente.ruolo !== "admin"))
    throw new ApiErrore(403, "Non hai i permessi per questa operazione.");
  return utente;
}

function trova(
  dati: Magazzino,
  postId: number,
): { campagnaId: number; post: PostVista } {
  for (const [id, r] of Object.entries(dati))
    for (const u of r.uscite)
      for (const p of u.post)
        if (p.post_id === postId) return { campagnaId: Number(id), post: p };
  throw new ApiErrore(404, "Post non trovato.");
}

function interventoAttivo(post: PostVista, adesso: number): boolean {
  if (!post.intervento_in_corso) return false;
  if (!post.intervento_dal) return true;
  return (
    adesso - new Date(post.intervento_dal).getTime() < SCADENZA_INTERVENTO_MS
  );
}

function rigenerazioniFatte(post: PostVista): number {
  return post.versioni.filter((v) => RIGENERAZIONI.includes(v.tipo_intervento))
    .length;
}

/**
 * Gli interventi ammessi adesso sul post, come `interventi_ammessi()` del
 * backend (spec R-16): la tabella per stato di campagna e di post, meno ciò
 * che il singolo post non permette. Esportata: Vedi campagna la usa per
 * riempire `interventi` di ogni post.
 */
export function interventiAmmessi(
  post: PostVista,
  statoCampagna: string,
  adesso: number,
): Intervento[] {
  let ammessi = [...(AMMESSI[`${statoCampagna}|${post.stato}`] ?? [])];
  if (!ammessi.length || interventoAttivo(post, adesso)) return [];
  if (
    post.stato === "approvato" &&
    new Date(post.data_ora).getTime() < adesso + MARGINE_MINUTI * 60 * 1000
  )
    return [];
  if (!post.versione_corrente)
    ammessi = ammessi.filter(
      (i) => i !== "modifica" && i !== "rigenera" && i !== "cambia_foto",
    );
  if (post.riempitivo) ammessi = ammessi.filter((i) => i !== "cambia_foto");
  if (rigenerazioniFatte(post) >= MAX_RIGENERAZIONI)
    ammessi = ammessi.filter((i) => i !== "rigenera");
  return ammessi;
}

/** Il primo motivo per cui l'intervento non è ammesso (stessi messaggi del backend, 409). */
function motivoNonAmmesso(
  post: PostVista,
  statoCampagna: string,
  intervento: Intervento,
  adesso: number,
): string {
  const previsti = AMMESSI[`${statoCampagna}|${post.stato}`] ?? [];
  if (previsti.includes(intervento)) {
    if (interventoAttivo(post, adesso))
      return "Sul post c'è un intervento in corso.";
    if (
      post.stato === "approvato" &&
      new Date(post.data_ora).getTime() < adesso + MARGINE_MINUTI * 60 * 1000
    )
      return `Il post esce tra meno di ${MARGINE_MINUTI} minuti: non si tocca più.`;
    if (intervento === "cambia_foto" && post.riempitivo)
      return "Un post con un'immagine AI non cambia foto.";
    if (
      intervento === "rigenera" &&
      rigenerazioniFatte(post) >= MAX_RIGENERAZIONI
    )
      return "Le 3 rigenerazioni del testo sono finite: resta la modifica a mano.";
    if (!post.versione_corrente) return "Il post non ha ancora un testo.";
  }
  return `Questo intervento non è ammesso: la campagna è «${statoCampagna}», il post è «${post.stato}».`;
}

/** Vero se l'intervento è ammesso adesso, altrimenti 409 (come `verifica_intervento()`). */
function ammesso(
  dati: Magazzino,
  postId: number,
  intervento: Intervento,
): { campagnaId: number; post: PostVista } {
  const trovato = trova(dati, postId);
  const stato = leggiCampagna(trovato.campagnaId).stato;
  const adesso = Date.now();
  if (!interventiAmmessi(trovato.post, stato, adesso).includes(intervento))
    throw new ApiErrore(
      409,
      motivoNonAmmesso(trovato.post, stato, intervento, adesso),
    );
  return trovato;
}

/** La spunta «va bene» resta solo in revisione, su un post da approvare (R-30; congelata). */
function inRevisione(dati: Magazzino, postId: number): PostVista {
  const { campagnaId, post } = trova(dati, postId);
  if (leggiCampagna(campagnaId).stato !== "in_revisione")
    throw new ApiErrore(409, "La campagna non è in revisione.");
  if (post.stato !== "da_approvare")
    throw new ApiErrore(409, "Il post non è da approvare.");
  if (interventoAttivo(post, Date.now()))
    throw new ApiErrore(409, "Sul post c'è un intervento in corso.");
  return post;
}

/** Registra una decisione sulla campagna, come `registra_decisione()`. */
function registraDecisione(
  campagnaId: number,
  esito: string,
  postId: number,
  nota: string,
): void {
  const c = leggiCampagna(campagnaId);
  (c.decisioni ??= []).push({
    id: (c.decisioni ?? []).reduce((m, d) => Math.max(m, d.id), 0) + 1,
    esito,
    canale: null,
    post_id: postId,
    motivo: null,
    nota,
  });
  salvaCampagna(c);
}

/** Data e ora nel formato delle note: gg/mm/aaaa hh:mm, Europe/Rome. */
function dataRoma(iso: string): string {
  return new Date(iso)
    .toLocaleString("it-IT", {
      timeZone: "Europe/Rome",
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    })
    .replace(",", "");
}

function senzaCancelletto(hashtag: string[]): string[] {
  return hashtag
    .map((h) => h.trim().replace(/^#+/, "").trim())
    .filter((h) => h.length > 0);
}

/** Un validatore ridotto (R-09): prezzi, testo vuoto, limiti della scheda del canale. */
function valida(
  testo: string,
  hashtag: string[],
  canale: string,
): ErroreValidazione[] {
  const scheda = SCHEDE[canale];
  const errori: ErroreValidazione[] = [];
  if (!testo)
    errori.push({
      livello: "blocco",
      regola: "testo_vuoto",
      messaggio: "Il testo è vuoto.",
    });
  if (/\d+\s?€|€\s?\d+/.test(testo))
    errori.push({
      livello: "blocco",
      regola: "prezzi_o_premi",
      messaggio: "Prezzo che non è nei dati della bottega.",
    });
  if (!scheda) return errori;
  const pubblicato = [testo, ...hashtag.map((h) => `#${h}`)].join(" ");
  if (pubblicato.length > scheda.limite_caratteri)
    errori.push({
      livello: "blocco",
      regola: "limite_caratteri",
      messaggio: `Testo e hashtag sono ${pubblicato.length} caratteri: ${canale} ne accetta al massimo ${scheda.limite_caratteri}.`,
    });
  if (hashtag.length > scheda.limite_hashtag)
    errori.push({
      livello: "blocco",
      regola: "limite_hashtag",
      messaggio: `Gli hashtag sono ${hashtag.length}: ${canale} ne accetta al massimo ${scheda.limite_hashtag}.`,
    });
  if (testo.length > scheda.max_caratteri)
    errori.push({
      livello: "avviso",
      regola: "max_caratteri",
      messaggio: `Il testo è di ${testo.length} caratteri: su ${canale} conviene restare entro ${scheda.max_caratteri}.`,
    });
  if (hashtag.length > scheda.max_hashtag)
    errori.push({
      livello: "avviso",
      regola: "max_hashtag",
      messaggio: `Gli hashtag sono ${hashtag.length}: su ${canale} conviene restare entro ${scheda.max_hashtag}.`,
    });
  return errori;
}

/** Aggiunge la versione e azzera la spunta, come ogni nuova versione (R-30). */
function nuovaVersione(
  post: PostVista,
  dati: {
    testo: string;
    hashtag: string[];
    autore_id: number | null;
    tipo_intervento: string;
    testo_proposto?: string | null;
    nota?: string | null;
    errori: ErroreValidazione[];
  },
): void {
  const corrente = post.versione_corrente;
  if (!corrente) return;
  const numero = Math.max(...post.versioni.map((v) => v.numero), 0) + 1;
  const versione = {
    ...corrente,
    id: Math.max(...post.versioni.map((v) => v.id), 0) + 1,
    numero,
    testo: dati.testo,
    hashtag: dati.hashtag,
    autore_id: dati.autore_id,
    tipo_intervento: dati.tipo_intervento,
    testo_proposto: dati.testo_proposto ?? null,
    nota: dati.nota ?? null,
    provider_ai: dati.autore_id == null ? corrente.provider_ai : null,
    modello_ai: dati.autore_id == null ? corrente.modello_ai : null,
    versione_prompt: dati.autore_id == null ? corrente.versione_prompt : null,
    errori_validazione: dati.errori,
    creata_il: new Date().toISOString(),
  };
  post.versioni = [...post.versioni, versione];
  post.versione_corrente = versione;
  post.da_rivedere = dati.errori.some((e) => e.livello === "blocco");
  post.controllato_da = null;
  post.controllato_il = null;
}

/** Il job `rigenera_post`: nuovo testo, stesse foto, ciclo contato, intervento spento. */
function completaRigenerazione(postId: number): void {
  const dati = leggi();
  let trovato: { campagnaId: number; post: PostVista };
  try {
    trovato = trova(dati, postId);
  } catch {
    return;
  }
  const { campagnaId, post } = trovato;
  const tipo = post.intervento_in_corso;
  if (!tipo || !post.versione_corrente) return;
  if (
    leggiCampagna(campagnaId).stato !== "in_revisione" ||
    post.stato !== "da_approvare"
  ) {
    post.intervento_in_corso = null;
    post.intervento_dal = null;
    scrivi(dati);
    return;
  }
  const corrente = post.versione_corrente;
  const richieste = leggiRichieste();
  const proposto = richieste[postId]?.testo_proposto ?? null;
  const nota = richieste[postId]?.nota ?? null;
  delete richieste[postId];
  localStorage.setItem(CHIAVE_RICHIESTE, JSON.stringify(richieste));
  const testo =
    tipo === "rigenera_da_proposta" && proposto
      ? proposto
      : `${corrente.testo
          .split("\n")[0]
          .replace(/ \(riscritto.*\)$/, "")} (riscritto, versione ${
          post.versioni.length + 1
        })`;
  nuovaVersione(post, {
    testo,
    hashtag: corrente.hashtag,
    autore_id: null,
    tipo_intervento: tipo,
    testo_proposto: proposto,
    nota,
    errori: valida(testo, senzaCancelletto(corrente.hashtag), post.canale),
  });
  post.intervento_in_corso = null;
  post.intervento_dal = null;
  scrivi(dati);
}

/** Dopo un ricaricamento della pagina le rigenerazioni a metà si chiudono o si riprogrammano. */
function riprendiRigenerazioni(): void {
  const dati = leggi();
  const adesso = Date.now();
  for (const r of Object.values(dati))
    for (const u of r.uscite)
      for (const p of u.post) {
        if (!p.intervento_in_corso || !p.intervento_dal) continue;
        const trascorso = adesso - new Date(p.intervento_dal).getTime();
        if (trascorso >= SCADENZA_INTERVENTO_MS) continue;
        setTimeout(
          () => completaRigenerazione(p.post_id),
          Math.max(ATTESA_RIGENERAZIONE_MS - trascorso, 0),
        );
      }
}

if (USA_ESEMPI) riprendiRigenerazioni();

export const esempiInterventi = {
  /** CA-64: nuova versione `modifica_operatore` con l'autore, validata. */
  async modifica(
    postId: number,
    testo: string,
    hashtag: string[],
  ): Promise<void> {
    const utente = operatore();
    const dati = leggi();
    const { post } = ammesso(dati, postId, "modifica");
    const corrente = post.versione_corrente;
    if (!corrente) throw new ApiErrore(409, "Il post non ha ancora un testo.");
    const nuovoTesto = testo.trim();
    const nuoviHashtag = senzaCancelletto(hashtag);
    if (
      nuovoTesto === corrente.testo.trim() &&
      nuoviHashtag.join(" ") === senzaCancelletto(corrente.hashtag).join(" ")
    )
      throw new ApiErrore(
        422,
        "Il testo e gli hashtag sono uguali a quelli di prima.",
      );
    const errori = valida(nuovoTesto, nuoviHashtag, post.canale);
    const blocchi = errori.filter((e) => e.livello === "blocco");
    if (blocchi.length)
      throw new ApiErrore(422, blocchi.map((b) => b.messaggio).join(" "));
    nuovaVersione(post, {
      testo: nuovoTesto,
      hashtag: nuoviHashtag,
      autore_id: utente.id,
      tipo_intervento: "modifica_operatore",
      errori,
    });
    scrivi(dati);
  },

  /** CA-65: chi e quando; un post da rivedere non si spunta. */
  async controllato(postId: number, valore: boolean): Promise<void> {
    const utente = operatore();
    const dati = leggi();
    const post = inRevisione(dati, postId);
    if (valore && post.da_rivedere)
      throw new ApiErrore(
        409,
        "Un post da rivedere non si può segnare come controllato.",
      );
    post.controllato_da = valore ? utente.id : null;
    post.controllato_il = valore ? new Date().toISOString() : null;
    scrivi(dati);
  },

  /** CA-26…CA-28: da zero o da testo proposto, al massimo 3 cicli. */
  async rigenera(
    postId: number,
    modalita: ModalitaRigenerazione,
    testoProposto: string | null,
    nota: string | null,
  ): Promise<void> {
    operatore();
    const dati = leggi();
    const { post } = ammesso(dati, postId, "rigenera");
    const proposto = (testoProposto ?? "").trim();
    if (modalita === "da_proposta" && !proposto)
      throw new ApiErrore(422, "Scrivi il testo da cui partire.");
    post.intervento_in_corso =
      modalita === "totale" ? "rigenera_totale" : "rigenera_da_proposta";
    post.intervento_dal = new Date().toISOString();
    localStorage.setItem(
      CHIAVE_RICHIESTE,
      JSON.stringify({
        ...leggiRichieste(),
        [postId]: {
          testo_proposto: modalita === "da_proposta" ? proposto : null,
          nota: nota?.trim() || null,
        },
      }),
    );
    scrivi(dati);
    setTimeout(() => completaRigenerazione(postId), ATTESA_RIGENERAZIONE_MS);
  },

  /** CA-71: le foto del gruppo dell'uscita con cui cambiare quella del post. */
  async fotoPossibili(postId: number): Promise<FotoPossibile[]> {
    operatore();
    const dati = leggi();
    const { campagnaId, post } = ammesso(dati, postId, "cambia_foto");
    const uscita = dati[campagnaId].uscite.find((u) => u.post.includes(post));
    const gruppoId = uscita?.gruppo?.id;
    if (gruppoId == null)
      throw new ApiErrore(409, "Un post con un'immagine AI non cambia foto.");
    const occupate = new Set(
      post.versione_corrente?.foto.map((f) => f.foto_id) ?? [],
    );
    for (const altro of dati[campagnaId].uscite.flatMap((u) => u.post))
      if (
        altro !== post &&
        altro.canale === post.canale &&
        STATI_CHE_USANO_LA_FOTO.includes(altro.stato)
      )
        for (const f of altro.versione_corrente?.foto ?? [])
          occupate.add(f.foto_id);
    const gruppo = leggiCampagna(campagnaId).gruppi.find(
      (g) => g.id === gruppoId,
    );
    return (gruppo?.foto ?? [])
      .filter((f) => f.origine === "caricata" && !occupate.has(f.id))
      .map((f, i) => ({
        foto_id: f.id,
        punteggio: Math.round((0.9 - 0.05 * i) * 100) / 100,
        analizzata: true,
      }))
      .sort(
        (a, b) =>
          (b.punteggio ?? 0) - (a.punteggio ?? 0) || a.foto_id - b.foto_id,
      );
  },

  /** CA-71: versione `cambio_foto` con lo stesso testo; la foto scelta prende il primo posto. */
  async cambiaFoto(postId: number, fotoId: number): Promise<void> {
    const utente = operatore();
    const possibili = await esempiInterventi.fotoPossibili(postId);
    if (!possibili.some((f) => f.foto_id === fotoId))
      throw new ApiErrore(
        422,
        "Questa foto non si può usare per il post: deve essere del gruppo dell'uscita, idonea o arrivata con una richiesta, e non già su questo canale.",
      );
    const dati = leggi();
    const { post } = trova(dati, postId);
    const corrente = post.versione_corrente;
    if (!corrente) return;
    const primo = Math.min(...corrente.foto.map((f) => f.posizione));
    const rivedere = post.da_rivedere;
    nuovaVersione(post, {
      testo: corrente.testo,
      hashtag: corrente.hashtag,
      autore_id: utente.id,
      tipo_intervento: "cambio_foto",
      errori: Array.isArray(corrente.errori_validazione)
        ? (corrente.errori_validazione as ErroreValidazione[])
        : [],
    });
    // Cambiare la foto non cambia l'indicatore «da rivedere» (R-36).
    post.da_rivedere = rivedere;
    const nuova = post.versione_corrente;
    if (nuova)
      nuova.foto = corrente.foto.map((f) =>
        f.posizione === primo ? { ...f, foto_id: fotoId } : f,
      );
    scrivi(dati);
  },

  /** CA-72: nuova data e ora, dentro il periodo, dopo il margine e diversa da quella di prima. */
  async sposta(postId: number, dataOra: string): Promise<void> {
    operatore();
    const dati = leggi();
    const { campagnaId, post } = ammesso(dati, postId, "sposta");
    const c = leggiCampagna(campagnaId);
    const nuova = new Date(dataOra);
    if (Number.isNaN(nuova.getTime()))
      throw new ApiErrore(422, "Scegli data e ora.");
    if (nuova.getTime() < Date.now() + MARGINE_MINUTI * 60 * 1000)
      throw new ApiErrore(
        422,
        `La nuova data deve essere almeno ${MARGINE_MINUTI} minuti dopo adesso.`,
      );
    const giorno = `${nuova.getFullYear()}-${String(
      nuova.getMonth() + 1,
    ).padStart(2, "0")}-${String(nuova.getDate()).padStart(2, "0")}`;
    if (giorno < c.inizio || giorno > c.fine)
      throw new ApiErrore(
        422,
        "La nuova data deve cadere nel periodo della campagna.",
      );
    if (nuova.getTime() === new Date(post.data_ora).getTime())
      throw new ApiErrore(422, "La nuova data è uguale a quella di prima.");
    const prima = post.data_ora;
    post.data_ora = nuova.toISOString();
    post.controllato_da = null;
    post.controllato_il = null;
    registraDecisione(
      campagnaId,
      "riprogrammato",
      postId,
      `Spostato dal ${dataRoma(prima)} al ${dataRoma(post.data_ora)}`,
    );
    scrivi(dati);
  },

  /** CA-85: il post approvato non esce più; la nota è obbligatoria. */
  async annullaPost(postId: number, nota: string): Promise<void> {
    operatore();
    const pulita = nota.trim();
    if (!pulita)
      throw new ApiErrore(422, "Per annullare un post serve la nota.");
    const dati = leggi();
    const { campagnaId, post } = ammesso(dati, postId, "annulla");
    post.stato = "annullato";
    registraDecisione(campagnaId, "post_annullato", postId, pulita);
    scrivi(dati);
  },
};
