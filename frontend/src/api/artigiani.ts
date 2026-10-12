import { ApiErrore, richiesta } from "./http";
import {
  canaliEsempio,
  leggiProfiloEsempio,
  salvaProfiloEsempio,
  USA_ESEMPI,
} from "./esempi/artigiani";

export interface CanaleCollegato {
  canale: string;
  collegato: boolean;
}
export type Json =
  | string
  | number
  | boolean
  | null
  | Json[]
  | { [chiave: string]: Json };
export interface DatiProfilo {
  nome: string;
  referente: string;
  citta: string;
  tipo_prodotto: string;
  clienti_ideali: string;
  obiettivo: string;
  canali: string[];
  anni_attivita: number | null;
  sito: string | null;
  storia: string | null;
  origine: string | null;
  valori: string[] | null;
  gamma: string | null;
  fascia_prezzo: string | null;
  stagionalita: string | null;
  zona: string | null;
  tono: string[] | null;
  cortesia: string | null;
  vincoli: string | null;
  frequenza: string | null;
  orari: Record<string, Json> | Json[] | null;
  social_esistenti: Record<string, Json> | null;
  foto_policy: Record<string, Json> | null;
  eventi_ricorrenti: { nome: string; quando: string; tipo: string }[] | null;
  chiusure: string | null;
}
export interface ProfiloPubblico extends DatiProfilo {
  id: number;
  logo: string | null;
  aggiornato_il: string;
}
/** Riepilogo usato dalla pagina Campagna già presente. */
export interface ProfiloBottega {
  bottega: string;
  referente: string;
  citta: string;
  tipo_prodotto: string;
  obiettivo: string;
  canali_preferiti: string[];
  frequenza: string;
  foto_policy: { quantita_mese?: string };
}
export function canali(): Promise<CanaleCollegato[]> {
  return USA_ESEMPI
    ? Promise.resolve(canaliEsempio)
    : richiesta("GET", "/canali");
}
export async function leggiProfilo(): Promise<ProfiloPubblico | null> {
  if (USA_ESEMPI) return leggiProfiloEsempio();
  try {
    return await richiesta<ProfiloPubblico>("GET", "/profilo");
  } catch (e) {
    if (e instanceof ApiErrore && e.stato === 404) return null;
    throw e;
  }
}
export async function salvaProfilo(
  dati: DatiProfilo,
): Promise<ProfiloPubblico> {
  if (USA_ESEMPI) return salvaProfiloEsempio(dati);
  return richiesta<ProfiloPubblico>("PUT", "/profilo", datiScrittura(dati));
}
export async function profilo(): Promise<ProfiloBottega> {
  const p = await leggiProfilo();
  if (!p) throw new Error("Compila prima il profilo della bottega.");
  return {
    bottega: p.nome,
    referente: p.referente,
    citta: p.citta,
    tipo_prodotto:
      SCELTE.tipo_prodotto.find((v) => v.value === p.tipo_prodotto)?.label ??
      p.tipo_prodotto,
    obiettivo:
      SCELTE.obiettivo.find((v) => v.value === p.obiettivo)?.label ??
      p.obiettivo,
    canali_preferiti: p.canali,
    frequenza: p.frequenza ?? "decidete_voi",
    foto_policy:
      typeof p.foto_policy?.quantita_mese === "string"
        ? { quantita_mese: p.foto_policy.quantita_mese }
        : {},
  };
}

const opzioni = (coppie: [string, string][]) =>
  coppie.map(([value, label]) => ({ value, label }));
export const SCELTE = {
  tipo_prodotto: opzioni([
    ["legno_mobili", "Legno e mobili"],
    ["ceramica_vetro", "Ceramica e vetro"],
    ["gioielli_metalli", "Gioielli e metalli"],
    ["tessile_pelle", "Tessuti e pelle"],
    ["alimentare", "Alimentare"],
    ["altro", "Altro"],
  ]),
  valori: opzioni([
    ["artigianalita", "Artigianalità"],
    ["sostenibilita", "Sostenibilità"],
    ["tradizione", "Tradizione"],
    ["innovazione", "Innovazione"],
    ["territorio", "Territorio"],
    ["su_misura", "Su misura"],
  ]),
  fascia_prezzo: opzioni([
    ["accessibile", "Accessibile"],
    ["media", "Media"],
    ["alta", "Alta"],
  ]),
  obiettivo: opzioni([
    ["vendere", "Vendere di più"],
    ["negozio", "Portare persone in bottega"],
    ["notorieta", "Farmi conoscere"],
    ["fidelizzare", "Mantenere il rapporto con i clienti"],
  ]),
  tono: opzioni([
    ["caldo", "Caldo"],
    ["elegante", "Elegante"],
    ["diretto", "Diretto"],
    ["ironico", "Ironico"],
    ["professionale", "Professionale"],
  ]),
  cortesia: opzioni([
    ["tu", "Do del tu"],
    ["lei", "Do del lei"],
    ["dipende", "Dipende dalla situazione"],
  ]),
  canali: opzioni([
    ["facebook", "Facebook"],
    ["instagram", "Instagram"],
  ]),
  frequenza: opzioni([
    ["f1_2", "2 post a settimana"],
    ["f3_4", "3 post a settimana"],
    ["f5_piu", "5 post a settimana"],
    ["decidete_voi", "Decidete voi (3 post a settimana)"],
  ]),
  quantita_mese: opzioni([
    ["meno_5", "Meno di 5"],
    ["da5_a12", "Da 5 a 12"],
    ["da12_a20", "Da 12 a 20"],
    ["oltre_20", "Più di 20"],
  ]),
  chi_scatta: opzioni([
    ["artigiano", "Io"],
    ["fotografo", "Un fotografo"],
    ["consorzio", "Il consorzio"],
  ]),
  persone: opzioni([
    ["mai", "Mai"],
    ["con_consenso", "Solo con il consenso"],
    ["spesso", "Spesso"],
  ]),
  tipo_evento: opzioni([
    ["fiera_mercatino", "Fiera o mercatino"],
    ["festivita", "Festività"],
    ["lancio_prodotto", "Lancio di un prodotto"],
    ["promozione", "Promozione"],
    ["chiusura", "Chiusura"],
    ["altro", "Altro"],
  ]),
};
export const PASSI = [
  "La bottega",
  "La tua storia",
  "Prodotti e valori",
  "Clienti e obiettivo",
  "Come parlare",
  "Canali e frequenza",
  "Le fotografie",
  "Eventi e chiusure",
  "Riepilogo",
];
export const PASSO_CAMPO: Record<string, number> = {
  nome: 0,
  referente: 0,
  citta: 0,
  anni_attivita: 0,
  tipo_prodotto: 2,
  clienti_ideali: 3,
  obiettivo: 3,
  canali: 5,
  eventi_ricorrenti: 7,
};
export const ETICHETTE: Record<string, string> = {
  nome: "Nome della bottega",
  referente: "Referente",
  citta: "Città",
  tipo_prodotto: "Tipo di prodotto",
  clienti_ideali: "Clienti ideali",
  obiettivo: "Obiettivo",
  canali: "Canali preferiti",
  anni_attivita: "Anni di attività",
  eventi_ricorrenti: "Eventi ricorrenti",
};
export function profiloVuoto(): DatiProfilo {
  return {
    nome: "",
    referente: "",
    citta: "",
    tipo_prodotto: "",
    clienti_ideali: "",
    obiettivo: "",
    canali: [],
    anni_attivita: null,
    sito: null,
    storia: null,
    origine: null,
    valori: null,
    gamma: null,
    fascia_prezzo: null,
    stagionalita: null,
    zona: null,
    tono: null,
    cortesia: null,
    vincoli: null,
    frequenza: null,
    orari: null,
    social_esistenti: null,
    foto_policy: null,
    eventi_ricorrenti: null,
    chiusure: null,
  };
}
export function erroriProfilo(p: DatiProfilo): Record<string, string> {
  const e: Record<string, string> = {};
  for (const k of ["nome", "referente", "citta", "clienti_ideali"] as const)
    if (!p[k].trim()) e[k] = "Campo obbligatorio.";
  for (const k of ["tipo_prodotto", "obiettivo"] as const)
    if (!SCELTE[k].some((s) => s.value === p[k])) e[k] = "Scegli una voce.";
  if (
    !p.canali.length ||
    p.canali.some((c) => !SCELTE.canali.some((s) => s.value === c))
  )
    e.canali = "Scegli almeno un canale.";
  if (
    p.anni_attivita !== null &&
    (!Number.isInteger(p.anni_attivita) ||
      p.anni_attivita < 0 ||
      p.anni_attivita > 2147483647)
  )
    e.anni_attivita = "Inserisci un numero intero di anni, da zero in su.";
  if (
    p.eventi_ricorrenti?.some(
      (v) =>
        !v.nome.trim() ||
        !v.quando.trim() ||
        !SCELTE.tipo_evento.some((s) => s.value === v.tipo),
    )
  )
    e.eventi_ricorrenti =
      "Per ogni evento indica nome, quando e tipo, oppure rimuovilo.";
  return e;
}
export function datiScrittura(p: DatiProfilo): DatiProfilo {
  // Elenco esplicito: id, logo e aggiornato_il letti dal server non sono scrivibili.
  const vuoto = profiloVuoto();
  return Object.fromEntries(
    Object.keys(vuoto).map((k) => {
      const v = p[k as keyof DatiProfilo];
      return [
        k,
        typeof v === "string" ? v.trim() || vuoto[k as keyof DatiProfilo] : v,
      ];
    }),
  ) as unknown as DatiProfilo;
}
