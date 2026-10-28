/**
 * Chiedi all'artigiano (R-46): una domanda e da 0 a 3 foto caricate da
 * sostituire. La campagna resta in revisione e si può approvare o respingere
 * quando si vuole; il sistema non manda email.
 */
import {
  Alert,
  Button,
  Checkbox,
  Group,
  Image,
  Modal,
  Stack,
  Text,
  Textarea,
} from "@mantine/core";
import { useState } from "react";

import { urlFotoFile } from "../../../../api/archivio";
import type { CampagnaDettaglio } from "../../../../api/campagne";
import { chiediArtigiano } from "../../../../api/campagne";
import { data } from "../../campagna/util";
import { useInvio } from "./useInvio";

/** Quante foto si possono chiedere in una richiesta (R-46). */
const MAX_FOTO = 3;

export function ChiediArtigiano({
  campagna,
  chiudi,
  fatto,
}: {
  campagna: CampagnaDettaglio;
  chiudi: () => void;
  fatto: () => void;
}) {
  const [domanda, setDomanda] = useState("");
  const [scelte, setScelte] = useState<number[]>([]);
  const { occupato, errore, esegui } = useInvio(fatto);

  const gruppi = campagna.gruppi
    .map((g) => ({
      ...g,
      foto: g.foto.filter((f) => f.origine === "caricata"),
    }))
    .filter((g) => g.foto.length > 0);
  const scambia = (id: number) =>
    setScelte((s) =>
      s.includes(id)
        ? s.filter((x) => x !== id)
        : s.length < MAX_FOTO
        ? [...s, id]
        : s,
    );
  const aperta =
    campagna.richiesta?.stato === "aperta" ? campagna.richiesta : null;

  return (
    <Modal opened onClose={chiudi} title="Chiedi all'artigiano" size="lg">
      <Stack gap="sm">
        <Text size="sm" c="dimmed">
          La campagna resta in revisione. La richiesta non blocca l’approvazione
          né il rifiuto. Avvisa tu l'artigiano: il sistema non manda email.
        </Text>
        {aperta && (
          <Alert color="yellow" variant="light" py="xs">
            Sostituisce la richiesta aperta del {data(aperta.creata_il)}.
          </Alert>
        )}
        <Textarea
          label="Domanda per l'artigiano"
          placeholder="La foto del vaso mostra una cliente: puoi mandarne una senza persone?"
          value={domanda}
          onChange={(e) => setDomanda(e.currentTarget.value)}
          autosize
          minRows={3}
          maxRows={8}
          withAsterisk
          data-autofocus
        />
        <Stack gap={6}>
          <Group justify="space-between">
            <Text size="sm" fw={500}>
              Foto da sostituire (facoltative)
            </Text>
            <Text size="xs" c="dimmed">
              {scelte.length} di {MAX_FOTO}
            </Text>
          </Group>
          {gruppi.length === 0 && (
            <Text size="sm" c="dimmed">
              La campagna non ha foto caricate.
            </Text>
          )}
          {gruppi.map((g) => (
            <Stack key={g.id} gap={4}>
              <Text size="xs" c="dimmed">
                {g.descrizione ?? "Gruppo senza descrizione"}
              </Text>
              <Group gap="sm">
                {g.foto.map((f) => (
                  <Checkbox.Card
                    key={f.id}
                    checked={scelte.includes(f.id)}
                    onClick={() => scambia(f.id)}
                    radius="md"
                    p={6}
                    w={96}
                  >
                    <Stack gap={4} align="center">
                      <Image
                        src={urlFotoFile(f.file, f.id)}
                        h={64}
                        w={80}
                        radius="sm"
                        fit="cover"
                        fallbackSrc="data:image/svg+xml;utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='80' height='64'%3E%3Crect width='80' height='64' fill='%23e9ecef'/%3E%3C/svg%3E"
                      />
                      <Checkbox.Indicator />
                      <Text size="xs" c="dimmed">
                        Foto {f.id}
                      </Text>
                    </Stack>
                  </Checkbox.Card>
                ))}
              </Group>
            </Stack>
          ))}
        </Stack>
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
            disabled={!domanda.trim()}
            onClick={() =>
              void esegui(() => chiediArtigiano(campagna.id, domanda, scelte))
            }
          >
            Chiedi
          </Button>
        </Group>
      </Stack>
    </Modal>
  );
}
