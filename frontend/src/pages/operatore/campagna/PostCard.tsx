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
  UnstyledButton,
} from "@mantine/core";
import { useState } from "react";
import { Link } from "react-router-dom";

import type { PostVista } from "../../../api/revisione";
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
  return (
    <Paper withBorder radius="md" p="sm" w={300} miw={280}>
      <Group gap="xs" wrap="nowrap">
        <Avatar color="verde" radius="xl" size={30}>
          {bottega.slice(0, 1).toUpperCase()}
        </Avatar>
        <Stack gap={0}>
          <Text size="xs" fw={600}>
            {bottega}
          </Text>
          <Text size="xs" c="dimmed">
            {post.canale === "facebook" ? "Pubblico" : citta}
          </Text>
        </Stack>
      </Group>
      <Text size="xs" mt="xs" style={{ whiteSpace: "pre-line" }}>
        {v?.testo
          ? v.testo.length > 300
            ? v.testo.slice(0, 300) + "…"
            : v.testo
          : null}
      </Text>
      {!!v?.hashtag?.length && (
        <Text size="xs" c="verde" mt={4}>
          {v.hashtag.join(" ")}
        </Text>
      )}
      {post.riempitivo === "cartolina" ? (
        <Box
          mt="xs"
          p="md"
          style={{
            background:
              "linear-gradient(135deg, var(--mantine-color-verde-6), var(--mantine-color-verde-8))",
            borderRadius: 8,
          }}
        >
          <Text size="xs" c="white" fw={600}>
            {bottega}
          </Text>
          <Text size="xs" c="white" mt={4}>
            {tema}
          </Text>
          <Text size="xs" c="white" mt={6} ff="monospace" opacity={0.7}>
            cartolina
          </Text>
        </Box>
      ) : foto ? (
        <Box
          mt="xs"
          p="md"
          style={{
            border: "1px dashed var(--mantine-color-gray-5)",
            borderRadius: 8,
          }}
        >
          <Text size="xs" c="dimmed" ff="monospace">
            {foto.foto_id >= 900
              ? `cartolina-${foto.foto_id}.png`
              : `foto-${foto.foto_id}.jpg`}
          </Text>
          <Badge size="xs" variant="light" mt={4}>
            originale
          </Badge>
        </Box>
      ) : null}
      {post.canale === "facebook" && (
        <Text size="xs" c="dimmed" mt="xs" ta="center" fs="italic">
          In anteprima non si vedono Mi piace e commenti.
        </Text>
      )}
    </Paper>
  );
}

export function PostCard({
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
  const [storico, setStorico] = useState(false);
  const v = post.versione_corrente;
  const errori = erroriDi(post);
  const blocchi = errori.filter((e) => e.livello === "blocco");
  const avvisi = errori.filter((e) => e.livello === "avviso");
  const inCorso = !!post.intervento_in_corso;

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
            <Badge
              color={post.canale === "facebook" ? "indigo" : "pink"}
              variant="light"
            >
              {NOME_CANALE[post.canale] ?? post.canale}
            </Badge>
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
            {post.riempitivo === "cartolina" && (
              <Badge variant="light">Riempitivo · cartolina</Badge>
            )}
            {inCorso && (
              <Badge color="yellow" variant="light">
                intervento in corso
              </Badge>
            )}
          </Group>
        </Group>

        {inCorso && (
          <Alert color="yellow" variant="light" py="xs">
            <b>{post.intervento_in_corso}</b> sta intervenendo su questo post
            {post.intervento_dal ? ` dal ${dataOra(post.intervento_dal)}` : ""}.
            Finché lavora lei, nessun altro lo tocca.
          </Alert>
        )}

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

        {post.versioni.length > 0 && (
          <UnstyledButton onClick={() => setStorico((s) => !s)}>
            <Text size="sm" c="verde">
              {storico
                ? "− Chiudi lo storico"
                : `Storico (${post.versioni.length})`}
            </Text>
          </UnstyledButton>
        )}
        {storico && (
          <Stack gap="sm">
            {post.versioni.map((ver) => (
              <Paper key={ver.id} withBorder radius="md" p="sm">
                <Group justify="space-between">
                  <Text size="sm" fw={600}>
                    Versione {ver.numero}
                  </Text>
                  <Text size="xs" c="dimmed">
                    {ver.creata_il ? dataOra(ver.creata_il) : ""}
                  </Text>
                </Group>
                <Text size="xs" c="dimmed">
                  {ver.tipo_intervento} ·{" "}
                  {ver.autore_id == null ? "AI" : "operatore"}
                </Text>
                {ver.testo && (
                  <Text
                    size="sm"
                    mt={6}
                    c={ver.numero === v?.numero ? undefined : "dimmed"}
                    style={{ whiteSpace: "pre-line" }}
                  >
                    {ver.testo}
                  </Text>
                )}
                {!!ver.hashtag?.length && (
                  <Text size="xs" c="verde" mt={4}>
                    {ver.hashtag.join(" ")}
                  </Text>
                )}
                {ver.nota && (
                  <Text size="xs" mt={4}>
                    Nota: {ver.nota}
                  </Text>
                )}
                {(Array.isArray(ver.errori_validazione)
                  ? ver.errori_validazione
                  : []
                ).map((e) => (
                  <Text key={e.regola} size="xs" mt={4}>
                    <Text span ff="monospace">
                      [{e.livello} · {e.regola}]
                    </Text>{" "}
                    {e.messaggio}
                  </Text>
                ))}
              </Paper>
            ))}
          </Stack>
        )}

        {post.riempitivo === "cartolina" && (
          <Text size="xs" c="dimmed">
            Riempitivo: non usa foto nuove.
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
