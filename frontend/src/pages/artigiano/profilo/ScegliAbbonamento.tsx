/**
 * La scelta dell'abbonamento nel profilo: quanti post a settimana per ogni
 * social. Schede grandi, una per abbonamento, ben visibili; la scelta vale per
 * tutte le campagne (il periodo di ogni campagna dà poi i post totali).
 */
import { Group, Radio, SimpleGrid, Text } from "@mantine/core";

import { ABBONAMENTI } from "../../../api/abbonamento";

export function ScegliAbbonamento({
  value,
  onChange,
  error,
}: {
  value: string | null;
  onChange: (v: string) => void;
  error?: string;
}) {
  return (
    <Radio.Group
      value={value}
      onChange={onChange}
      label="Il tuo abbonamento: quanti post a settimana su ogni social?"
      description="Ogni campagna ne ricava i post totali in base alle date che scegli."
      error={error}
      withAsterisk
    >
      <SimpleGrid cols={{ base: 1, sm: 2 }} mt="xs">
        {ABBONAMENTI.map((a) => (
          <Radio.Card
            key={a.value}
            value={a.value}
            radius="md"
            p="md"
            withBorder
            style={{ minHeight: 64 }}
          >
            <Group wrap="nowrap" align="flex-start">
              <Radio.Indicator mt={4} />
              <div>
                <Text fw={700} size="lg" lh={1.2}>
                  {a.titolo}
                </Text>
                <Text size="xs" c="dimmed">
                  {a.nota}
                </Text>
              </div>
            </Group>
          </Radio.Card>
        ))}
      </SimpleGrid>
    </Radio.Group>
  );
}
