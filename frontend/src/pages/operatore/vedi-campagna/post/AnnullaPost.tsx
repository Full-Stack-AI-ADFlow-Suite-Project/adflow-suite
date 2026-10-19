/**
 * Annulla il post (R-36): un post approvato che esce tra almeno 15 minuti non
 * esce più, senza sospendere la campagna. La nota è obbligatoria.
 */
import { Alert, Button, Group, Modal, Stack, Textarea } from "@mantine/core";
import { useState } from "react";

import { annullaPost } from "../../../../api/interventi";
import type { PostVista } from "../../../../api/revisione";
import { NOME_CANALE } from "../../campagna/util";
import { useInvio } from "../decisioni/useInvio";

export function AnnullaPost({
  post,
  chiudi,
  fatto,
}: {
  post: PostVista;
  chiudi: () => void;
  fatto: () => void;
}) {
  const [nota, setNota] = useState("");
  const { occupato, errore, esegui } = useInvio(fatto);

  return (
    <Modal
      opened
      onClose={chiudi}
      title={`Annulla il post · ${NOME_CANALE[post.canale] ?? post.canale}`}
    >
      <Stack gap="sm">
        <Alert color="red" variant="light" py="xs">
          Il post non esce più e non torna indietro.
        </Alert>
        <Textarea
          label="Perché non deve uscire?"
          value={nota}
          onChange={(e) => setNota(e.currentTarget.value)}
          autosize
          minRows={3}
          withAsterisk
          data-autofocus
        />
        {errore && (
          <Alert color="red" variant="light" py="xs">
            {errore}
          </Alert>
        )}
        <Group justify="flex-end">
          <Button variant="default" onClick={chiudi}>
            Indietro
          </Button>
          <Button
            color="red"
            loading={occupato}
            disabled={!nota.trim()}
            onClick={() => void esegui(() => annullaPost(post.post_id, nota))}
          >
            Annulla il post
          </Button>
        </Group>
      </Stack>
    </Modal>
  );
}
