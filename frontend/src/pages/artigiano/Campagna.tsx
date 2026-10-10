/**
 * Pagina Campagna (docs/appunti/pagine/AdFlow-campagna*.html):
 * niente campagne → Bentornato; una bozza → passi 10–12; dopo l'invio
 * una vista per stato. Una campagna alla volta (la scelta è della 2b).
 */
import { useCallback, useEffect, useState } from "react";
import { Center, Loader } from "@mantine/core";

import { dettaglio, elenco, type CampagnaDettaglio } from "../../api/campagne";
import {
  profilo as apiProfilo,
  type ProfiloBottega,
} from "../../api/artigiani";
import { Guscio } from "../../components/Guscio";
import { Bentornato } from "./campagna/Bentornato";
import { Bozza } from "./campagna/Bozza";
import { VistaStato } from "./campagna/VistaStato";

type Vista =
  | { tipo: "bentornato" }
  | { tipo: "bozza"; campagna: CampagnaDettaglio | null }
  | { tipo: "stato"; campagna: CampagnaDettaglio };

export function Campagna() {
  const [vista, setVista] = useState<Vista | null>(null);
  const [profilo, setProfilo] = useState<ProfiloBottega | null>(null);
  const [respintaRecente, setRespintaRecente] =
    useState<CampagnaDettaglio | null>(null);

  const carica = useCallback(async () => {
    let lista;
    let p;
    try {
      [p, lista] = await Promise.all([apiProfilo(), elenco()]);
    } catch {
      setVista({ tipo: "bentornato" });
      return;
    }
    setProfilo(p);
    const bozza = lista.find((c) => c.stato === "bozza");
    const ultima = lista.reduce<(typeof lista)[number] | null>(
      (m, c) => (m === null || c.id > m.id ? c : m),
      null,
    );
    if (bozza) {
      setVista({ tipo: "bozza", campagna: await dettaglio(bozza.id) });
      return;
    }
    if (ultima) {
      const c = await dettaglio(ultima.id);
      setVista({ tipo: "stato", campagna: c });
      setRespintaRecente(c.stato === "respinta" ? c : null);
      return;
    }
    setVista({ tipo: "bentornato" });
  }, []);

  useEffect(() => {
    // Carica la campagna all'apertura della pagina: setState solo dopo l'attesa.
    // oxlint-disable-next-line react/set-state-in-effect
    void carica();
  }, [carica]);

  const apriBozza = useCallback((c: CampagnaDettaglio) => {
    setVista({ tipo: "bozza", campagna: c });
  }, []);

  const ricarica = useCallback(
    async (c: CampagnaDettaglio) =>
      setVista({ tipo: "bozza", campagna: await dettaglio(c.id) }),
    [],
  );

  const nuovaCampagna = useCallback(() => setVista({ tipo: "bentornato" }), []);
  const dopoInvio = useCallback(async () => {
    setRespintaRecente(null);
    await carica();
  }, [carica]);

  return (
    <Guscio titolo="Campagna">
      {vista === null || profilo === null ? (
        <Center py="xl">
          <Loader color="verde" />
        </Center>
      ) : vista.tipo === "bentornato" ? (
        <Bentornato
          profilo={profilo}
          respinta={respintaRecente}
          onAvanti={() => setVista({ tipo: "bozza", campagna: null })}
        />
      ) : vista.tipo === "bozza" ? (
        <Bozza
          campagna={vista.campagna}
          profilo={profilo}
          onCambiata={ricarica}
          onCreata={apriBozza}
          onInviata={dopoInvio}
        />
      ) : (
        <VistaStato campagna={vista.campagna} onNuovaCampagna={nuovaCampagna} />
      )}
    </Guscio>
  );
}
