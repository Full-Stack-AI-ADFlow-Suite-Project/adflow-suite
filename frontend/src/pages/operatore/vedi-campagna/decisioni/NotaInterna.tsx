// Congelato per l'MVP, ADR-114: non estendere.
/** Nota interna (R-32): in ogni stato dopo l'invio, la leggono solo gli operatori. */
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

import { aggiungiNota } from "../../../../api/decisioni";
import { useInvio } from "./useInvio";

export function NotaInterna({
  campagnaId,
  chiudi,
  fatto,
}: {
  campagnaId: number;
  chiudi: () => void;
  fatto: () => void;
}) {
  const [nota, setNota] = useState("");
  const { occupato, errore, esegui } = useInvio(fatto);

  return (
    <Modal opened onClose={chiudi} title="Nota interna" size="lg">
      <Stack gap="sm">
        <Text size="sm" c="dimmed">
          La leggono solo gli operatori. Non cambia lo stato della campagna e
          non parte nessuna email.
        </Text>
        <Textarea
          label="Nota"
          value={nota}
          onChange={(e) => setNota(e.currentTarget.value)}
          autosize
          minRows={3}
          maxRows={8}
          data-autofocus
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
          <Button
            color="verde"
            loading={occupato}
            onClick={() => void esegui(() => aggiungiNota(campagnaId, nota))}
          >
            Salva la nota
          </Button>
        </Group>
      </Stack>
    </Modal>
  );
}
