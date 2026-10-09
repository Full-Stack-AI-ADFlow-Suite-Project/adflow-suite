/**
 * Richiesta verso le API (prefisso /api, proxy di Vite verso il backend).
 * Ogni 401 chiama il gestore registrato dall'auth: si torna al login
 * e dopo l'accesso alla pagina di partenza (spec R-29).
 */

export class ApiErrore extends Error {
  stato: number;
  dettaglio: string;

  constructor(stato: number, dettaglio: string) {
    super(dettaglio);
    this.stato = stato;
    this.dettaglio = dettaglio;
  }
}

type Gestore401 = () => void;
let gestore401: Gestore401 | null = null;

export function impostaGestore401(gestore: Gestore401): void {
  gestore401 = gestore;
}

interface Opzioni {
  /** False per login e me: lì un 401 non è una sessione scaduta. */
  gestisci401?: boolean;
}

export async function richiesta<T>(
  metodo: string,
  percorso: string,
  corpo?: unknown,
  opzioni: Opzioni = {},
): Promise<T> {
  const risposta = await fetch(`/api${percorso}`, {
    method: metodo,
    headers:
      corpo === undefined ? undefined : { "Content-Type": "application/json" },
    body: corpo === undefined ? undefined : JSON.stringify(corpo),
  });

  if (risposta.status === 401) {
    if (opzioni.gestisci401 !== false) gestore401?.();
    throw new ApiErrore(401, "Sessione scaduta.");
  }
  if (risposta.status === 204) return undefined as T;
  if (!risposta.ok) {
    const dati = (await risposta.json().catch(() => null)) as {
      detail?: string;
    } | null;
    throw new ApiErrore(risposta.status, dati?.detail ?? "Errore inatteso.");
  }
  return (await risposta.json()) as T;
}
