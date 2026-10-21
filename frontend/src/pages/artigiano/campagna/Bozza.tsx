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
import stile from "./Passo10.module.css";
import { Passo11 } from "./Passo11";
import { Passo12 } from "./Passo12";

const PASSI_BOZZA: { codice: 10 | 11 | 12; numero: number; label: string }[] = [
  { codice: 10, numero: 1, label: "Durata e canali" },
  { codice: 11, numero: 2, label: "Foto della campagna" },
  { codice: 12, numero: 3, label: "Riepilogo e invio" },
];

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

  return (
    <div className={stile.layout}>
      <aside className={stile.indice} aria-label="Passi della campagna">
        <div className={stile.indiceTitolo}>Nuova campagna · 3 passi</div>
        <div className={stile.indiceLista}>
          {PASSI_BOZZA.map((voce) => {
            const attivo = passo === voce.codice;
            const completato = passo > voce.codice;
            const disabilitato = voce.codice !== 10 && !campagna;
            const classi = [
              stile.vocePasso,
              attivo ? stile.vocePassoAttiva : "",
              completato ? stile.vocePassoCompletata : "",
            ]
              .filter(Boolean)
              .join(" ");
            return (
              <button
                key={voce.codice}
                type="button"
                disabled={disabilitato}
                className={classi}
                onClick={() => setPasso(voce.codice)}
              >
                <span className={stile.voceNumero}>
                  {completato ? "✓" : voce.numero}
                </span>
                <span>{voce.label}</span>
              </button>
            );
          })}
        </div>
      </aside>

      {passo === 10 || !campagna ? (
        <Passo10
          key={campagna?.id ?? "nuova"}
          profilo={profilo}
          campagna={campagna}
          errore={errore}
          onContinua={continua10}
        />
      ) : passo === 11 ? (
        <Passo11
          campagna={campagna}
          onCambiata={onCambiata}
          onIndietro={() => setPasso(10)}
          onAvanti={() => setPasso(12)}
        />
      ) : (
        <Passo12
          campagna={campagna}
          onIndietro={() => setPasso(11)}
          onInviata={onInviata}
        />
      )}
    </div>
  );
}
