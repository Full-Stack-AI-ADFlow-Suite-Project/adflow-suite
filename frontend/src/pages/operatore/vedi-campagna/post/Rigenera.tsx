/**
 * Rigenera il testo del post (R-03, R-04, R-31): una sola finestra. Con «Parti
 * da questo testo» vuoto l'AI riscrive da zero, con un testo parte da quello.
 */
import {
  Alert,
  Anchor,
  Button,
  Group,
  Modal,
  Stack,
  Text,
  Textarea,
} from "@mantine/core";
import { useState } from "react";

import { ApiErrore } from "../../../../api/http";
import { rigeneraPost } from "../../../../api/interventi";
import type { PostVista } from "../../../../api/revisione";
import { NOME_CANALE } from "../../campagna/util";

export function Rigenera({
  post,
  chiudi,
  fatto,
}: {
  post: PostVista;
  chiudi: () => void;
  fatto: () => void;
}) {
  const [partiDaTesto, setPartiDaTesto] = useState(false);
  const [proposto, setProposto] = useState("");
  const [nota, setNota] = useState("");
  const [occupato, setOccupato] = useState(false);
  const [errore, setErrore] = useState<string | null>(null);
  const daProposta = partiDaTesto && proposto.trim() !== "";

  const invia = async () => {
    setOccupato(true);
    setErrore(null);
    try {
      await rigeneraPost(
        post.post_id,
        daProposta ? "da_proposta" : "totale",
        daProposta ? proposto : null,
        nota.trim() || null,
      );
      fatto();
    } catch (e) {
      setErrore(
        e instanceof ApiErrore
          ? e.message
          : "Impossibile rigenerare il testo. Riprova.",
      );
    } finally {
      setOccupato(false);
    }
  };

  return (
    <Modal
      opened
      onClose={chiudi}
      title={`Rigenera testo · ${NOME_CANALE[post.canale] ?? post.canale}`}
      size="lg"
    >
      <Stack gap="sm">
        <Text size="sm" c="dimmed">
          L'AI riscrive il testo del post. Le foto restano le stesse e le
          versioni rifiutate le arrivano come "cosa non rifare". Conta come una
          delle 3 rigenerazioni del post, e finché lavora non si può toccare il
          post né approvare la campagna.
        </Text>
        <Textarea
          label="Indicazioni per l'AI (facoltative)"
          description="Per esempio: più caldo, meno lungo, nomina il sabato."
          value={nota}
          onChange={(e) => setNota(e.currentTarget.value)}
          autosize
          minRows={2}
          maxRows={5}
          data-autofocus
        />
        {partiDaTesto ? (
          <Textarea
            label="Parti da questo testo (facoltativo)"
            description="Se lo svuoti, l'AI riscrive da zero."
            value={proposto}
            onChange={(e) => setProposto(e.currentTarget.value)}
            autosize
            minRows={4}
            maxRows={12}
          />
        ) : (
          <Anchor
            component="button"
            type="button"
            size="sm"
            ta="left"
            onClick={() => {
              setProposto(post.versione_corrente?.testo ?? "");
              setPartiDaTesto(true);
            }}
          >
            Parti da questo testo
          </Anchor>
        )}
        {errore && (
          <Alert color="red" variant="light" py="xs">
            {errore}
          </Alert>
        )}
        <Group justify="flex-end">
          <Button variant="default" onClick={chiudi}>
            Annulla
          </Button>
          <Button color="verde" loading={occupato} onClick={() => void invia()}>
            Rigenera
          </Button>
        </Group>
      </Stack>
    </Modal>
  );
}
