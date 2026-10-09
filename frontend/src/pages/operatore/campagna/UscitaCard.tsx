/** Una uscita del piano: tema in alto e i post dei canali affiancati. */
import { Card, Group, SimpleGrid, Stack, Text, Title } from "@mantine/core";

import type { Uscita } from "../../../api/revisione";
import { PostCard } from "./PostCard";

export function UscitaCard({
  uscita,
  bottega,
  citta,
}: {
  uscita: Uscita;
  bottega: string;
  citta: string | null;
}) {
  return (
    <Card withBorder radius="lg" p="lg">
      <Stack gap="md">
        <Group justify="space-between" wrap="wrap">
          <div>
            <Text size="xs" c="dimmed">
              Uscita {uscita.numero}
            </Text>
            <Title order={2} size="h3">
              {uscita.tema}
            </Title>
          </div>
          <Group gap="md" wrap="wrap">
            {uscita.gruppo?.descrizione && (
              <Text size="sm" c="dimmed">
                Gruppo · {uscita.gruppo.descrizione}
              </Text>
            )}
            {uscita.gruppo?.da_usare_il && (
              <Text size="xs" c="yellow" fw={500}>
                Da usare entro il {uscita.gruppo.da_usare_il}
              </Text>
            )}
          </Group>
        </Group>
        <SimpleGrid cols={{ base: 1, md: 2 }} spacing="md">
          {uscita.post.map((p) => (
            <PostCard
              key={p.post_id}
              post={p}
              bottega={bottega}
              citta={citta}
              tema={uscita.tema}
            />
          ))}
        </SimpleGrid>
      </Stack>
    </Card>
  );
}
