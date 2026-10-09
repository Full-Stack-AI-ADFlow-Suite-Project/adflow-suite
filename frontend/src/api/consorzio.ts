/** GET /consorzio (main.py): nome, telefono ed email del consorzio, senza sessione. */
import { richiesta } from "./http";
import type { Consorzio } from "./accesso";
import { consorzioEsempio, USA_ESEMPI } from "./esempi/accesso";

export function consorzio(): Promise<Consorzio> {
  if (USA_ESEMPI) return Promise.resolve(consorzioEsempio);
  return richiesta<Consorzio>("GET", "/consorzio", undefined, {
    gestisci401: false,
  });
}
