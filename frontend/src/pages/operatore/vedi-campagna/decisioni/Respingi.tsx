/**
 * Respingi (R-18): motivo `foto` o `altro`, nota obbligatoria e, con `foto`, le
 * foto da rifare. Vale da `in_revisione` e da `piano_da_rivedere`; i post
 * restano nello storico come scartati e l'artigiano riceve un'email.
 */
import {
  Alert,
  Button,
  Checkbox,
  Group,
  Image,
  Modal,
  Radio,
  Stack,
  Text,
  Textarea,
} from "@mantine/core";
import { useState } from "react";

import { respingi } from "../../../../api/decisioni";
import type { MotivoRespinta } from "../../../../api/decisioni";
import type { CampagnaDettaglio } from "../../../../api/campagne";
import { urlFotoFile } from "../../../../api/archivio";
import { useInvio } from "./useInvio";

export function Respingi({
  campagna,
  chiudi,
  fatto,
}: {
  campagna: CampagnaDettaglio;
  chiudi: () => void;
  fatto: () => void;
}) {
  const [motivo, setMotivo] = useState<MotivoRespinta | "">("");
  const [nota, setNota] = useState("");
  const [segnate, setSegnate] = useState<number[]>([]);
  const { occupato, errore, esegui } = useInvio(fatto);

  const gruppi = campagna.gruppi.filter((g) => g.foto.length > 0);
  const scambia = (id: number, scelta: boolean) =>
    setSegnate((s) => (scelta ? [...s, id] : s.filter((x) => x !== id)));

  return (
    <Modal opened onClose={chiudi} title="Respingi la campagna" size="lg">
      <Stack gap="sm">
        <Text size="sm" c="dimmed">
          La campagna si chiude: i post restano nello storico, l'artigiano
          riceve un'email con il motivo e la nota e ne crea una nuova.
        </Text>
        <Radio.Group
          label="Motivo"
          value={motivo}
          onChange={(v) => setMotivo(v as MotivoRespinta)}
          withAsterisk
        >
          <Stack gap={6} mt={6}>
            <Radio
              value="foto"
              label="Foto insufficienti o di qualità non adatta"
            />
            <Radio value="altro" label="Altro" />
          </Stack>
        </Radio.Group>
        <Textarea
          label="Nota per l'artigiano"
          description="Indicare cosa rifare o correggere."
          value={nota}
          onChange={(e) => setNota(e.currentTarget.value)}
          autosize
          minRows={3}
          maxRows={8}
          withAsterisk
        />
        {motivo === "foto" && (
          <Stack gap={6}>
            <Text size="sm" fw={500}>
              Foto da rifare
            </Text>
            {gruppi.length === 0 && (
              <Text size="sm" c="dimmed">
                La campagna non ha foto.
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
                      checked={segnate.includes(f.id)}
                      onClick={() => scambia(f.id, !segnate.includes(f.id))}
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
          <Button
            color="red"
            loading={occupato}
            disabled={!motivo}
            onClick={() =>
              void esegui(() =>
                respingi(
                  campagna.id,
                  motivo as MotivoRespinta,
                  nota,
                  motivo === "foto" ? segnate : [],
                ),
              )
            }
          >
            Respingi la campagna
          </Button>
        </Group>
      </Stack>
    </Modal>
  );
}
