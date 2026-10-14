// Congelato per l'MVP, ADR-114: non estendere.
/**
 * Riprogramma un post fallito (R-34): in campagna attiva o sospesa torna
 * approvato con una nuova data e ora, dentro il periodo e almeno 15 minuti da
 * adesso. Il contenuto non cambia. Il periodo lo controlla l'API.
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

import { riprogramma } from "../../../../api/decisioni";
import type { PostVista } from "../../../../api/revisione";
import { NOME_CANALE } from "../../campagna/util";
import { useInvio } from "./useInvio";

export function RiprogrammaPost({
  post,
  ricarica,
}: {
  post: PostVista;
  ricarica: () => void;
}) {
  const [aperto, setAperto] = useState(false);
  const [quando, setQuando] = useState("");
  const { occupato, errore, esegui } = useInvio(() => {
    setAperto(false);
    ricarica();
  });

  return (
    <>
      <Group gap="xs">
        <Button size="xs" variant="default" onClick={() => setAperto(true)}>
          Riprogramma
        </Button>
        <Text size="xs" c="dimmed">
          Non è stato pubblicato: puoi darle una nuova data.
        </Text>
      </Group>
      {aperto && (
        <Modal
          opened
          onClose={() => setAperto(false)}
          title={`Riprogramma · ${NOME_CANALE[post.canale] ?? post.canale}`}
        >
          <Stack gap="sm">
            <Text size="sm" c="dimmed">
              Il post torna approvato con la stessa versione. La data deve
              cadere dentro il periodo della campagna e almeno 15 minuti da
              adesso.
            </Text>
            <TextInput
              type="datetime-local"
              label="Nuova data e ora"
              value={quando}
              onChange={(e) => setQuando(e.currentTarget.value)}
              withAsterisk
            />
            {errore && (
              <Alert color="red" variant="light" py="xs">
                {errore}
              </Alert>
            )}
            <Group justify="flex-end">
              <Button variant="default" onClick={() => setAperto(false)}>
                Annulla
              </Button>
              <Button
                color="verde"
                loading={occupato}
                disabled={!quando}
                onClick={() =>
                  void esegui(() => riprogramma(post.post_id, quando))
                }
              >
                Riprogramma
              </Button>
            </Group>
          </Stack>
        </Modal>
      )}
    </>
  );
}
