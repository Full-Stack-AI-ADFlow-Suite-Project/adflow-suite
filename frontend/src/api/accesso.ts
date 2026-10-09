/**
 * Modulo accesso (plan §3): POST /auth/login, POST /auth/logout, GET /auth/me.
 * I tipi rispecchiano backend/app/moduli/accesso/schemas.py.
 */
import { richiesta } from "./http";
import {
  loginEsempio,
  logoutEsempio,
  meEsempio,
  USA_ESEMPI,
} from "./esempi/accesso";

export type Ruolo = "artigiano" | "operatore" | "admin";

export interface Login {
  email: string;
  password: string;
}

export interface UtentePubblico {
  id: number;
  email: string;
  nome: string;
  ruolo: Ruolo;
}

/** Il contatto del consorzio si legge senza sessione (main.py, GET /consorzio). */
export interface Consorzio {
  nome: string;
  telefono: string;
  email: string;
}

export function login(dati: Login): Promise<UtentePubblico> {
  if (USA_ESEMPI) return loginEsempio(dati.email, dati.password);
  return richiesta<UtentePubblico>("POST", "/auth/login", dati, {
    gestisci401: false,
  });
}

export function logout(): Promise<void> {
  if (USA_ESEMPI) return logoutEsempio();
  return richiesta<void>("POST", "/auth/logout", undefined, {
    gestisci401: false,
  });
}

export function me(): Promise<UtentePubblico> {
  if (USA_ESEMPI) return meEsempio();
  return richiesta<UtentePubblico>("GET", "/auth/me", undefined, {
    gestisci401: false,
  });
}
