/**
 * Dati di esempio con la forma delle API di plan §3: li usano le pagine
 * finché non si passa alle API vere (T1-07). La sessione finta vive in
 * localStorage, così un ricaricamento non butta fuori.
 */
import { ApiErrore } from "../http";
import type { Consorzio, UtentePubblico } from "../accesso";

export const USA_ESEMPI = import.meta.env.VITE_USA_ESEMPI !== "0";

export const consorzioEsempio: Consorzio = {
  nome: "Consorzio Artigiani delle Alpi",
  telefono: "0172 000 000",
  email: "info@consorzio.example",
};

/** Utenti di esempio: l'accesso vale con la password "prova". */
const utentiEsempio: (UtentePubblico & { password: string })[] = [
  {
    id: 1,
    email: "mario@falegnameriabianchi.it",
    nome: "Mario Bianchi",
    ruolo: "artigiano",
    password: "prova",
  },
  {
    id: 2,
    email: "laura@consorzio.example",
    nome: "Laura Ferrari",
    ruolo: "operatore",
    password: "prova",
  },
  {
    id: 3,
    email: "admin@consorzio.example",
    nome: "Admin",
    ruolo: "admin",
    password: "prova",
  },
];

const CHIAVE_SESSIONE = "adflow_utente_esempio";

function leggiSessione(): UtentePubblico | null {
  const grezzo = localStorage.getItem(CHIAVE_SESSIONE);
  if (!grezzo) return null;
  try {
    return JSON.parse(grezzo) as UtentePubblico;
  } catch {
    return null;
  }
}

export async function meEsempio(): Promise<UtentePubblico> {
  const utente = leggiSessione();
  if (!utente) throw new ApiErrore(401, "Sessione assente.");
  return utente;
}

export async function loginEsempio(
  email: string,
  password: string,
): Promise<UtentePubblico> {
  const record = utentiEsempio.find(
    (u) => u.email === email.trim().toLowerCase() && u.password === password,
  );
  if (!record) throw new ApiErrore(401, "Email o password non corrette.");
  const { password: _password, ...utente } = record;
  localStorage.setItem(CHIAVE_SESSIONE, JSON.stringify(utente));
  return utente;
}

export async function logoutEsempio(): Promise<void> {
  localStorage.removeItem(CHIAVE_SESSIONE);
}
