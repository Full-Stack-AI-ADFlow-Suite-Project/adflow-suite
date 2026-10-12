/** Rigenera il testo del post, da zero o da un testo proposto (R-03, R-04, R-31). */
import {
  Alert,
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
import type { ModalitaRigenerazione } from "../../../../api/interventi";
import type { PostVista } from "../../../../api/revisione";
import { NOME_CANALE } from "../../campagna/util";

export function Rigenera({
  post,
  modalita,
  chiudi,
  fatto,
}: {
  post: PostVista;
  /** Null = la finestra è chiusa. */
  modalita: ModalitaRigenerazione | null;
  chiudi: () => void;
  fatto: () => void;
}) {
  const [proposto, setProposto] = useState("");
  const [nota, setNota] = useState("");
  const [occupato, setOccupato] = useState(false);
  const [errore, setErrore] = useState<string | null>(null);
  const daProposta = modalita === "da_proposta";

  const invia = async () => {
    if (!modalita) return;
    setOccupato(true);
    setErrore(null);
    try {
      await rigeneraPost(
        post.post_id,
        modalita,
        daProposta ? proposto : null,
        nota.trim() || null,
      );
      setProposto("");
      setNota("");
      fatto();
    } catch (e) {
      setErrore(
        e instanceof ApiErrore ? e.message : "Non sono riuscita a rigenerare.",
      );
    } finally {
      setOccupato(false);
    }
  };

  return (
    <Modal
      opened={modalita !== null}
      onClose={chiudi}
      title={`${
        daProposta ? "Rigenera da testo proposto" : "Rigenera da zero"
      } · ${NOME_CANALE[post.canale] ?? post.canale}`}
      size="lg"
    >
      <Stack gap="sm">
        <Text size="sm" c="dimmed">
          {daProposta
            ? "L'AI riscrive il post partendo dal tuo testo."
            : "L'AI riscrive il post da capo."}{" "}
          Le foto restano le stesse e le versioni rifiutate le arrivano come
          "cosa non rifare". Conta come una delle 3 rigenerazioni del post, e
          finché lavora non si può toccare il post né approvare la campagna.
        </Text>
        {daProposta && (
          <Textarea
            label="Testo proposto"
            value={proposto}
            onChange={(e) => setProposto(e.currentTarget.value)}
            autosize
            minRows={4}
            maxRows={12}
            required
            data-autofocus
          />
        )}
        <Textarea
          label="Nota per l'AI (facoltativa)"
          description="Per esempio: più caldo, meno lungo, nomina il sabato."
          value={nota}
          onChange={(e) => setNota(e.currentTarget.value)}
          autosize
          minRows={2}
          maxRows={5}
        />
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
