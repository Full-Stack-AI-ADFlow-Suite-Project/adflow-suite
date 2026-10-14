/**
 * CalendarioCampagnaView (R-45, CA-56, ADR-114 E1):
 * Elenco per giorno dei post approvati, pubblicati, falliti o annullati.
 * Usato nella scheda Calendario di VediCampagna (operatore) e
 * nella pagina Campagna in stati attiva, conclusa, sospesa, annullata (artigiano).
 */
import { useEffect, useState } from "react";
import {
  Alert,
  Badge,
  Box,
  Card,
  Center,
  Group,
  Image,
  Loader,
  Paper,
  Stack,
  Text,
  Title,
} from "@mantine/core";

import { ApiErrore } from "../api/http";
import { calendario, type CalendarioCampagna } from "../api/campagne";

export interface CalendarioCampagnaViewProps {
  campagnaId: number;
  stato: string;
  ruolo?: "artigiano" | "operatore";
}

const GIORNI_SETT = [
  "Domenica",
  "Lunedì",
  "Martedì",
  "Mercoledì",
  "Giovedì",
  "Venerdì",
  "Sabato",
];

const MESI = [
  "gennaio",
  "febbraio",
  "marzo",
  "aprile",
  "maggio",
  "giugno",
  "luglio",
  "agosto",
  "settembre",
  "ottobre",
  "novembre",
  "dicembre",
];

function formattaGiorno(dataIso: string): string {
  const parti = dataIso.split("-").map(Number);
  if (parti.length !== 3) return dataIso;
  const data = new Date(parti[0], parti[1] - 1, parti[2]);
  const nomeGiorno = GIORNI_SETT[data.getDay()];
  const mese = MESI[data.getMonth()];
  return `${nomeGiorno} ${parti[2]} ${mese}`;
}

function isOggi(dataIso: string): boolean {
  const oggi = new Date();
  const y = oggi.getFullYear();
  const m = String(oggi.getMonth() + 1).padStart(2, "0");
  const d = String(oggi.getDate()).padStart(2, "0");
  return dataIso === `${y}-${m}-${d}`;
}

function oggiFormattato(): string {
  const oggi = new Date();
  const nomeGiorno = GIORNI_SETT[oggi.getDay()].toLowerCase();
  const d = oggi.getDate();
  const mese = MESI[oggi.getMonth()];
  return `${nomeGiorno} ${d} ${mese}`;
}

export function CalendarioCampagnaView({
  campagnaId,
  stato,
  ruolo = "artigiano",
}: CalendarioCampagnaViewProps) {
  const eApprovata = ["attiva", "sospesa", "conclusa", "annullata"].includes(
    stato,
  );
  const [dati, setDati] = useState<CalendarioCampagna | null>(null);
  const [caricamento, setCaricamento] = useState(eApprovata);
  const [errore, setErrore] = useState<string | null>(null);
  const [nonDisponibile, setNonDisponibile] = useState(false);

  useEffect(() => {
    if (!eApprovata) return;

    let attivo = true;

    calendario(campagnaId)
      .then((risp) => {
        if (attivo) {
          setDati(risp);
          setCaricamento(false);
        }
      })
      .catch((err) => {
        if (!attivo) return;
        setCaricamento(false);
        if (err instanceof ApiErrore && err.stato === 409) {
          setNonDisponibile(true);
        } else if (err instanceof ApiErrore && err.stato === 404) {
          setErrore("Campagna non trovata.");
        } else {
          setErrore(
            err instanceof Error
              ? err.message
              : "Errore caricamento calendario",
          );
        }
      });

    return () => {
      attivo = false;
    };
  }, [campagnaId, eApprovata]);

  if (!eApprovata || nonDisponibile) {
    return (
      <Paper withBorder radius="md" p="lg" style={{ borderStyle: "dashed" }}>
        <Text c="dimmed" size="sm">
          {ruolo === "operatore"
            ? "Il calendario si legge dopo l'approvazione: giorno per giorno i post approvati, pubblicati o falliti, con ora, canale e stato (R-45). Prima dell'approvazione le date dei post sono nelle uscite."
            : "Il calendario è disponibile dopo l'approvazione della campagna."}
        </Text>
      </Paper>
    );
  }

  if (caricamento) {
    return (
      <Center py="xl">
        <Loader color="verde" />
      </Center>
    );
  }

  if (errore) {
    return (
      <Alert color="red" variant="light">
        {errore}
      </Alert>
    );
  }

  if (!dati) return null;

  const tuttiPost = dati.giorni.flatMap((g) => g.post);
  const nTotali = tuttiPost.length;
  const nPubblicati = tuttiPost.filter((p) => p.stato === "pubblicato").length;
  const nInProgramma = tuttiPost.filter((p) => p.stato === "approvato").length;
  const nNonPubblicati = tuttiPost.filter(
    (p) => p.stato === "fallito" || p.stato === "annullato",
  ).length;
  const nScaduti = dati.n_post_scaduti;
  const nFacebook = tuttiPost.filter((p) => p.canale === "facebook").length;
  const nInstagram = tuttiPost.filter((p) => p.canale === "instagram").length;
  const nAI = tuttiPost.filter((p) =>
    p.foto.some((f) => f.origine === "ai"),
  ).length;
  const nFoto = nTotali - nAI;

  return (
    <Stack gap="md">
      {/* Strategia del piano approvato (CA-56) */}
      {dati.strategia && (
        <Alert color="verde" variant="light">
          <Text fw={600} size="sm" mb={4}>
            Il piano di questa campagna.
          </Text>
          <Text size="sm">{dati.strategia}</Text>
        </Alert>
      )}

      {/* Avvisi canali tolti (per operatore; per artigiano è già in cima a VistaStato) */}
      {ruolo === "operatore" &&
        dati.canali_tolti.map((ct) => (
          <Alert key={ct.canale} color="orange" variant="light">
            <Text size="sm">
              <b>
                Canale{" "}
                {ct.canale === "facebook"
                  ? "Facebook"
                  : ct.canale === "instagram"
                  ? "Instagram"
                  : ct.canale}{" "}
                escluso:
              </b>{" "}
              {ct.nota || "Il canale è stato tolto dall'operatore."}
            </Text>
          </Alert>
        ))}

      {/* Conteggi e riepilogo post */}
      <Paper withBorder radius="md" p="md">
        <Stack gap="xs">
          <Group gap="xs" wrap="wrap">
            <Text size="sm" fw={600}>
              Post:
            </Text>
            <Text size="sm">
              <b>{nTotali}</b> post · <b>{nPubblicati}</b> pubblicati ·{" "}
              <b>{nInProgramma}</b> in programma · <b>{nNonPubblicati}</b> non
              pubblicati · <b>{nScaduti}</b> scaduti prima dell'approvazione
            </Text>
          </Group>
          <Group gap="xs" wrap="wrap">
            <Text size="sm" fw={600}>
              Canali e foto:
            </Text>
            <Text size="sm">
              Facebook <b>{nFacebook}</b> · Instagram <b>{nInstagram}</b> · Con
              le tue foto <b>{nFoto}</b> · Con immagine AI <b>{nAI}</b>
            </Text>
          </Group>
        </Stack>
      </Paper>

      {/* Intestazione sezione e legenda */}
      <div>
        <Title order={4} size="h5" mb={6}>
          Calendario · per giorno
        </Title>
        <Group gap="xs" wrap="wrap">
          <Badge color="verde" size="sm" variant="light">
            pubblicato
          </Badge>
          <Badge color="gray" size="sm" variant="light">
            in programma
          </Badge>
          <Badge color="red" size="sm" variant="light">
            non pubblicato
          </Badge>
          <Badge
            color="orange"
            size="sm"
            variant="outline"
            style={{ borderStyle: "dashed" }}
          >
            immagine AI
          </Badge>
          <Text size="xs" c="dimmed">
            Oggi è {oggiFormattato()}.
          </Text>
        </Group>
      </div>

      {/* Elenco per giorno */}
      {dati.giorni.length === 0 ? (
        <Card withBorder radius="md" p="md" style={{ borderStyle: "dashed" }}>
          <Text c="dimmed" size="sm">
            Nessun post presente nel calendario.
          </Text>
        </Card>
      ) : (
        dati.giorni.map((g) => (
          <Stack key={g.data} gap="xs">
            <Text fw={700} size="sm" mt="xs">
              {formattaGiorno(g.data)}
              {isOggi(g.data) ? " · oggi" : ""}
            </Text>
            {g.post.map((p) => {
              const isAi = p.foto.some((f) => f.origine === "ai");
              const isFallitoOAnnullato =
                p.stato === "fallito" || p.stato === "annullato";
              return (
                <Card key={p.id} withBorder radius="md" p="sm">
                  <Group align="flex-start" wrap="nowrap" gap="md">
                    {/* Anteprima foto / Badge AI */}
                    {isAi ? (
                      <Box
                        w={64}
                        h={64}
                        style={{
                          display: "flex",
                          flexDirection: "column",
                          alignItems: "center",
                          justifyContent: "center",
                          background: "var(--mantine-color-orange-light)",
                          border: "1px dashed var(--mantine-color-orange-4)",
                          borderRadius: 6,
                          flexShrink: 0,
                        }}
                      >
                        <Text size="xs" fw={700} c="orange.8">
                          AI
                        </Text>
                        <Text size="10px" c="dimmed">
                          1:1
                        </Text>
                      </Box>
                    ) : p.foto.length > 0 ? (
                      <Box
                        w={64}
                        h={64}
                        style={{
                          borderRadius: 6,
                          overflow: "hidden",
                          flexShrink: 0,
                          border: "1px solid var(--mantine-color-gray-3)",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          background: "var(--mantine-color-gray-1)",
                        }}
                      >
                        <Image
                          src={p.foto[0].url}
                          w={64}
                          h={64}
                          fit="cover"
                          alt=""
                          fallbackSrc=""
                        />
                      </Box>
                    ) : null}

                    {/* Dettagli post */}
                    <Stack gap={4} style={{ flex: 1, minWidth: 0 }}>
                      <Group gap="xs" wrap="wrap">
                        <Text size="xs" fw={700} ff="monospace">
                          ore {p.ora} ·{" "}
                          {p.canale === "facebook" ? "Facebook" : "Instagram"}
                        </Text>
                        {p.canale === "facebook" ? (
                          <Badge size="xs" color="blue">
                            Facebook
                          </Badge>
                        ) : (
                          <Badge size="xs" color="grape">
                            Instagram
                          </Badge>
                        )}
                        {ruolo === "operatore" ? (
                          p.stato === "pubblicato" ? (
                            <Badge size="xs" color="verde">
                              pubblicato
                            </Badge>
                          ) : p.stato === "approvato" ? (
                            <Badge size="xs" color="gray" variant="light">
                              approvato
                            </Badge>
                          ) : (
                            <Badge size="xs" color="red">
                              {p.stato}
                            </Badge>
                          )
                        ) : p.stato === "pubblicato" ? (
                          <Badge size="xs" color="verde">
                            pubblicato
                          </Badge>
                        ) : p.stato === "approvato" ? (
                          <Badge size="xs" color="gray" variant="light">
                            in programma
                          </Badge>
                        ) : (
                          <Badge size="xs" color="red">
                            non pubblicato
                          </Badge>
                        )}
                        {isAi && (
                          <Badge
                            size="xs"
                            color="orange"
                            variant="outline"
                            style={{ borderStyle: "dashed" }}
                          >
                            immagine AI
                          </Badge>
                        )}
                      </Group>

                      {p.testo && (
                        <Text size="xs" style={{ whiteSpace: "pre-line" }}>
                          "{p.testo}"
                        </Text>
                      )}

                      {p.hashtag.length > 0 && (
                        <Text size="xs" c="verde">
                          {p.hashtag
                            .map((h) => (h.startsWith("#") ? h : `#${h}`))
                            .join(" ")}
                        </Text>
                      )}

                      {isFallitoOAnnullato && (
                        <Text size="xs" c="dimmed">
                          Non è stato possibile pubblicarlo. Il consorzio è già
                          stato avvisato.
                        </Text>
                      )}
                      {isAi && (
                        <Text size="xs" c="dimmed">
                          Immagine creata con AI · 1:1
                        </Text>
                      )}
                    </Stack>
                  </Group>
                </Card>
              );
            })}
          </Stack>
        ))
      )}
    </Stack>
  );
}
