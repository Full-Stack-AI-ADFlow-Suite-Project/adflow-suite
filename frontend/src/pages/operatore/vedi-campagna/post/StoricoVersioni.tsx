/** Lo storico delle versioni di un post, con l'autore di ognuna (spec §3, R-02). */
import {
  Badge,
  Group,
  Paper,
  Stack,
  Text,
  UnstyledButton,
} from "@mantine/core";
import { useState } from "react";

import type { PostVista } from "../../../../api/revisione";
import { useAuth } from "../../../../contesto-auth";
import { dataOra } from "../../campagna/util";
import { conCancelletto, nomeAutore, nomeTipo } from "./regole";

export function StoricoVersioni({ post }: { post: PostVista }) {
  const { utente } = useAuth();
  const [aperto, setAperto] = useState(false);
  const corrente = post.versione_corrente;
  if (post.versioni.length === 0) return null;

  // Dalla più recente: è quella che si cerca più spesso.
  const versioni = [...post.versioni].sort((a, b) => b.numero - a.numero);

  return (
    <Stack gap="sm">
      <UnstyledButton onClick={() => setAperto((a) => !a)}>
        <Text size="sm" c="verde">
          {aperto ? "− Chiudi lo storico" : `Storico (${post.versioni.length})`}
        </Text>
      </UnstyledButton>
      {aperto &&
        versioni.map((ver) => {
          const attuale = ver.numero === corrente?.numero;
          const errori = Array.isArray(ver.errori_validazione)
            ? ver.errori_validazione
            : [];
          return (
            <Paper key={ver.id} withBorder radius="md" p="sm">
              <Group justify="space-between" wrap="wrap" gap="xs">
                <Group gap={6}>
                  <Text size="sm" fw={600}>
                    Versione {ver.numero}
                  </Text>
                  {attuale && (
                    <Badge size="xs" variant="light" color="verde">
                      corrente
                    </Badge>
                  )}
                </Group>
                <Text size="xs" c="dimmed">
                  {ver.creata_il ? dataOra(ver.creata_il) : ""}
                </Text>
              </Group>
              <Text size="xs" c="dimmed">
                {nomeTipo(ver.tipo_intervento)} · {nomeAutore(ver, utente)}
              </Text>
              {ver.testo && (
                <Text
                  size="sm"
                  mt={6}
                  c={attuale ? undefined : "dimmed"}
                  style={{ whiteSpace: "pre-line" }}
                >
                  {ver.testo}
                </Text>
              )}
              {!!ver.hashtag?.length && (
                <Text size="xs" c="verde" mt={4}>
                  {conCancelletto(ver.hashtag)}
                </Text>
              )}
              {ver.testo_proposto && (
                <Text size="xs" mt={4}>
                  Testo proposto: {ver.testo_proposto}
                </Text>
              )}
              {ver.nota && (
                <Text size="xs" mt={4}>
                  Nota: {ver.nota}
                </Text>
              )}
              {errori.map((e) => (
                <Text key={e.regola + e.messaggio} size="xs" mt={4}>
                  <Text span ff="monospace">
                    [{e.livello} · {e.regola}]
                  </Text>{" "}
                  {e.messaggio}
                </Text>
              ))}
            </Paper>
          );
        })}
    </Stack>
  );
}
