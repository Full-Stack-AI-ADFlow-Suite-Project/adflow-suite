/**
 * Togli il canale (R-18): i suoi post si scartano, la nota la legge anche
 * l'artigiano, la scelta è definitiva e resta sempre almeno un canale.
 */
import {
  Alert,
  Button,
  Group,
  Modal,
  Radio,
  Stack,
  Text,
  Textarea,
} from "@mantine/core";
import { useState } from "react";

import { togliCanale } from "../../../../api/decisioni";
import { NOME_CANALE } from "../../campagna/util";
import { useInvio } from "./useInvio";

export function TogliCanale({
  campagnaId,
  canali,
  generazioneFallita,
  chiudi,
  fatto,
}: {
  campagnaId: number;
  /** I canali ancora in campagna (almeno due, altrimenti il pulsante non c'è). */
  canali: string[];
  generazioneFallita: boolean;
  chiudi: () => void;
  fatto: () => void;
}) {
  const [canale, setCanale] = useState("");
  const [nota, setNota] = useState("");
  const { occupato, errore, esegui } = useInvio(fatto);

  return (
    <Modal opened onClose={chiudi} title="Togli il canale" size="lg">
      <Stack gap="sm">
        <Alert color="yellow" variant="light" py="xs">
          È definitivo: i post di quel canale vengono scartati e non tornano.
          {generazioneFallita
            ? " La generazione riparte per i canali che restano."
            : ""}
        </Alert>
        <Radio.Group
          label="Canale da togliere"
          value={canale}
          onChange={setCanale}
          withAsterisk
        >
          <Stack gap={6} mt={6}>
            {canali.map((c) => (
              <Radio key={c} value={c} label={NOME_CANALE[c] ?? c} />
            ))}
          </Stack>
        </Radio.Group>
        <Textarea
          label="Nota"
          description="La legge anche l'artigiano: dì perché il canale non va."
          value={nota}
          onChange={(e) => setNota(e.currentTarget.value)}
          autosize
          minRows={3}
          maxRows={8}
          withAsterisk
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
            color="red"
            loading={occupato}
            disabled={!canale}
            onClick={() =>
              void esegui(() => togliCanale(campagnaId, canale, nota))
            }
          >
            Togli {canale ? NOME_CANALE[canale] ?? canale : "il canale"}
          </Button>
        </Group>
        <Text size="xs" c="dimmed">
          Un canale alla volta; l'ultimo non si può togliere.
        </Text>
      </Stack>
    </Modal>
  );
}
