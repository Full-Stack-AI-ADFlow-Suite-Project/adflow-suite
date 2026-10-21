/** Il piano editoriale sotto la decisione: strategia, sintesi per canale e verifiche. */
import {
  Card,
  Group,
  Spoiler,
  Stack,
  Text,
  Title,
  UnstyledButton,
} from "@mantine/core";
import { useState } from "react";

import type { Piano } from "../../../api/revisione";

export function PianoCard({ piano }: { piano: Piano | null }) {
  const [aperto, setAperto] = useState(true);
  return (
    <Card withBorder radius="lg" p="lg">
      <UnstyledButton onClick={() => setAperto((v) => !v)} w="100%">
        <Group justify="space-between">
          <Title order={2} size="h3">
            Il piano
          </Title>
          <Group gap={8}>
            <Text size="sm" c="dimmed">
              {aperto ? "− chiudi" : "+ apri"}
            </Text>
          </Group>
        </Group>
      </UnstyledButton>
      {aperto &&
        (!piano ? (
          <Text size="sm" c="dimmed" mt="sm">
            Il piano editoriale sarà disponibile al termine della generazione.
          </Text>
        ) : (
          <Stack gap="sm" mt="sm">
            <Text size="sm" c="dimmed">
              Numero {piano.numero}
              {piano.creata_il ? ` · ${piano.creata_il.slice(0, 10)}` : ""}
            </Text>
            <Text size="sm">
              <Spoiler
                maxHeight={80}
                showLabel="Leggi tutto"
                hideLabel="Chiudi"
                styles={{ content: { fontSize: "inherit" } }}
              >
                {piano.strategia}
              </Spoiler>
            </Text>
            {Array.isArray(piano.esito_controllo) && (
              <Stack gap={4} mt={4}>
                <Text size="sm" c="dimmed">
                  Verifiche del controllo:
                </Text>
                {piano.esito_controllo.map((v, i) => (
                  <Group key={i} gap={6} wrap="nowrap" align="flex-start">
                    <Text c="verde" size="sm" lh={1.3}>
                      ✓
                    </Text>
                    <Text size="sm" c="dimmed" lh={1.3}>
                      {String(v)}
                    </Text>
                  </Group>
                ))}
              </Stack>
            )}
          </Stack>
        ))}
    </Card>
  );
}
