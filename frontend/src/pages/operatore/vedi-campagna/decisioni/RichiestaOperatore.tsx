/**
 * Il riquadro della richiesta all'artigiano nella barra di decisione di Vedi
 * campagna (R-46): in attesa, con le foto ancora da caricare, oppure con la
 * risposta arrivata. La foto nuova la usa l'operatore con Cambia foto.
 */
import { Badge, Card, Group, Image, Stack, Text } from "@mantine/core";

import { urlFotoFile } from "../../../../api/archivio";
import type {
  CampagnaDettaglio,
  RichiestaArtigiano,
} from "../../../../api/campagne";
import { data } from "../../campagna/util";

const SEGNAPOSTO =
  "data:image/svg+xml;utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='80' height='64'%3E%3Crect width='80' height='64' fill='%23e9ecef'/%3E%3C/svg%3E";

function Miniatura({
  campagna,
  fotoId,
}: {
  campagna: CampagnaDettaglio;
  fotoId: number;
}) {
  const foto = campagna.gruppi
    .flatMap((g) => g.foto)
    .find((f) => f.id === fotoId);
  return (
    <Image
      src={foto ? urlFotoFile(foto.file, foto.id) : SEGNAPOSTO}
      alt={`Foto ${fotoId}`}
      h={64}
      w={80}
      radius="sm"
      fit="cover"
      fallbackSrc={SEGNAPOSTO}
    />
  );
}

export function RichiestaOperatore({
  campagna,
  richiesta,
}: {
  campagna: CampagnaDettaglio;
  richiesta: RichiestaArtigiano;
}) {
  if (richiesta.stato === "decaduta") return null;
  const inviata = richiesta.stato === "inviata";

  return (
    <Card
      withBorder
      radius="md"
      mt="md"
      bg="var(--mantine-color-yellow-light)"
      style={{ borderLeft: "4px solid var(--mantine-color-yellow-6)" }}
      aria-label="Richiesta all'artigiano"
    >
      <Stack gap="xs">
        <Group gap="xs">
          <Text fw={600}>
            {inviata
              ? `Risposta dell'artigiano · arrivata il ${data(
                  richiesta.inviata_il ?? richiesta.creata_il,
                )}`
              : "Richiesta all'artigiano · in attesa"}
          </Text>
          <Badge color={inviata ? "verde" : "yellow"} variant="light">
            {inviata ? "inviata" : "aperta"}
          </Badge>
        </Group>
        <Text size="sm" c="dimmed">
          Chiesta il {data(richiesta.creata_il)}
        </Text>
        <Text size="sm" style={{ whiteSpace: "pre-line" }}>
          {richiesta.domanda}
        </Text>
        {inviata && richiesta.risposta && (
          <Text size="sm" fw={500} style={{ whiteSpace: "pre-line" }}>
            «{richiesta.risposta}»
          </Text>
        )}
        {richiesta.foto.length > 0 && (
          <Group gap="md" align="flex-start">
            {richiesta.foto.map((f) => (
              <Stack key={f.foto_id} gap={4} align="center">
                {inviata ? (
                  <Group gap={6} wrap="nowrap">
                    <Miniatura campagna={campagna} fotoId={f.foto_id} />
                    <Text span c="dimmed">
                      →
                    </Text>
                    {f.nuova_foto_id != null ? (
                      <Miniatura campagna={campagna} fotoId={f.nuova_foto_id} />
                    ) : (
                      <Text size="xs" c="dimmed">
                        non caricata
                      </Text>
                    )}
                  </Group>
                ) : (
                  <Miniatura campagna={campagna} fotoId={f.foto_id} />
                )}
                {!inviata && (
                  <Badge
                    size="sm"
                    variant="light"
                    color={f.nuova_foto_id != null ? "verde" : "yellow"}
                  >
                    {f.nuova_foto_id != null ? "nuova arrivata" : "da caricare"}
                  </Badge>
                )}
              </Stack>
            ))}
          </Group>
        )}
        {inviata && richiesta.foto.length > 0 && (
          <Text size="sm">
            Usa Cambia foto sui post che usano la foto vecchia: la nuova è in
            cima all'elenco.
          </Text>
        )}
      </Stack>
    </Card>
  );
}
