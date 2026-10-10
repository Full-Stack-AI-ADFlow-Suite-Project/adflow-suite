import { useRef, useState } from "react";
import {
  Alert,
  Button,
  FileButton,
  Group,
  Image,
  Paper,
  Stack,
  Text,
  Title,
} from "@mantine/core";

import { caricaLogo, eliminaLogo, urlLogo } from "../../../../api/archivio";
import { ApiErrore } from "../../../../api/http";

export function SezioneLogo({
  logo,
  onLogoCambiato,
}: {
  logo: string | null;
  onLogoCambiato: (nuovoLogo: string | null) => void;
}) {
  const [caricando, setCaricando] = useState(false);
  const [errore, setErrore] = useState("");
  const resetRef = useRef<() => void>(null);

  const gestisciUpload = async (file: File | null) => {
    if (!file) return;
    setErrore("");
    setCaricando(true);
    try {
      const profilo = await caricaLogo(file);
      onLogoCambiato(profilo.logo);
      resetRef.current?.();
    } catch (e) {
      setErrore(
        e instanceof ApiErrore
          ? e.dettaglio
          : "Errore nel caricamento del logo.",
      );
    } finally {
      setCaricando(false);
    }
  };

  const gestisciElimina = async () => {
    setErrore("");
    setCaricando(true);
    try {
      await eliminaLogo();
      onLogoCambiato(null);
    } catch (e) {
      setErrore(
        e instanceof ApiErrore
          ? e.dettaglio
          : "Errore nell'eliminazione del logo.",
      );
    } finally {
      setCaricando(false);
    }
  };

  const sorgente = urlLogo(logo);

  return (
    <Paper withBorder p="md" radius="sm">
      <Stack gap="xs">
        <div>
          <Title order={3}>Logo della bottega</Title>
          <Text size="sm" c="dimmed" mt={2}>
            Serve per le cartoline: un'immagine con il logo e una frase, per un
            evento, gli orari o un augurio. Senza logo usiamo il nome della
            bottega.
          </Text>
        </div>

        {errore && (
          <Alert color="red" title="Attenzione">
            {errore}
          </Alert>
        )}

        {sorgente ? (
          <Group align="center" gap="lg" mt="xs">
            <Paper
              withBorder
              p={4}
              radius="sm"
              style={{
                width: 96,
                height: 96,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                overflow: "hidden",
                backgroundColor: "var(--mantine-color-gray-0)",
              }}
            >
              <Image
                src={sorgente}
                alt="Logo bottega"
                fit="contain"
                w={88}
                h={88}
                fallbackSrc="https://placehold.co/96x96?text=Logo"
              />
            </Paper>
            <Stack gap="xs">
              <Text size="sm" fw={500}>
                Logo impostato
              </Text>
              <Group gap="xs">
                <FileButton
                  resetRef={resetRef}
                  onChange={gestisciUpload}
                  accept="image/png,image/jpeg,image/webp"
                >
                  {(props) => (
                    <Button
                      {...props}
                      variant="default"
                      size="xs"
                      loading={caricando}
                    >
                      Sostituisci logo
                    </Button>
                  )}
                </FileButton>
                <Button
                  variant="subtle"
                  color="red"
                  size="xs"
                  onClick={gestisciElimina}
                  loading={caricando}
                >
                  Rimuovi logo
                </Button>
              </Group>
              <Text size="xs" c="dimmed">
                JPG, PNG o WEBP, fino a 2 MB, lato corto ≥ 300 px (spec R-40).
              </Text>
            </Stack>
          </Group>
        ) : (
          <Stack gap="xs" mt="xs">
            <Group align="center">
              <FileButton
                resetRef={resetRef}
                onChange={gestisciUpload}
                accept="image/png,image/jpeg,image/webp"
              >
                {(props) => (
                  <Button
                    {...props}
                    variant="default"
                    size="sm"
                    loading={caricando}
                  >
                    Carica logo
                  </Button>
                )}
              </FileButton>
              <Text size="xs" c="dimmed">
                JPG, PNG o WEBP, fino a 2 MB, lato corto ≥ 300 px (spec R-40).
              </Text>
            </Group>
          </Stack>
        )}
      </Stack>
    </Paper>
  );
}
