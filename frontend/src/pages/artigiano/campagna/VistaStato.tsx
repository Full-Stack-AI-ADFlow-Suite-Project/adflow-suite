/**
 * Vista per stato della campagna dopo l'invio
 * (docs/appunti/pagine/AdFlow-campagna-stati.html). L'artigiano vede
 * l'esito del lavoro, mai il lavoro in corso: niente piano né post fino
 * all'approvazione (spec §4); calendario e metriche dagli sprint 3 e 4.
 */
import {
  Alert,
  Badge,
  Button,
  Group,
  List,
  Paper,
  Stack,
  Text,
  Title,
} from "@mantine/core";

import type { CampagnaDettaglio } from "../../../api/campagne";
import { Riga } from "./Riga";

const POST_A_SETTIMANA: Record<string, number> = {
  f1_2: 2,
  f3_4: 3,
  f5_piu: 5,
  decidete_voi: 3,
};

function dataOraIT(iso: string | null): string {
  if (!iso) return "—";
  const d = new Date(iso);
  const data = d.toLocaleDateString("it-IT");
  const ora = d.toLocaleTimeString("it-IT", {
    hour: "2-digit",
    minute: "2-digit",
  });
  return `${data} alle ${ora}`;
}

function Passi({
  voci,
}: {
  voci: { testo: string; segno: "done" | "now" | "todo" | "warn" }[];
}) {
  const segni = { done: "✓", now: "●", todo: "○", warn: "!" } as const;
  const colori = {
    done: undefined,
    now: "var(--mantine-color-verde-7)",
    todo: "var(--mantine-color-dimmed)",
    warn: "var(--mantine-color-orange-7)",
  } as const;
  return (
    <List spacing={6} mb="md" style={{ listStyle: "none" }}>
      {voci.map((v) => (
        <List.Item
          key={v.testo}
          c={colori[v.segno]}
          fw={v.segno === "now" ? 500 : 400}
        >
          <Text component="span" ff="monospace" mr={8}>
            {segni[v.segno]}
          </Text>
          {v.testo}
        </List.Item>
      ))}
    </List>
  );
}

function RiepilogoLettura({ campagna }: { campagna: CampagnaDettaglio }) {
  const nFoto = campagna.gruppi.reduce((n, g) => n + g.foto.length, 0);
  const postSett = POST_A_SETTIMANA[campagna.frequenza ?? ""] ?? 3;
  const chiesti = Math.max(
    0,
    ...Object.values(campagna.post_chiesti_per_canale),
  );
  return (
    <Stack gap={4} mt="md">
      <Riga
        nome="Periodo"
        valore={`${new Date(campagna.inizio + "T00:00:00").toLocaleDateString(
          "it-IT",
        )} → ${new Date(campagna.fine + "T00:00:00").toLocaleDateString(
          "it-IT",
        )}`}
      />
      <Riga nome="Canali" valore={(campagna.canali ?? []).join(", ")} />
      <Riga
        nome="Ritmo scelto"
        valore={`${postSett} post a settimana per canale · ${chiesti} per canale nel periodo`}
      />
      <Riga
        nome="Foto"
        valore={`${nFoto} foto in ${campagna.gruppi.length} gruppi`}
      />
    </Stack>
  );
}

export function VistaStato({
  campagna,
  onNuovaCampagna,
}: {
  campagna: CampagnaDettaglio;
  onNuovaCampagna: () => void;
}) {
  const pubblicazione = `Pubblicazione dal ${new Date(
    campagna.inizio + "T00:00:00",
  ).toLocaleDateString("it-IT")}`;

  const corpo = () => {
    switch (campagna.stato) {
      case "inviata":
      case "in_generazione":
        return (
          <>
            <Alert color="verde" variant="light" mb="md">
              <b>Generazione dei post in corso…</b> Stiamo preparando i post di
              "{campagna.titolo}". Poi li rivede il consorzio: non devi fare
              nulla.
            </Alert>
            <Passi
              voci={[
                {
                  testo: `Inviata il ${dataOraIT(campagna.inviata_il)}`,
                  segno: "done",
                },
                { testo: "Preparazione dei post", segno: "now" },
                { testo: "Revisione del consorzio", segno: "todo" },
                { testo: pubblicazione, segno: "todo" },
              ]}
            />
            <RiepilogoLettura campagna={campagna} />
            <Text size="xs" c="dimmed" mt="sm">
              Dati e foto in sola lettura: dopo l'invio non si modificano.
            </Text>
          </>
        );
      case "generazione_fallita":
        return (
          <>
            <Alert color="orange" variant="light" mb="md">
              <b>Non siamo riusciti a preparare i post.</b> Il problema è
              nostro, non della tua campagna: il consorzio la fa ripartire. Dati
              e foto sono al sicuro, non devi reinviarli.
            </Alert>
            <Passi
              voci={[
                {
                  testo: `Inviata il ${dataOraIT(campagna.inviata_il)}`,
                  segno: "done",
                },
                {
                  testo: "Preparazione dei post · in attesa del consorzio",
                  segno: "warn",
                },
                { testo: "Revisione del consorzio", segno: "todo" },
                { testo: pubblicazione, segno: "todo" },
              ]}
            />
          </>
        );
      case "piano_da_rivedere":
      case "in_revisione":
        return (
          <>
            <Alert color="verde" variant="light" mb="md">
              I post sono pronti e li sta controllando un operatore. Ti
              scriviamo per email appena c'è una decisione. La campagna parte il{" "}
              <b>
                {new Date(campagna.inizio + "T00:00:00").toLocaleDateString(
                  "it-IT",
                )}
              </b>
              .
            </Alert>
            <Passi
              voci={[
                {
                  testo: `Inviata il ${dataOraIT(campagna.inviata_il)}`,
                  segno: "done",
                },
                { testo: "Post preparati", segno: "done" },
                { testo: "Revisione del consorzio", segno: "now" },
                { testo: pubblicazione, segno: "todo" },
              ]}
            />
          </>
        );
      case "respinta": {
        const esito = campagna.esito_respinta;
        const segnate = new Set(esito?.foto_segnate ?? []);
        return (
          <>
            {esito && (
              <Alert color="red" variant="light" mb="md">
                <b>Motivo: {esito.motivo}.</b>
                {esito.nota && <> Richiesta del consorzio: "{esito.nota}"</>}
              </Alert>
            )}
            {segnate.size > 0 && (
              <>
                <Text size="sm" fw={500} mb={6}>
                  Foto da rifare ({segnate.size} su{" "}
                  {campagna.gruppi.reduce((n, g) => n + g.foto.length, 0)})
                </Text>
                <Group gap="xs" mb="md">
                  {campagna.gruppi.flatMap((g) =>
                    g.foto.map((f) => (
                      <Paper
                        key={f.id}
                        withBorder
                        radius="sm"
                        w={84}
                        h={84}
                        p={4}
                        style={
                          segnate.has(f.id)
                            ? {
                                borderColor: "var(--mantine-color-red-6)",
                                borderWidth: 2,
                              }
                            : undefined
                        }
                      >
                        <Text
                          ff="monospace"
                          size="10px"
                          ta="center"
                          style={{ wordBreak: "break-all" }}
                        >
                          {f.file}
                        </Text>
                      </Paper>
                    )),
                  )}
                </Group>
              </>
            )}
            <Riga
              nome="Campagna"
              valore={`${campagna.titolo} · ${new Date(
                campagna.inizio + "T00:00:00",
              ).toLocaleDateString("it-IT")} → ${new Date(
                campagna.fine + "T00:00:00",
              ).toLocaleDateString("it-IT")}`}
            />
            <Riga
              nome="Respinta il"
              valore={dataOraIT(campagna.chiusa_il).split(" alle")[0]}
            />
            <Group mt="lg">
              <Button color="verde" onClick={onNuovaCampagna}>
                Crea una nuova campagna →
              </Button>
            </Group>
          </>
        );
      }
      case "scaduta":
        return (
          <>
            <Alert color="orange" variant="light" mb="md">
              <b>La campagna non è stata approvata in tempo.</b> "
              {campagna.titolo}" doveva partire il{" "}
              {new Date(campagna.inizio + "T00:00:00").toLocaleDateString(
                "it-IT",
              )}{" "}
              e il consorzio non è riuscito ad approvarla prima. Nessun post è
              stato pubblicato. Le foto restano nel tuo archivio: le usiamo
              nella prossima campagna.
            </Alert>
            <Button color="verde" onClick={onNuovaCampagna}>
              Crea una nuova campagna →
            </Button>
          </>
        );
      case "attiva":
        return (
          <>
            <Alert color="verde" variant="light" mb="md">
              <b>Il piano di questa campagna.</b> La strategia e il calendario
              dei post approvati, pubblicati o non pubblicati arrivano con lo
              sprint 3; le metriche con lo sprint 4.
            </Alert>
            <RiepilogoLettura campagna={campagna} />
          </>
        );
      case "sospesa":
        return (
          <Alert color="orange" variant="light">
            <b>Pubblicazioni ferme.</b> Il consorzio ha sospeso la campagna:
            contatta il consorzio per ripartire. I post in programma ripartono
            dopo.
          </Alert>
        );
      case "annullata":
        return (
          <Alert color="orange" variant="light">
            <b>Annullata.</b> Il consorzio ha fermato la campagna il{" "}
            {dataOraIT(campagna.chiusa_il).split(" alle")[0]}: i post in
            programma non usciranno. Quelli già pubblicati restano nel
            calendario.
          </Alert>
        );
      case "conclusa":
        return (
          <>
            <Alert color="verde" variant="light" mb="md">
              La campagna è conclusa. L'elenco dei post pubblicati e le metriche
              finali arrivano con gli sprint 3 e 4. Da qui si riparte.
            </Alert>
            <Button color="verde" onClick={onNuovaCampagna}>
              Crea una nuova campagna →
            </Button>
          </>
        );
      default:
        return <Text c="dimmed">Stato non previsto: {campagna.stato}</Text>;
    }
  };

  const badge =
    campagna.stato === "attiva" ? (
      <Badge color="verde" variant="light">
        in corso
      </Badge>
    ) : campagna.stato === "conclusa" ? (
      <Badge variant="light">conclusa</Badge>
    ) : null;

  return (
    <Paper withBorder radius="md" p="xl">
      <Title order={2} mb="md">
        {campagna.titolo} {badge}
      </Title>
      {corpo()}
    </Paper>
  );
}
