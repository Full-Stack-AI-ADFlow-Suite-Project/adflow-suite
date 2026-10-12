/**
 * Le azioni dell'operatore sul singolo post (T2b-51): modifica a mano, spunta
 * "va bene", rigenera nelle due modalità. Solo in `in_revisione` su un post
 * `da_approvare` (R-16, R-30); con un intervento in corso nessun altro
 * intervento (R-31); alla terza rigenerazione resta la modifica a mano (R-03).
 */
import {
  Alert,
  Button,
  Checkbox,
  Group,
  Loader,
  Stack,
  Text,
} from "@mantine/core";
import { useEffect, useState } from "react";

import { ApiErrore } from "../../../../api/http";
import { segnaControllato } from "../../../../api/interventi";
import type { ModalitaRigenerazione } from "../../../../api/interventi";
import type { PostVista } from "../../../../api/revisione";
import { dataOra } from "../../campagna/util";
import { ModificaMano } from "./ModificaMano";
import { Rigenera } from "./Rigenera";
import {
  interventoAttivo,
  MAX_RIGENERAZIONI,
  rigenerazioniFatte,
} from "./regole";

/** Ogni quanto si rilegge Vedi campagna mentre l'AI lavora sul post. */
const ATTESA_AGGIORNAMENTO_MS = 2000;

export function AzioniPost({
  post,
  statoCampagna,
  ricarica,
}: {
  post: PostVista;
  statoCampagna: string;
  ricarica: () => void;
}) {
  const [modifica, setModifica] = useState(false);
  const [rigenera, setRigenera] = useState<ModalitaRigenerazione | null>(null);
  const [occupato, setOccupato] = useState(false);
  const [errore, setErrore] = useState<string | null>(null);

  const inCorso = interventoAttivo(post);
  const scaduto = !!post.intervento_in_corso && !inCorso;

  // Finché l'AI lavora si rilegge la pagina: la nuova versione compare da sola.
  useEffect(() => {
    if (!inCorso) return;
    const timer = setInterval(ricarica, ATTESA_AGGIORNAMENTO_MS);
    return () => clearInterval(timer);
  }, [inCorso, ricarica]);

  if (
    post.stato === "approvato" &&
    ["attiva", "sospesa"].includes(statoCampagna)
  )
    return (
      <Text size="xs" c="dimmed">
        Il post non si modifica: per fermare le uscite sospendi o annulla la
        campagna.
      </Text>
    );
  if (post.stato !== "da_approvare" || statoCampagna !== "in_revisione")
    return null;

  const v = post.versione_corrente;
  if (!v) return null;

  const fatte = rigenerazioniFatte(post);
  const finite = fatte >= MAX_RIGENERAZIONI;
  const fermo = inCorso || occupato;

  const spunta = async (valore: boolean) => {
    setOccupato(true);
    setErrore(null);
    try {
      await segnaControllato(post.post_id, valore);
      ricarica();
    } catch (e) {
      setErrore(
        e instanceof ApiErrore ? e.message : "Non sono riuscita a salvare.",
      );
    } finally {
      setOccupato(false);
    }
  };

  const dopoIntervento = () => {
    setModifica(false);
    setRigenera(null);
    ricarica();
  };

  return (
    <Stack gap="xs">
      {inCorso && (
        <Alert color="yellow" variant="light" py="xs">
          <Group gap="xs" wrap="nowrap">
            <Loader size="xs" color="yellow" />
            <Text size="sm">
              Rigenerazione{" "}
              {post.intervento_in_corso === "rigenera_da_proposta"
                ? "da testo proposto"
                : "da zero"}{" "}
              in corso
              {post.intervento_dal
                ? ` dalle ${dataOra(post.intervento_dal)}`
                : ""}
              . Finché l'AI lavora il post non si tocca e la campagna non si
              approva.
            </Text>
          </Group>
        </Alert>
      )}
      {scaduto && (
        <Alert color="gray" variant="light" py="xs">
          L'ultima rigenerazione è partita da più di 10 minuti: vale come
          fallita, il post è com'era e si può rilanciare.
        </Alert>
      )}

      <Checkbox
        label="Va bene"
        checked={!!post.controllato_il}
        disabled={fermo || (post.da_rivedere && !post.controllato_il)}
        onChange={(e) => void spunta(e.currentTarget.checked)}
        description={
          post.controllato_il
            ? `Controllato da operatore n. ${
                post.controllato_da ?? "—"
              } · ${dataOra(post.controllato_il)}`
            : post.da_rivedere
            ? "Un post da rivedere non si può spuntare: prima va sistemato."
            : "La vedono tutti gli operatori; si toglie a ogni nuova versione."
        }
      />

      <Group gap="xs" wrap="wrap">
        <Button
          size="xs"
          variant="default"
          disabled={fermo}
          onClick={() => setModifica(true)}
        >
          Modifica a mano
        </Button>
        <Button
          size="xs"
          variant="default"
          disabled={fermo || finite}
          onClick={() => setRigenera("totale")}
        >
          Rigenera da zero
        </Button>
        <Button
          size="xs"
          variant="default"
          disabled={fermo || finite}
          onClick={() => setRigenera("da_proposta")}
        >
          Rigenera da testo proposto
        </Button>
        <Text size="xs" c="dimmed">
          Rigenerazioni: {fatte} di {MAX_RIGENERAZIONI}
        </Text>
      </Group>
      {finite && (
        <Text size="xs" c="dimmed">
          Le 3 rigenerazioni sono finite: resta la modifica a mano.
        </Text>
      )}

      {errore && (
        <Alert color="red" variant="light" py="xs">
          {errore}
        </Alert>
      )}

      {modifica && (
        <ModificaMano
          post={post}
          aperto
          chiudi={() => setModifica(false)}
          fatto={dopoIntervento}
        />
      )}
      {rigenera && (
        <Rigenera
          post={post}
          modalita={rigenera}
          chiudi={() => setRigenera(null)}
          fatto={dopoIntervento}
        />
      )}
    </Stack>
  );
}
