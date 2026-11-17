/** Le altre campagne dell'artigiano, per vedere se si sovrappongono a quella in bozza. */
import { useEffect, useState } from "react";

import { elenco, type CampagnaElencoItem } from "../../../api/campagne";

export function useAltreCampagne(idEscluso?: number): CampagnaElencoItem[] {
  const [altre, setAltre] = useState<CampagnaElencoItem[]>([]);
  useEffect(() => {
    let vivo = true;
    elenco()
      .then((lista) => {
        if (vivo) setAltre(lista.filter((c) => c.id !== idEscluso));
      })
      .catch(() => {
        if (vivo) setAltre([]);
      });
    return () => {
      vivo = false;
    };
  }, [idEscluso]);
  return altre;
}
