/**
 * Le azioni dell'operatore sul singolo post (T2b-51, T3-64). I pulsanti nascono
 * solo da `post.interventi`, cioè da ciò che il server dice ammesso adesso
 * (R-16): modifica a mano, rigenera il testo, cambia foto, sposta,
 * annulla il post, riprogramma. Con un intervento in corso nessun altro
 * intervento (R-31); alla terza rigenerazione resta la modifica a mano (R-03).
 */
import { Alert, Button, Group, Loader, Stack, Text } from "@mantine/core";
import { useEffect, useState } from "react";

import type { PostVista } from "../../../../api/revisione";
import { dataOra } from "../../campagna/util";
import { RiprogrammaPost } from "../decisioni/RiprogrammaPost";
import { AnnullaPost } from "./AnnullaPost";
import { CambiaFoto } from "./CambiaFoto";
import { ModificaMano } from "./ModificaMano";
import { Rigenera } from "./Rigenera";
import {
  interventoAttivo,
  MAX_RIGENERAZIONI,
  rigenerazioniFatte,
} from "./regole";
import { Sposta } from "./Sposta";

/** Ogni quanto si rilegge Vedi campagna mentre l'AI lavora sul post. */
const ATTESA_AGGIORNAMENTO_MS = 2000;

type Finestra =
  | "modifica"
  | "cambia_foto"
  | "rigenera_immagine"
  | "sposta"
  | "annulla"
  | "rigenera"
  | null;

export function AzioniPost({
  post,
  statoCampagna,
  ricarica,
}: {
  post: PostVista;
  statoCampagna: string;
  ricarica: () => void;
}) {
  const [finestra, setFinestra] = useState<Finestra>(null);

  const inCorso = interventoAttivo(post);
  const scaduto = !!post.intervento_in_corso && !inCorso;
  const approvata = ["attiva", "sospesa"].includes(statoCampagna);
  const ammessi = post.interventi ?? [];

  const haImmagineAi =
    post.riempitivo === "immagine_ai" ||
    (post.versione_corrente?.foto ?? []).some(
      (f) =>
        (f as { origine?: string }).origine === "creata_ai" ||
        (f as { origine?: string }).origine === "ai",
    );
  const haBloccoImmagineNonCreata =
    Array.isArray(post.versione_corrente?.errori_validazione) &&
    post.versione_corrente.errori_validazione.some(
      (e: unknown) =>
        (e as { regola?: string }).regola === "immagine_non_creata",
    );
  const puoRigenerareImmagine =
    ammessi.includes("rigenera_immagine") &&
    (haImmagineAi || haBloccoImmagineNonCreata);

  // Finché l'AI lavora si rilegge la pagina: la nuova versione compare da sola.
  useEffect(() => {
    if (!inCorso) return;
    const timer = setInterval(ricarica, ATTESA_AGGIORNAMENTO_MS);
    return () => clearInterval(timer);
  }, [inCorso, ricarica]);

  const dopoIntervento = () => {
    setFinestra(null);
    ricarica();
  };
  const chiudi = () => setFinestra(null);

  const fatte = rigenerazioniFatte(post);
  const rigenerazioniFinite =
    !inCorso &&
    post.stato === "da_approvare" &&
    statoCampagna === "in_revisione" &&
    !ammessi.includes("rigenera") &&
    fatte >= MAX_RIGENERAZIONI;

  return (
    <Stack gap="xs">
      {inCorso && (
        <Alert color="yellow" variant="light" py="xs">
          <Group gap="xs" wrap="nowrap">
            <Loader size="xs" color="yellow" />
            <Text size="sm">
              {post.intervento_in_corso === "rigenera_immagine"
                ? "Rigenerazione dell'immagine in corso"
                : "Rigenerazione del testo in corso"}
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

      {/* Congelato per l'MVP, ADR-114: la spunta 'va bene' sul post è nascosta */}

      {ammessi.length > 0 && (
        <Group gap="xs" wrap="wrap">
          {ammessi.includes("modifica") && (
            <Button
              size="xs"
              variant="light"
              onClick={() => setFinestra("modifica")}
            >
              Modifica a mano
            </Button>
          )}
          {ammessi.includes("rigenera") && (
            <Button
              size="xs"
              variant="light"
              onClick={() => setFinestra("rigenera")}
            >
              Rigenera testo
            </Button>
          )}
          {puoRigenerareImmagine && (
            <Button
              size="xs"
              variant="light"
              onClick={() => setFinestra("rigenera_immagine")}
            >
              Rigenera immagine
            </Button>
          )}
          {ammessi.includes("cambia_foto") && (
            <Button
              size="xs"
              variant="light"
              onClick={() => setFinestra("cambia_foto")}
            >
              Cambia immagine
            </Button>
          )}
          {ammessi.includes("sposta") && (
            <Button
              size="xs"
              variant="light"
              onClick={() => setFinestra("sposta")}
            >
              Sposta
            </Button>
          )}
          {ammessi.includes("annulla") && (
            <Button
              size="xs"
              variant="light"
              color="red"
              onClick={() => setFinestra("annulla")}
            >
              Annulla il post
            </Button>
          )}
          {ammessi.includes("rigenera") && (
            <Text size="xs" c="dimmed">
              Rigenerazioni: {fatte} di {MAX_RIGENERAZIONI}
            </Text>
          )}
        </Group>
      )}
      {ammessi.includes("riprogramma") && (
        <RiprogrammaPost post={post} ricarica={ricarica} />
      )}
      {rigenerazioniFinite && (
        <Text size="xs" c="dimmed">
          Limite di 3 rigenerazioni raggiunto. È disponibile la modifica a mano.
        </Text>
      )}
      {ammessi.length === 0 &&
        !inCorso &&
        post.stato === "approvato" &&
        approvata && (
          <Text size="xs" c="dimmed">
            Pubblicazione tra meno di 15 minuti: modifiche non più disponibili.
          </Text>
        )}

      {finestra === "modifica" && (
        <ModificaMano
          post={post}
          aperto
          approvata={approvata}
          chiudi={chiudi}
          fatto={dopoIntervento}
        />
      )}
      {finestra === "rigenera" && (
        <Rigenera post={post} chiudi={chiudi} fatto={dopoIntervento} />
      )}
      {(finestra === "cambia_foto" || finestra === "rigenera_immagine") && (
        <CambiaFoto
          post={post}
          approvata={approvata}
          apriSuAI={finestra === "rigenera_immagine"}
          chiudi={chiudi}
          fatto={dopoIntervento}
        />
      )}
      {finestra === "sposta" && (
        <Sposta post={post} chiudi={chiudi} fatto={dopoIntervento} />
      )}
      {finestra === "annulla" && (
        <AnnullaPost post={post} chiudi={chiudi} fatto={dopoIntervento} />
      )}
    </Stack>
  );
}
