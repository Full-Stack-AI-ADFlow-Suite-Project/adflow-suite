/**
 * Cambia foto (R-36): la finestra mostra le foto con cui si può sostituire quella
 * del post, la migliore in cima. Nasce una nuova versione con lo stesso testo; dopo
 * l'approvazione la approva chi la scrive.
 */
import {
  Alert,
  Badge,
  Button,
  Center,
  Group,
  Loader,
  Modal,
  SimpleGrid,
  Stack,
  Text,
} from "@mantine/core";
import { useEffect, useState } from "react";

import { ApiErrore } from "../../../../api/http";
import { cambiaFoto, fotoPossibili } from "../../../../api/interventi";
import type { FotoPossibile, PostVista } from "../../../../api/revisione";
import { NOME_CANALE } from "../../campagna/util";
import { AVVISO_CAMPAGNA_APPROVATA } from "./regole";

export function CambiaFoto({
  post,
  approvata,
  chiudi,
  fatto,
}: {
  post: PostVista;
  /** Campagna attiva o sospesa: la versione nuova la approva l'operatore. */
  approvata: boolean;
  chiudi: () => void;
  fatto: () => void;
}) {
  const [foto, setFoto] = useState<FotoPossibile[] | null>(null);
  const [occupata, setOccupata] = useState<number | null>(null);
  const [errore, setErrore] = useState<string | null>(null);

  useEffect(() => {
    let attivo = true;
    fotoPossibili(post.post_id)
      .then((elenco) => {
        if (attivo) setFoto(elenco);
      })
      .catch((e) => {
        if (attivo)
          setErrore(
            e instanceof ApiErrore
              ? e.message
              : "Non sono riuscita a leggere le foto.",
          );
      });
    return () => {
      attivo = false;
    };
  }, [post.post_id]);

  const usa = async (fotoId: number) => {
    setOccupata(fotoId);
    setErrore(null);
    try {
      await cambiaFoto(post.post_id, fotoId);
      fatto();
    } catch (e) {
      setErrore(
        e instanceof ApiErrore ? e.message : "Non sono riuscita a cambiare.",
      );
    } finally {
      setOccupata(null);
    }
  };

  return (
    <Modal
      opened
      onClose={chiudi}
      title={`Cambia foto · ${NOME_CANALE[post.canale] ?? post.canale}`}
      size="lg"
    >
      <Stack gap="sm">
        {approvata && (
          <Alert color="yellow" variant="light" py="xs">
            {AVVISO_CAMPAGNA_APPROVATA}
          </Alert>
        )}
        <Text size="sm" c="dimmed">
          Il testo resta quello di adesso: dopo il cambio rileggilo. Le foto già
          usate da un altro post dello stesso canale non compaiono.
        </Text>
        {!foto && !errore && (
          <Center py="md">
            <Loader color="verde" size="sm" />
          </Center>
        )}
        {foto && foto.length === 0 && (
          <Text size="sm">
            {approvata
              ? "Nel gruppo non ci sono altre foto adatte."
              : "Nel gruppo non ci sono altre foto adatte: chiedile all'artigiano, oppure respingi."}
          </Text>
        )}
        {foto && foto.length > 0 && (
          <SimpleGrid cols={{ base: 1, sm: 2 }} spacing="sm">
            {foto.map((f) => (
              <Stack
                key={f.foto_id}
                gap={6}
                p="xs"
                style={{
                  border: "1px solid var(--mantine-color-default-border)",
                  borderRadius: 8,
                }}
              >
                <img
                  src={`/api/foto/${f.foto_id}/file`}
                  alt={`Foto ${f.foto_id}`}
                  style={{
                    width: "100%",
                    height: 160,
                    objectFit: "cover",
                    borderRadius: 6,
                    display: "block",
                  }}
                />
                <Group justify="space-between" wrap="nowrap" gap="xs">
                  {f.analizzata ? (
                    <Badge variant="light" size="sm">
                      Punteggio{" "}
                      {f.punteggio != null
                        ? String(f.punteggio).replace(".", ",")
                        : "—"}
                    </Badge>
                  ) : (
                    <Badge variant="light" color="yellow" size="sm">
                      Nuova, dall'artigiano: guardala tu
                    </Badge>
                  )}
                  <Button
                    size="xs"
                    color="verde"
                    loading={occupata === f.foto_id}
                    disabled={occupata !== null}
                    onClick={() => void usa(f.foto_id)}
                  >
                    Usa questa foto
                  </Button>
                </Group>
              </Stack>
            ))}
          </SimpleGrid>
        )}
        {errore && (
          <Alert color="red" variant="light" py="xs">
            {errore}
          </Alert>
        )}
        <Group justify="flex-end">
          <Button variant="default" onClick={chiudi}>
            Chiudi
          </Button>
        </Group>
      </Stack>
    </Modal>
  );
}
