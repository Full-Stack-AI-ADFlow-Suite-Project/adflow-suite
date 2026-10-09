/**
 * Bozza: i passi 10 (durata e canali), 11 (foto a gruppi) e 12 (riepilogo
 * e invio). La bozza si crea alla fine del passo 10; senza PATCH (2a) i
 * dati del passo 10 si leggono in sola lettura.
 */
import { useState } from "react";
import { Text } from "@mantine/core";

import {
  crea,
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
  const [passo, setPasso] = useState(campagna ? 11 : 10);
  const [errore, setErrore] = useState("");

  const continua10 = async (dati: CampagnaCrea) => {
    setErrore("");
    try {
      const c = await crea(dati);
      onCreata(c);
      setPasso(11);
    } catch (e) {
      setErrore(e instanceof ApiErrore ? e.dettaglio : "Errore inatteso.");
    }
  };

  if (passo === 10 && !campagna) {
    return (
      <Passo10 profilo={profilo} errore={errore} onContinua={continua10} />
    );
  }
  if (!campagna) return null;
  if (passo === 11) {
    return (
      <Passo11
        campagna={campagna}
        onCambiata={onCambiata}
        onAvanti={() => setPasso(12)}
      />
    );
  }
  return (
    <>
      <Text
        size="sm"
        c="verde"
        td="underline"
        mb="md"
        component="button"
        onClick={() => setPasso(11)}
        style={{
          background: "none",
          border: "none",
          cursor: "pointer",
          padding: 0,
        }}
      >
        ← Torna alle foto
      </Text>
      <Passo12 campagna={campagna} profilo={profilo} onInviata={onInviata} />
    </>
  );
}
