/**
 * Le foto della campagna che il piano non usa, sotto la decisione di Vedi
 * campagna: chi approva vede subito quali foto sono rimaste fuori e perché
 * (non idonee, doppioni, in eccesso), senza aprire «Foto e profilo».
 */
import {
  Badge,
  Card,
  Group,
  Image,
  SimpleGrid,
  Stack,
  Text,
} from "@mantine/core";

import { urlFotoFile } from "../../../api/archivio";
import type { CampagnaDettaglio } from "../../../api/campagne";
import type {
  CausaNonUsata,
  FotoNonUsata,
  VediCampagna,
} from "../../../api/revisione";

const CAUSE: {
  causa: CausaNonUsata;
  titolo: string;
  colore: string;
  spiegazione: string;
}[] = [
  {
    causa: "non_idonea",
    titolo: "Non idonee",
    colore: "red",
    spiegazione:
      "L’analisi le scarta: tecnicamente non pubblicabili (sfocate, troppo scure o chiare, tagliate male) o senza il lavoro di una bottega.",
  },
  {
    causa: "doppione",
    titolo: "Doppioni",
    colore: "orange",
    spiegazione:
      "Quasi uguali a un’altra foto della serie: il piano usa la migliore delle due.",
  },
  {
    causa: "in_eccesso",
    titolo: "In eccesso",
    colore: "yellow",
    spiegazione:
      "Foto buone, ma più dei post chiesti: il piano usa quelle con il punteggio più alto.",
  },
  {
    causa: "non_analizzata",
    titolo: "Non analizzate",
    colore: "gray",
    spiegazione: "Senza analisi: il piano non le ha viste.",
  },
  {
    causa: "altro",
    titolo: "Altre",
    colore: "gray",
    spiegazione: "Immagini che il piano non usa più.",
  },
];

function Miniatura({ id, file }: { id: number; file?: string }) {
  return (
    <Image
      src={urlFotoFile(file ?? "", id)}
      alt={`Foto ${id}`}
      w={64}
      h={64}
      fit="cover"
      radius="sm"
      style={{ flexShrink: 0 }}
    />
  );
}

export function FotoEscluse({
  vista,
  campagna,
}: {
  vista: VediCampagna;
  campagna: CampagnaDettaglio | null;
}) {
  const tutte: FotoNonUsata[] = vista.foto_non_usate.flatMap((g) => g.foto);
  if (tutte.length === 0) return null;
  const file = new Map(
    (campagna?.gruppi ?? []).flatMap((g) => g.foto).map((f) => [f.id, f.file]),
  );
  const chiesti = Math.max(
    0,
    ...Object.values(campagna?.post_chiesti_per_canale ?? {}),
  );

  return (
    <Card withBorder radius="lg" p="lg" aria-label="Foto escluse dal piano">
      <Group justify="space-between" wrap="wrap">
        <div>
          <Text fw={600}>Foto escluse dal piano · {tutte.length}</Text>
          <Text size="xs" c="dimmed">
            Post chiesti per canale: {chiesti}. Le foto qui sotto non sono in
            nessun post.
          </Text>
        </div>
        <Group gap={6}>
          {CAUSE.map((c) => {
            const n = tutte.filter((f) => f.causa === c.causa).length;
            return n > 0 ? (
              <Badge key={c.causa} color={c.colore} variant="light">
                {n} {c.titolo.toLowerCase()}
              </Badge>
            ) : null;
          })}
        </Group>
      </Group>
      <Stack gap="md" mt="md">
        {CAUSE.map((c) => {
          const lista = tutte.filter((f) => f.causa === c.causa);
          if (lista.length === 0) return null;
          return (
            <div key={c.causa}>
              <Text size="sm" fw={500}>
                {c.titolo} ({lista.length})
              </Text>
              <Text size="xs" c="dimmed" mb={6}>
                {c.spiegazione}
              </Text>
              <SimpleGrid cols={{ base: 1, sm: 2 }} spacing="xs">
                {lista.map((f) => (
                  <Group
                    key={f.foto_id}
                    wrap="nowrap"
                    gap="sm"
                    align="flex-start"
                  >
                    <Miniatura id={f.foto_id} file={file.get(f.foto_id)} />
                    <div style={{ minWidth: 0 }}>
                      <Text
                        size="xs"
                        ff="monospace"
                        style={{ wordBreak: "break-all" }}
                      >
                        {file.get(f.foto_id) ?? `foto ${f.foto_id}`}
                      </Text>
                      {f.causa === "non_idonea" && f.motivo && (
                        <Text size="xs">{f.motivo}</Text>
                      )}
                      {f.causa === "doppione" && f.simile_a != null && (
                        <Group gap={6} mt={2} wrap="nowrap">
                          <Text size="xs">Simile a</Text>
                          <Miniatura
                            id={f.simile_a}
                            file={file.get(f.simile_a)}
                          />
                        </Group>
                      )}
                    </div>
                  </Group>
                ))}
              </SimpleGrid>
            </div>
          );
        })}
      </Stack>
    </Card>
  );
}
