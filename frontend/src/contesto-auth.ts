/**
 * Contesto della sessione: utente corrente, entrata e uscita.
 * Le rotte per ruolo (spec R-29): artigiano → Campagna,
 * operatore e admin → campagne da approvare.
 */
import { createContext, useContext } from "react";

import type { Ruolo, UtentePubblico } from "./api/accesso";

export function paginaIniziale(ruolo: Ruolo): string {
  return ruolo === "artigiano" ? "/campagna" : "/da-approvare";
}

export interface Auth {
  /** undefined = controllo della sessione in corso. */
  utente: UtentePubblico | null | undefined;
  sessioneScaduta: boolean;
  entra: (email: string, password: string) => Promise<UtentePubblico>;
  esci: () => Promise<void>;
}

export const ContestoAuth = createContext<Auth | null>(null);

export function useAuth(): Auth {
  const auth = useContext(ContestoAuth);
  if (!auth) throw new Error("useAuth fuori da AuthProvider");
  return auth;
}
