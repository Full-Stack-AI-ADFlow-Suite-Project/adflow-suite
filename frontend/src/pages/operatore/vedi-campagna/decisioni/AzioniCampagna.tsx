/**
 * Le azioni dell'operatore sulla campagna approvata (T3-64), sotto la barra di
 * Vedi campagna: sospendi e annulla la campagna in `attiva`, riattiva e annulla
 * in `sospesa` (spec R-33). Negli altri stati non c'è nessun pulsante. Respingi
 * è in `Decidi`; nota interna e togli canale restano nascosti (ADR-114).
 */
import { Button, Card, Group } from "@mantine/core";
import { useState } from "react";

import type { VediCampagna } from "../../../../api/revisione";
import { Annulla, Riattiva, Sospendi } from "./Sospensione";
import type { PostInArretrato } from "./Sospensione";

type Finestra = "sospendi" | "riattiva" | "annulla" | null;

export function AzioniCampagna({
  vista,
  ricarica,
}: {
  vista: VediCampagna;
  ricarica: () => void;
}) {
  const [finestra, setFinestra] = useState<Finestra>(null);
  const stato = vista.campagna.stato;
  const sospendibile = stato === "attiva";
  const riattivabile = stato === "sospesa";

  const chiudi = () => setFinestra(null);
  const fatto = () => {
    setFinestra(null);
    ricarica();
  };

  if (!sospendibile && !riattivabile) return null;

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
    <Card withBorder radius="lg" p="md" aria-label="Azioni sulla campagna">
      <Group gap="xs" wrap="wrap">
        {sospendibile && (
          <Button
            size="xs"
            variant="light"
            color="yellow"
            onClick={() => setFinestra("sospendi")}
          >
            Sospendi
          </Button>
        )}
        {riattivabile && (
          <Button
            size="xs"
            variant="light"
            onClick={() => setFinestra("riattiva")}
          >
            Riattiva
          </Button>
        )}
        <Button
          size="xs"
          variant="light"
          color="red"
          onClick={() => setFinestra("annulla")}
        >
          Annulla la campagna
        </Button>
      </Group>

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
