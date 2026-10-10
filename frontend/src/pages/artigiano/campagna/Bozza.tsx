/**
 * Bozza: i passi 10 (durata e canali), 11 (foto a gruppi) e 12 (riepilogo
 * e invio). La bozza si crea alla fine del passo 10 o si modifica con PATCH (T2a-21/T2a-53).
 * CA-08: bozza aperta → rientra → pagina Campagna dal passo 10 con dati, canali, gruppi e foto.
 */
import { useState } from "react";

import {
  crea,
  modifica,
  type CampagnaCrea,
  type CampagnaDettaglio,
} from "../../../api/campagne";
import type { ProfiloBottega } from "../../../api/artigiani";
import { ApiErrore } from "../../../api/http";
import { Passo10 } from "./Passo10";
import { Passo11 } from "./Passo11";
import { Passo12 } from "./Passo12";

export function Bozza({
  campagna,
  profilo,
  onCambiata,
  onCreata,
  onInviata,
}: {
  campagna: CampagnaDettaglio | null;
  profilo: ProfiloBottega;
  onCambiata: (c: CampagnaDettaglio) => Promise<void>;
  onCreata: (c: CampagnaDettaglio) => void;
  onInviata: () => Promise<void>;
}) {
  const [passo, setPasso] = useState<10 | 11 | 12>(10);
  const [errore, setErrore] = useState("");

  const continua10 = async (dati: CampagnaCrea) => {
    setErrore("");
    try {
      if (campagna) {
        const c = await modifica(campagna.id, dati);
        await onCambiata(c);
        setPasso(11);
      } else {
        const c = await crea(dati);
        onCreata(c);
        setPasso(11);
      }
    } catch (e) {
      setErrore(e instanceof ApiErrore ? e.dettaglio : "Errore inatteso.");
    }
  };

  if (passo === 10) {
    return (
      <Passo10
        key={campagna?.id ?? "nuova"}
        profilo={profilo}
        campagna={campagna}
        errore={errore}
        onContinua={continua10}
      />
    );
  }

  if (!campagna) return null;

  if (passo === 11) {
    return (
      <Passo11
        campagna={campagna}
        onCambiata={onCambiata}
        onIndietro={() => setPasso(10)}
        onAvanti={() => setPasso(12)}
      />
    );
  }

  return (
    <Passo12
      campagna={campagna}
      profilo={profilo}
      onIndietro={() => setPasso(11)}
      onInviata={onInviata}
    />
  );
}
