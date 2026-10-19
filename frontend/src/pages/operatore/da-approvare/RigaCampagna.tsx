/**
 * Una riga di Campagne da approvare (R-38): la campagna con i conteggi dei
 * post, "entro quando" e l'ultima nota interna. Da qui si va in Vedi campagna.
 */
import { Badge, Box, Button, Card, Group, Text } from "@mantine/core";
import { Link } from "react-router-dom";

import type { CampagnaDaApprovare } from "../../../api/decisioni";
import { coloreCampagna, data, dataOra, NOME_CANALE } from "../campagna/util";

const BORDO: Record<string, string | undefined> = {
  in_revisione: "var(--mantine-color-yellow-6)",
  piano_da_rivedere: "var(--mantine-color-yellow-6)",
  generazione_fallita: "var(--mantine-color-red-6)",
};

export function RigaCampagna({ c }: { c: CampagnaDaApprovare }) {
  const n = c.conteggi;
  const riempitivi = Object.entries(n?.riempitivi ?? {}).filter(
    ([, quanti]) => quanti > 0,
  );

  return (
    <Card
      withBorder
      radius="md"
      p="lg"
      style={
        BORDO[c.stato]
          ? { borderLeft: `4px solid ${BORDO[c.stato]}` }
          : undefined
      }
    >
      <Group justify="space-between" align="flex-start" wrap="wrap">
        <Box style={{ flex: "1 1 420px" }}>
          <Text size="sm" c="dimmed">
            {c.bottega}
            {c.citta ? ` · ${c.citta}` : ""}
          </Text>
          <Group gap="sm" mt={4}>
            <Text fw={600} size="lg">
              {c.titolo}
            </Text>
            <Badge
              color={coloreCampagna(c.stato)}
              variant="light"
              ff="monospace"
            >
              {c.stato}
            </Badge>
            {c.richiesta === "aperta" && (
              <Badge color="yellow" variant="light">
                Richiesta aperta
              </Badge>
            )}
            {c.richiesta === "inviata" && (
              <Badge color="verde" variant="light">
                Risposta arrivata
              </Badge>
            )}
          </Group>
          <Text size="sm" c="dimmed" mt={6}>
            {data(c.inizio)} → {data(c.fine)} ·{" "}
            {(c.canali ?? []).map((x) => NOME_CANALE[x] ?? x).join(", ")}
          </Text>
          {c.entro_quando && (
            <Text size="sm" mt={6}>
              <b>Entro quando:</b> {dataOra(c.entro_quando)}
            </Text>
          )}
          {n && n.totale > 0 && (
            <Group gap={6} mt={8}>
              <Badge variant="light">{n.totale} post</Badge>
              <Badge variant="light">{n.da_approvare} da approvare</Badge>
              {n.da_rivedere > 0 && (
                <Badge color="red" variant="light">
                  {n.da_rivedere} da rivedere
                </Badge>
              )}
              {riempitivi.map(([canale, quanti]) => (
                <Badge key={canale} color="gray" variant="light">
                  {quanti} riempitiv{quanti === 1 ? "o" : "i"} ·{" "}
                  {NOME_CANALE[canale] ?? canale}
                </Badge>
              ))}
            </Group>
          )}
          {c.ultima_nota && (
            <Text size="sm" c="dimmed" mt={8} fs="italic">
              Ultima nota: {c.ultima_nota}
            </Text>
          )}
        </Box>
        <Button color="verde" component={Link} to={`/campagne/${c.id}`}>
          Vedi campagna →
        </Button>
      </Group>
    </Card>
  );
}
