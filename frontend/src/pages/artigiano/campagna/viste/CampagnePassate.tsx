/** "Campagne passate" in fondo alla pagina: chiuse e non più da sostituire (spec §4). */
import {
  Badge,
  Group,
  Paper,
  Stack,
  Text,
  UnstyledButton,
} from "@mantine/core";

import type { CampagnaElencoItem } from "../../../../api/campagne";

const ESITO: Record<string, string> = {
  conclusa: "conclusa",
  annullata: "annullata dal consorzio",
  respinta: "respinta",
  scaduta: "scaduta",
};

function giorno(iso: string): string {
  return new Date(iso + "T00:00:00").toLocaleDateString("it-IT");
}

export function CampagnePassate({
  passate,
  apertaId,
  onApri,
}: {
  passate: CampagnaElencoItem[];
  apertaId: number | null;
  onApri: (c: CampagnaElencoItem) => void;
}) {
  if (passate.length === 0) return null;
  return (
    <Stack gap="xs" mt="xl">
      <Text fw={600}>Campagne passate</Text>
      {passate.map((c) => (
        <UnstyledButton key={c.id} onClick={() => onApri(c)}>
          <Paper
            withBorder
            radius="md"
            p="sm"
            style={
              c.id === apertaId
                ? { borderColor: "var(--mantine-color-verde-6)" }
                : undefined
            }
          >
            <Group justify="space-between" wrap="wrap">
              <div>
                <Text size="sm" fw={500}>
                  {c.titolo}
                </Text>
                <Text size="xs" c="dimmed">
                  {giorno(c.inizio)} → {giorno(c.fine)}
                </Text>
              </div>
              <Badge variant="light" color="gray">
                {ESITO[c.stato] ?? c.stato}
              </Badge>
            </Group>
          </Paper>
        </UnstyledButton>
      ))}
    </Stack>
  );
}
