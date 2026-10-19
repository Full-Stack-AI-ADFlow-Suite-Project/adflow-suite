/**
 * Pagina Campagna (docs/pagine/AdFlow-campagna*.html):
 * niente campagne → Bentornato; una bozza → passi 10–12; dopo l'invio
 * una vista per stato. Una campagna alla volta: con più campagne si apre
 * quella che chiede qualcosa e in cima c'è la riga di scelta (spec §4).
 */
import { useCallback, useEffect, useState } from "react";
import { Center, Loader } from "@mantine/core";

import {
  dettaglio,
  elenco,
  type CampagnaDettaglio,
  type CampagnaElencoItem,
} from "../../api/campagne";
import {
  profilo as apiProfilo,
  type ProfiloBottega,
} from "../../api/artigiani";
import { Guscio } from "../../components/Guscio";
import { Bentornato } from "./campagna/Bentornato";
import { Bozza } from "./campagna/Bozza";
import { CampagnePassate } from "./campagna/viste/CampagnePassate";
import { scegli } from "./campagna/viste/scelta";
import { SceltaCampagna } from "./campagna/viste/SceltaCampagna";
import { VistaStato } from "./campagna/viste/VistaStato";

type Vista =
  | { tipo: "bentornato" }
  | { tipo: "bozza"; campagna: CampagnaDettaglio | null }
  | { tipo: "stato"; campagna: CampagnaDettaglio };

export function Campagna() {
  const [vista, setVista] = useState<Vista | null>(null);
  const [profilo, setProfilo] = useState<ProfiloBottega | null>(null);
  const [respintaRecente, setRespintaRecente] =
    useState<CampagnaDettaglio | null>(null);
  const [lista, setLista] = useState<CampagnaElencoItem[]>([]);

  /** Mostra una campagna: la bozza nei passi, le altre nella vista per stato. */
  const mostra = useCallback(async (c: CampagnaElencoItem) => {
    const d = await dettaglio(c.id);
    if (c.stato === "bozza") {
      setVista({ tipo: "bozza", campagna: d });
      return;
    }
    setVista({ tipo: "stato", campagna: d });
    setRespintaRecente(d.stato === "respinta" ? d : null);
  }, []);

  const carica = useCallback(
    async (preferita?: number) => {
      let lista;
      let p;
      try {
        [p, lista] = await Promise.all([apiProfilo(), elenco()]);
      } catch {
        setVista({ tipo: "bentornato" });
        return;
      }
      setProfilo(p);
      setLista(lista);
      const daAprire =
        lista.find((c) => c.id === preferita) ?? scegli(lista).aperta;
      if (daAprire) {
        await mostra(daAprire);
        return;
      }
      setVista({ tipo: "bentornato" });
    },
    [mostra],
  );

  useEffect(() => {
    // Carica la campagna all'apertura della pagina: setState solo dopo l'attesa.
    // oxlint-disable-next-line react/set-state-in-effect
    void carica();
  }, [carica]);

  const apriBozza = useCallback((c: CampagnaDettaglio) => {
    setVista({ tipo: "bozza", campagna: c });
    // La nuova bozza entra nella riga di scelta.
    void elenco().then(setLista);
  }, []);

  const ricarica = useCallback(
    async (c: CampagnaDettaglio) =>
      setVista({ tipo: "bozza", campagna: await dettaglio(c.id) }),
    [],
  );

  const nuovaCampagna = useCallback(() => setVista({ tipo: "bentornato" }), []);
  /** Dopo l'invio si resta sulla campagna appena inviata, non su un'altra. */
  const dopoInvio = useCallback(
    async (inviataId?: number) => {
      setRespintaRecente(null);
      await carica(inviataId);
    },
    [carica],
  );

  const { visibili, passate } = scegli(lista);
  const mostrata =
    vista !== null && vista.tipo !== "bentornato" ? vista.campagna : null;
  const apertaId = mostrata?.id ?? null;
  const inChiaro = visibili.some((c) => c.id === apertaId);
  // Una sola campagna: la riga serve per crearne un'altra, tranne dove la
  // vista ha già il suo pulsante (respinta, scaduta) o si sta compilando.
  const mostraRiga =
    visibili.length > 1 ||
    (visibili.length === 1 &&
      vista?.tipo !== "bozza" &&
      mostrata?.stato !== "respinta" &&
      mostrata?.stato !== "scaduta") ||
    (visibili.length > 0 && mostrata !== null && !inChiaro);

  return (
    <Guscio titolo="Campagna">
      {mostraRiga && (
        <SceltaCampagna
          visibili={visibili}
          apertaId={inChiaro ? apertaId : null}
          onApri={(c) => void mostra(c)}
          onNuova={nuovaCampagna}
        />
      )}
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
          onInviata={() => dopoInvio(vista.campagna?.id)}
        />
      ) : (
        <VistaStato
          campagna={vista.campagna}
          onNuovaCampagna={nuovaCampagna}
          onRisposta={() => void elenco().then(setLista)}
        />
      )}
      {vista !== null && vista.tipo !== "bozza" && (
        <CampagnePassate
          passate={passate}
          apertaId={inChiaro ? null : apertaId}
          onApri={(c) => void mostra(c)}
        />
      )}
    </Guscio>
  );
}
