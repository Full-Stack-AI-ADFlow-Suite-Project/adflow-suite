/**
 * Sposta il post (R-36): nuova data e ora, dentro il periodo della campagna e
 * almeno 15 minuti da adesso. Il testo e la foto restano; il periodo lo
 * controlla l'API.
 */
import {
  Alert,
  Button,
  Group,
  Modal,
  Stack,
  Text,
  TextInput,
} from "@mantine/core";
import { useState } from "react";

import { sposta } from "../../../../api/interventi";
import type { PostVista } from "../../../../api/revisione";
import { NOME_CANALE } from "../../campagna/util";
import { useInvio } from "../decisioni/useInvio";

export function Sposta({
  post,
  chiudi,
  fatto,
}: {
  post: PostVista;
  chiudi: () => void;
  fatto: () => void;
}) {
  const [quando, setQuando] = useState("");
  const { occupato, errore, esegui } = useInvio(fatto);

  return (
    <Modal
      opened
      onClose={chiudi}
      title={`Sposta il post · ${NOME_CANALE[post.canale] ?? post.canale}`}
    >
      <Stack gap="sm">
        <Text size="sm" c="dimmed">
          Dentro il periodo della campagna, almeno 15 minuti da adesso.
        </Text>
        <TextInput
          type="datetime-local"
          label="Nuova data e ora"
          value={quando}
          onChange={(e) => setQuando(e.currentTarget.value)}
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
            color="verde"
            loading={occupato}
            disabled={!quando}
            onClick={() => void esegui(() => sposta(post.post_id, quando))}
          >
            Sposta
          </Button>
        </Group>
      </Stack>
    </Modal>
  );
}
