/** Il piano editoriale sotto la decisione: strategia, sintesi per canale e verifiche. */
import {
  Badge,
  Card,
  Group,
  Spoiler,
  Stack,
  Text,
  Title,
  UnstyledButton,
} from "@mantine/core";
import { useState } from "react";

import type { Piano, PostVista, Uscita } from "../../../api/revisione";

function perCanale(uscite: Uscita[]): Map<string, PostVista[]> {
  const mappa = new Map<string, PostVista[]>();
  for (const u of uscite)
    for (const p of u.post) {
      const l = mappa.get(p.canale) ?? [];
      l.push(p);
      mappa.set(p.canale, l);
    }
  return mappa;
}

export function PianoCard({
  piano,
  uscite,
  costoAi,
}: {
  piano: Piano | null;
  uscite: Uscita[];
  costoAi?: number | null;
}) {
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
            Il piano si vedrà qui, quando ci sarà.
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
            <Stack gap={4}>
              {[...perCanale(uscite)].map(([canale, post]) => {
                const riempitivi = post.filter(
                  (p) =>
                    p.riempitivo === "immagine_ai" ||
                    p.riempitivo === "cartolina",
                ).length;
                const conFoto = post.length - riempitivi;
                return (
                  <Text key={canale} size="sm">
                    <Badge variant="light" ff="monospace" mr="xs">
                      {canale}
                    </Badge>
                    {post.length} post · {conFoto} con foto
                    {riempitivi > 0 && ` · ${riempitivi} con immagine AI`}
                  </Text>
                );
              })}
            </Stack>
            {costoAi != null && (
              <Text size="sm">
                <Text span fw={500}>
                  Costo AI della campagna:{" "}
                </Text>
                <b>{Number(costoAi).toFixed(2).replace(".", ",")} $</b>
                <Text span c="dimmed">
                  {" "}
                  · Stima del provider (R-44)
                </Text>
              </Text>
            )}
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
