/** Invio di una decisione: occupato, messaggio d'errore dell'API e rilettura a fine corsa. */
import { useState } from "react";

import { ApiErrore } from "../../../../api/http";

export function useInvio(dopo: () => void) {
  const [occupato, setOccupato] = useState(false);
  const [errore, setErrore] = useState<string | null>(null);

  const esegui = async (azione: () => Promise<unknown>) => {
    setOccupato(true);
    setErrore(null);
    try {
      await azione();
      dopo();
    } catch (e) {
      setErrore(
        e instanceof ApiErrore ? e.message : "Qualcosa non ha funzionato.",
      );
    } finally {
      setOccupato(false);
    }
  };

  return { occupato, errore, esegui };
}
