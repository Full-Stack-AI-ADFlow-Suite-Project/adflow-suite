/**
 * L'elenco delle campagne a sezioni, uguale per l'artigiano e per l'operatore
 * (ADR-117, H6). Riceve i dati, le sezioni e il link di una campagna; non
 * chiama le API. Nell'artigiano usa le etichette di stato della pagina
 * Campagna, nell'operatore quelle di `StatoBadge`.
 */
import { Alert, Badge, Group, Paper, Stack, Text, Title } from "@mantine/core";
import { Link } from "react-router-dom";

import type { CampagnaElencoItem } from "../../api/campagne";
import { StatoBadge } from "../StatoBadge";
import type { Lato, Sezione } from "./sezioni";

const CANALE: Record<string, string> = {
  facebook: "Facebook",
  instagram: "Instagram",
};

/** Etichetta dello stato per l'artigiano e il colore del badge. */
const STATO_ARTIGIANO: Record<string, [string, string]> = {
  bozza: ["Bozza", "gray"],
  inviata: ["In lavorazione", "blue"],
  in_generazione: ["In lavorazione", "blue"],
  generazione_fallita: ["In lavorazione", "blue"],
  piano_da_rivedere: ["In lavorazione", "blue"],
  in_revisione: ["In lavorazione", "blue"],
  attiva: ["In corso", "green"],
  sospesa: ["Pubblicazioni ferme", "yellow"],
  conclusa: ["Conclusa", "gray"],
  annullata: ["Annullata dal consorzio", "gray"],
  scaduta: ["Scaduta", "red"],
  respinta: ["Respinta", "red"],
};

/** "2026-10-01" → "01/10". */
function giornoMese(iso: string): string {
  const [, mese, giorno] = iso.split("-");
  return `${giorno}/${mese}`;
}

function Riga({
  campagna,
  lato,
  link,
}: {
  campagna: CampagnaElencoItem;
  lato: Lato;
  link: string | null;
}) {
  const consorzioChiede =
    lato === "artigiano" && campagna.richiesta === "aperta";
  const [etichetta, colore] = STATO_ARTIGIANO[campagna.stato] ?? [
    campagna.stato,
    "gray",
  ];
  const canali = (campagna.canali ?? []).map((c) => CANALE[c] ?? c).join(", ");

  const contenuto = (
    <Group justify="space-between" wrap="wrap" gap="sm">
      <div style={{ minWidth: 0 }}>
        <Group gap="sm">
          <Text fw={600}>{campagna.titolo}</Text>
          {consorzioChiede ? (
            <Badge color="yellow" variant="filled">
              Il consorzio ti chiede…
            </Badge>
          ) : lato === "operatore" ? (
            <StatoBadge tipo="campagna" stato={campagna.stato} />
          ) : (
            <Badge color={colore} variant="light">
              {etichetta}
            </Badge>
          )}
        </Group>
        <Text size="sm" c="dimmed" mt={4}>
          {giornoMese(campagna.inizio)} – {giornoMese(campagna.fine)}
          {canali ? ` · ${canali}` : ""}
        </Text>
      </div>
      {link && (
        <Text size="sm" fw={600} c="blu">
          Apri →
        </Text>
      )}
    </Group>
  );

  return link ? (
    <Paper
      withBorder
      radius="md"
      p="md"
      component={Link}
      to={link}
      style={{ color: "inherit", textDecoration: "none" }}
    >
      {contenuto}
    </Paper>
  ) : (
    <Paper withBorder radius="md" p="md">
      {contenuto}
    </Paper>
  );
}

export function ElencoCampagne({
  sezioni,
  lato,
  link,
  vuoto = "Nessuna campagna.",
}: {
  sezioni: Sezione[];
  lato: Lato;
  /** Dove porta un clic su una campagna; `null`: la riga non si apre. */
  link: (campagna: CampagnaElencoItem) => string | null;
  vuoto?: string;
}) {
  if (sezioni.length === 0) {
    return (
      <Paper withBorder radius="md" p="lg" style={{ borderStyle: "dashed" }}>
        <Text c="dimmed" size="sm">
          {vuoto}
        </Text>
      </Paper>
    );
  }
  return (
    <Stack gap="xl">
      {sezioni.map((sezione) => (
        <section key={sezione.chiave} aria-label={sezione.titolo}>
          <Title order={2} size="h4" mb="sm">
            {sezione.titolo}
          </Title>
          {sezione.informativa ? (
            <Alert color="gray" variant="light">
              {sezione.campagne.map((c) => (
                <div key={c.id}>
                  Una campagna in bozza: <b>{c.titolo}</b>. La compila e la
                  invia l'artigiano; si apre dopo l'invio.
                </div>
              ))}
            </Alert>
          ) : (
            <Stack gap="sm">
              {sezione.campagne.map((c) => (
                <Riga key={c.id} campagna={c} lato={lato} link={link(c)} />
              ))}
            </Stack>
          )}
        </section>
      ))}
    </Stack>
  );
}
