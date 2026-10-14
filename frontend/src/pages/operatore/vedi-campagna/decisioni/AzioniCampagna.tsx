/**
 * Le decisioni dell'operatore sulla campagna (T2b-52), sotto la barra di
 * Vedi campagna: nota interna in ogni stato dopo l'invio, respingi e togli il
 * canale in revisione, sospendi, riattiva e annulla in campagna attiva o
 * sospesa (spec §2.3, R-18, R-32, R-33). Si decide solo qui.
 * Congelato per l'MVP, ADR-114: le azioni di nota interna, togli canale, sospendi, riattiva e annulla sono nascoste.
 */
import { Button, Card, Group, Text } from "@mantine/core";
import { useState } from "react";

import type { CampagnaDettaglio } from "../../../../api/campagne";
import type { VediCampagna } from "../../../../api/revisione";
import { NotaInterna } from "./NotaInterna";
import { Respingi } from "./Respingi";
import { Annulla, Riattiva, Sospendi } from "./Sospensione";
import type { PostInArretrato } from "./Sospensione";
import { TogliCanale } from "./TogliCanale";

type Finestra =
  | "nota"
  | "respingi"
  | "togli"
  | "sospendi"
  | "riattiva"
  | "annulla"
  | null;

export function AzioniCampagna({
  vista,
  campagna,
  ricarica,
}: {
  vista: VediCampagna;
  campagna: CampagnaDettaglio | null;
  ricarica: () => void;
}) {
  const [finestra, setFinestra] = useState<Finestra>(null);
  const stato = vista.campagna.stato;

  // I canali ancora in campagna: un canale tolto non si toglie due volte.
  const tolti = vista.campagna.canali_tolti ?? [];
  const canali = (vista.campagna.canali ?? []).filter(
    (c) => !tolti.includes(c),
  );

  const puoRespingere =
    stato === "in_revisione" || stato === "piano_da_rivedere";
  const puoTogliere =
    stato === "generazione_fallita" ||
    stato === "piano_da_rivedere" ||
    stato === "in_revisione";
  const sospendibile = stato === "attiva";
  const riattivabile = stato === "sospesa";

  const chiudi = () => setFinestra(null);
  const fatto = () => {
    setFinestra(null);
    ricarica();
  };

  // eslint-disable-next-line react/purity
  const adesso = new Date().toISOString();
  const arretrati: PostInArretrato[] = vista.uscite.flatMap((u) =>
    u.post
      .filter((p) => p.stato === "approvato" && p.data_ora < adesso)
      .map((p) => ({
        postId: p.post_id,
        uscita: u.numero,
        canale: p.canale,
        dataOra: p.data_ora,
      })),
  );

  return (
    <Card withBorder radius="lg" p="md" aria-label="Decisioni sulla campagna">
      <Group gap="xs" wrap="wrap">
        <Button size="xs" variant="default" onClick={() => setFinestra("nota")}>
          Nota interna
        </Button>
        {puoRespingere && (
          <Button
            size="xs"
            variant="default"
            color="red"
            disabled={!campagna}
            onClick={() => setFinestra("respingi")}
          >
            Respingi
          </Button>
        )}
        {puoTogliere && (
          <Button
            size="xs"
            variant="default"
            disabled={canali.length < 2}
            onClick={() => setFinestra("togli")}
          >
            Togli il canale
          </Button>
        )}
        {sospendibile && (
          <Button
            size="xs"
            variant="default"
            onClick={() => setFinestra("sospendi")}
          >
            Sospendi
          </Button>
        )}
        {riattivabile && (
          <Button
            size="xs"
            variant="default"
            onClick={() => setFinestra("riattiva")}
          >
            Riattiva
          </Button>
        )}
        {(sospendibile || riattivabile) && (
          <Button
            size="xs"
            variant="default"
            color="red"
            onClick={() => setFinestra("annulla")}
          >
            Annulla la campagna
          </Button>
        )}
        {puoTogliere && canali.length < 2 && (
          <Text size="xs" c="dimmed">
            È rimasto un solo canale: non si può togliere.
          </Text>
        )}
      </Group>

      {finestra === "nota" && (
        <NotaInterna
          campagnaId={vista.campagna.id}
          chiudi={chiudi}
          fatto={fatto}
        />
      )}
      {finestra === "respingi" && campagna && (
        <Respingi campagna={campagna} chiudi={chiudi} fatto={fatto} />
      )}
      {finestra === "togli" && (
        <TogliCanale
          campagnaId={vista.campagna.id}
          canali={canali}
          generazioneFallita={stato === "generazione_fallita"}
          chiudi={chiudi}
          fatto={fatto}
        />
      )}
      {finestra === "sospendi" && (
        <Sospendi
          campagnaId={vista.campagna.id}
          chiudi={chiudi}
          fatto={fatto}
        />
      )}
      {finestra === "riattiva" && (
        <Riattiva
          campagnaId={vista.campagna.id}
          arretrati={arretrati}
          chiudi={chiudi}
          fatto={fatto}
        />
      )}
      {finestra === "annulla" && (
        <Annulla campagnaId={vista.campagna.id} chiudi={chiudi} fatto={fatto} />
      )}
    </Card>
  );
}
