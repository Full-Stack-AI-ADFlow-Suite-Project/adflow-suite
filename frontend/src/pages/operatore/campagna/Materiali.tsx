/**
 * Il pannello Foto e profilo di Vedi campagna: gruppi e foto con esito
 * (usata / non usata / in archivio), cartoline, richiesta dell'artigiano,
 * fotografia del profilo all'invio e storico delle decisioni.
 */
import {
  Badge,
  Box,
  Card,
  Divider,
  Group,
  Paper,
  SimpleGrid,
  Stack,
  Text,
  Title,
} from "@mantine/core";

import type { CampagnaDettaglio } from "../../../api/campagne";
import type { VediCampagna } from "../../../api/revisione";
import { data, NOME_CANALE } from "./util";

const FREQUENZE: Record<string, string> = {
  f1_2: "1–2 post a settimana",
  f3_4: "3–4 post a settimana",
  f5_piu: "5 o più post a settimana",
};

const ESITI: Record<string, string> = {
  approvata: "Approvata",
  proseguita: "Proseguita",
  respinta: "Respinta",
  riaperta: "Riaperta",
};

export function Materiali({
  campagna,
  vista,
}: {
  campagna: CampagnaDettaglio;
  vista: VediCampagna;
}) {
  // dove è finita ogni foto: uscita e canale dei post che la usano
  const usi = new Map<number, string[]>();
  for (const u of vista.uscite)
    for (const p of u.post)
      for (const f of p.versione_corrente?.foto ?? []) {
        const l = usi.get(f.foto_id) ?? [];
        l.push(
          `U${u.numero} ${(NOME_CANALE[p.canale] ?? p.canale).slice(0, 2)}`,
        );
        usi.set(f.foto_id, l);
      }

  const nonUsate = new Map<number, string>();
  for (const g of vista.foto_non_usate)
    for (const f of g.foto) nonUsate.set(f.foto_id, f.motivo ?? "senza motivo");

  const cartoline = vista.uscite
    .flatMap((u) =>
      u.post
        .filter((p) => p.riempitivo === "cartolina")
        .map((p) => ({ uscita: u.numero, post: p })),
    )
    .reduce<{ uscita: number; tema: string; canali: string[] }[]>((acc, x) => {
      const u = vista.uscite.find((u) => u.numero === x.uscita);
      const v = acc.find((e) => e.uscita === x.uscita);
      if (v) v.canali.push(NOME_CANALE[x.post.canale] ?? x.post.canale);
      else
        acc.push({
          uscita: x.uscita,
          tema: u?.tema ?? "",
          canali: [NOME_CANALE[x.post.canale] ?? x.post.canale],
        });
      return acc;
    }, []);

  const snap = campagna.profilo_snapshot;

  return (
    <SimpleGrid cols={{ base: 1, md: 2 }} spacing="md">
      <Stack gap="md">
        {campagna.gruppi.map((g) => (
          <Card key={g.id} withBorder radius="lg" p="lg">
            <Text size="xs" c="dimmed">
              Gruppo{g.origine === "create_ai" ? " · creato con l'AI" : ""}
            </Text>
            <Text fw={600} mt={2}>
              {g.descrizione ?? "(senza descrizione)"}
            </Text>
            {g.da_usare_il && (
              <Text size="xs" c="yellow" fw={500} mt={4}>
                Da usare entro il {data(g.da_usare_il)}
              </Text>
            )}
            <Stack gap={6} mt="sm">
              {g.foto.map((f) => (
                <Paper
                  key={f.id}
                  withBorder
                  radius="md"
                  p="xs"
                  style={
                    f.da_usare
                      ? { border: "2px solid var(--mantine-color-yellow-5)" }
                      : undefined
                  }
                >
                  <Group justify="space-between" wrap="wrap">
                    <Text size="xs" ff="monospace">
                      {f.file}
                      {f.da_usare ? " ★" : ""}
                    </Text>
                    <Text size="xs" c="dimmed">
                      {f.larghezza}×{f.altezza}
                    </Text>
                  </Group>
                  <Group gap={6} mt={4} wrap="wrap">
                    {usi.get(f.id)?.map((u) => (
                      <Badge key={u} size="xs" variant="light">
                        {u}
                      </Badge>
                    ))}
                    {nonUsate.get(f.id) && (
                      <Badge size="xs" variant="light" color="gray">
                        non usata
                      </Badge>
                    )}
                  </Group>
                  {nonUsate.get(f.id) && (
                    <Text size="xs" c="dimmed" mt={4}>
                      non usata: {nonUsate.get(f.id)}
                    </Text>
                  )}
                  {!usi.get(f.id) && !nonUsate.get(f.id) && (
                    <Text size="xs" c="dimmed" mt={4}>
                      non usata: resta in archivio.
                    </Text>
                  )}
                </Paper>
              ))}
            </Stack>
          </Card>
        ))}
        {cartoline.length > 0 && (
          <Card withBorder radius="lg" p="lg">
            <Text size="xs" c="dimmed">
              Cartoline
            </Text>
            <Text fw={600} mt={2}>
              Disegnate, non foto
            </Text>
            <Stack gap={6} mt="sm">
              {cartoline.map((c) => (
                <Paper key={c.uscita} withBorder radius="md" p="xs">
                  <Text size="xs" ff="monospace">
                    cartolina-{c.uscita}.png
                  </Text>
                  <Text size="xs" c="dimmed">
                    Tema: {c.tema} · {c.canali.join(", ")}
                  </Text>
                  <Badge size="xs" variant="light" mt={4}>
                    U{c.uscita}
                  </Badge>
                </Paper>
              ))}
            </Stack>
          </Card>
        )}
      </Stack>

      <Stack gap="md">
        <Card withBorder radius="lg" p="lg">
          <Title order={3} size="h4">
            Che cosa ha chiesto l'artigiano
          </Title>
          <Stack gap={4} mt="sm">
            <Text size="sm">
              <Text span c="dimmed">
                Testo dell'artigiano:{" "}
              </Text>
              {campagna.descrizione ?? "—"}
            </Text>
            <Text size="sm">
              <Text span c="dimmed">
                Canali chiesti:{" "}
              </Text>
              {(campagna.canali ?? [])
                .map((c) => NOME_CANALE[c] ?? c)
                .join(", ")}
            </Text>
            <Text size="sm">
              <Text span c="dimmed">
                Ritmo chiesto:{" "}
              </Text>
              {campagna.frequenza
                ? FREQUENZE[campagna.frequenza] ?? campagna.frequenza
                : "—"}
            </Text>
            <Text size="sm">
              <Text span c="dimmed">
                Obiettivo:{" "}
              </Text>
              {campagna.obiettivo ?? "—"}
            </Text>
          </Stack>
        </Card>

        <Card withBorder radius="lg" p="lg">
          <Title order={3} size="h4">
            Profilo bottega · fotografia
          </Title>
          {snap ? (
            <>
              <Stack gap={4} mt="sm">
                <Text size="sm">
                  <Text span c="dimmed">
                    Bottega:{" "}
                  </Text>
                  {snap.nome} · {snap.citta ?? "—"}
                </Text>
                <Text size="sm">
                  <Text span c="dimmed">
                    Chi:{" "}
                  </Text>
                  {snap.referente ?? "—"}
                </Text>
                <Text size="sm">
                  <Text span c="dimmed">
                    Che cosa fa:{" "}
                  </Text>
                  {snap.tipo_prodotto}
                </Text>
                <Text size="sm">
                  <Text span c="dimmed">
                    Obiettivo:{" "}
                  </Text>
                  {snap.obiettivo}
                </Text>
                <Text size="sm">
                  <Text span c="dimmed">
                    Clienti:{" "}
                  </Text>
                  {snap.clienti_ideali ?? "—"}
                </Text>
                <Text size="sm">
                  <Text span c="dimmed">
                    Tono:{" "}
                  </Text>
                  {(snap.tono ?? []).join(", ") || "—"}
                </Text>
                {snap.vincoli && (
                  <Text size="sm">
                    <Text span c="dimmed">
                      Da non dire:{" "}
                    </Text>
                    {snap.vincoli}
                  </Text>
                )}
              </Stack>
              <Text size="xs" c="dimmed" mt="sm">
                È il profilo com'era all'invio, non quello di oggi.
              </Text>
            </>
          ) : (
            <Text size="sm" c="dimmed" mt="sm">
              Nessuna fotografia: la campagna è ancora una bozza.
            </Text>
          )}
        </Card>

        {(campagna.decisioni ?? []).length > 0 && (
          <Card withBorder radius="lg" p="lg">
            <Title order={3} size="h4">
              Storico decisioni
            </Title>
            <Stack gap={6} mt="sm">
              {[...(campagna.decisioni ?? [])].reverse().map((d, i) => (
                <Box key={d.id}>
                  {i > 0 && <Divider my={6} />}
                  <Text size="sm" fw={500}>
                    {ESITI[d.esito] ?? d.esito}
                    {d.canale ? ` · ${NOME_CANALE[d.canale] ?? d.canale}` : ""}
                  </Text>
                  <Text size="xs" c="dimmed">
                    {[d.motivo, d.nota].filter(Boolean).join(" — ")}
                  </Text>
                </Box>
              ))}
            </Stack>
          </Card>
        )}
      </Stack>
    </SimpleGrid>
  );
}
