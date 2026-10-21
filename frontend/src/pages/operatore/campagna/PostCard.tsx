/**
 * Un post del canale dentro l'uscita: anteprima come esce sul social,
 * blocchi e avvisi del validatore, metadati della versione e storico.
 */
import {
  Alert,
  Avatar,
  Badge,
  Box,
  Card,
  Group,
  Paper,
  Stack,
  Text,
} from "@mantine/core";
import { Link } from "react-router-dom";

import type { PostVista } from "../../../api/revisione";
import { BadgeCanale, IconaCanale } from "../../../components/IconaCanale";
import { AzioniPost } from "../vedi-campagna/post/AzioniPost";
import { conCancelletto, interventoAttivo } from "../vedi-campagna/post/regole";
import { StoricoVersioni } from "../vedi-campagna/post/StoricoVersioni";
import { colorePost, dataOra, erroriDi, NOME_CANALE } from "./util";

function AnteprimaPost({
  post,
  bottega,
  citta,
  tema,
}: {
  post: PostVista;
  bottega: string;
  citta: string | null;
  tema: string;
}) {
  const v = post.versione_corrente;
  const foto = v?.foto?.[0];
  const isAi =
    post.riempitivo === "immagine_ai" || post.riempitivo === "cartolina";
  return (
    <Paper
      withBorder
      radius="md"
      p={0}
      w="100%"
      style={{
        overflow: "hidden",
        background: "#ffffff",
        borderColor: "rgba(15, 23, 42, 0.11)",
      }}
    >
      <Group
        justify="space-between"
        px="sm"
        py={10}
        wrap="nowrap"
        style={{ borderBottom: "1px solid rgba(15, 23, 42, 0.07)" }}
      >
        <Group gap="xs" wrap="nowrap">
          <Avatar color="verde" radius="xl" size={32}>
            {bottega.slice(0, 1).toUpperCase()}
          </Avatar>
          <Stack gap={0}>
            <Text size="xs" fw={700} c="#0f172a">
              {bottega}
            </Text>
            <Text size="11px" c="dimmed">
              {post.canale === "facebook"
                ? "Pagina · Pubblico"
                : citta || "Profilo Instagram"}
            </Text>
          </Stack>
        </Group>
        <IconaCanale canale={post.canale} size={18} />
      </Group>

      {isAi ? (
        <Box
          p="md"
          style={{
            background: "linear-gradient(145deg, #f3eefc 0%, #eae3f8 100%)",
            borderBottom: "1px dashed var(--mantine-color-grape-4)",
            minHeight: 190,
            display: "flex",
            flexDirection: "column",
            justifyContent: "center",
          }}
        >
          <Badge color="grape" variant="light" w="fit-content" mb={6}>
            Immagine creata con AI · 1:1
          </Badge>
          <Text size="sm" fw={600} c="grape.9">
            {tema}
          </Text>
          <Text size="xs" c="grape.7" mt={6} ff="monospace">
            {bottega}
          </Text>
        </Box>
      ) : foto ? (
        <Box style={{ background: "#f1f5f9" }}>
          <img
            src={`/api/foto/${foto.foto_id}/file`}
            alt={`Foto ${foto.foto_id}`}
            style={{
              width: "100%",
              aspectRatio: "1 / 1",
              maxHeight: 280,
              objectFit: "cover",
              display: "block",
            }}
          />
        </Box>
      ) : null}

      <Box p="sm">
        <Text size="xs" style={{ whiteSpace: "pre-line", lineHeight: 1.55 }}>
          {v?.testo
            ? v.testo.length > 340
              ? v.testo.slice(0, 340) + "…"
              : v.testo
            : null}
        </Text>
        {!!v?.hashtag?.length && (
          <Text size="xs" c="verde" fw={600} mt={6}>
            {conCancelletto(v.hashtag)}
          </Text>
        )}
        {post.canale === "facebook" && (
          <Text size="11px" c="dimmed" mt="xs" fs="italic">
            In anteprima non si vedono Mi piace e commenti.
          </Text>
        )}
      </Box>
    </Paper>
  );
}

export function PostCard({
  post,
  bottega,
  citta,
  tema,
  statoCampagna,
  ricarica,
}: {
  post: PostVista;
  bottega: string;
  citta: string | null;
  tema: string;
  statoCampagna: string;
  ricarica: () => void;
}) {
  const v = post.versione_corrente;
  const errori = erroriDi(post);
  const blocchi = errori.filter((e) => e.livello === "blocco");
  const avvisi = errori.filter((e) => e.livello === "avviso");
  const inCorso = interventoAttivo(post);
  const isAi =
    post.riempitivo === "immagine_ai" || post.riempitivo === "cartolina";

  return (
    <Card
      withBorder
      radius="md"
      p="md"
      id={`post-${post.post_id}`}
      style={
        post.da_rivedere
          ? { border: "1px solid var(--mantine-color-red-5)" }
          : inCorso
          ? { border: "1px solid var(--mantine-color-yellow-5)" }
          : undefined
      }
    >
      <Stack gap="sm">
        <Group justify="space-between" wrap="wrap">
          <Group gap={6} wrap="wrap">
            <BadgeCanale canale={post.canale} size="sm" />
            <Text size="sm" c="dimmed" ff="monospace">
              {dataOra(post.data_ora)}
            </Text>
            <Badge
              color={colorePost(post.stato)}
              variant="light"
              ff="monospace"
            >
              {post.stato}
            </Badge>
            {post.da_rivedere && (
              <Badge color="red" variant="light">
                da rivedere
              </Badge>
            )}
            {avvisi.length > 0 && (
              <Badge color="yellow" variant="light">
                {avvisi.length} avviso{avvisi.length > 1 ? "i" : ""}
              </Badge>
            )}
            {isAi && (
              <Badge color="grape" variant="light">
                Immagine AI
              </Badge>
            )}
            {inCorso && (
              <Badge color="yellow" variant="light">
                intervento in corso
              </Badge>
            )}
          </Group>
        </Group>

        {!v ? (
          <Alert color="gray" variant="light">
            Testo non ancora scritto:{" "}
            {post.riempitivo
              ? "il testo arriva con la generazione."
              : "manca l'ultima tappa della generazione."}
          </Alert>
        ) : (
          <AnteprimaPost
            post={post}
            bottega={bottega}
            citta={citta}
            tema={tema}
          />
        )}

        {blocchi.map((b) => (
          <Alert
            key={b.regola + b.messaggio}
            color="red"
            variant="light"
            py="xs"
          >
            <b>Blocco</b> ({b.regola}): {b.messaggio} Il post è da rivedere e
            non va online così.
          </Alert>
        ))}
        {avvisi.map((a) => (
          <Alert
            key={a.regola + a.messaggio}
            color="yellow"
            variant="light"
            py="xs"
          >
            <b>Avviso</b> ({a.regola}): {a.messaggio} Non blocca l'approvazione.
          </Alert>
        ))}

        {v && (
          <Text size="xs" c="dimmed">
            v{v.numero} · {v.tipo_intervento} ·{" "}
            {v.autore_id == null ? "AI" : "operatore"} · {v.testo?.length ?? 0}{" "}
            caratteri · {v.hashtag?.length ?? 0} hashtag
          </Text>
        )}

        {v?.tipo_intervento === "cambio_foto" && (
          <Alert color="yellow" variant="light" py="xs">
            Foto cambiata: rileggi il testo.
          </Alert>
        )}

        <AzioniPost
          post={post}
          statoCampagna={statoCampagna}
          ricarica={ricarica}
        />
        <StoricoVersioni post={post} />

        {isAi && (
          <Text size="xs" c="dimmed">
            Immagine creata con AI: 1:1, la stessa per l'uscita su entrambi i
            canali (R-28).
          </Text>
        )}
        {(post.stato === "scaduto" ||
          post.stato === "scartato" ||
          post.stato === "annullato") && (
          <Text size="xs" c="dimmed">
            Il post è chiuso: non torna indietro.
          </Text>
        )}
        {post.stato === "pubblicato" && (
          <Text size="xs">
            <Text span fw={500}>
              Controllato da:
            </Text>{" "}
            {post.controllato_da != null
              ? `operatore n. ${post.controllato_da}`
              : "—"}
            {post.controllato_il ? ` · ${dataOra(post.controllato_il)}` : ""} ·{" "}
            <Link to="#">Post su {NOME_CANALE[post.canale]}</Link>
          </Text>
        )}
      </Stack>
    </Card>
  );
}
