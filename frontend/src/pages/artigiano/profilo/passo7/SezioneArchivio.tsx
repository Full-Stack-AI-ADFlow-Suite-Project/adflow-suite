import { useEffect, useState } from "react";
import {
  ActionIcon,
  Alert,
  Button,
  FileButton,
  Group,
  Image,
  Loader,
  Paper,
  SimpleGrid,
  Stack,
  Text,
  TextInput,
  Title,
  Tooltip,
} from "@mantine/core";

import {
  caricaFotoArchivio,
  creaGruppoArchivio,
  elencoArchivio,
  eliminaFotoArchivio,
  eliminaGruppoArchivio,
  urlFotoFile,
  type GruppoSintetico,
} from "../../../../api/archivio";
import { ApiErrore } from "../../../../api/http";

export function SezioneArchivio() {
  const [gruppi, setGruppi] = useState<GruppoSintetico[]>([]);
  const [inCaricamento, setInCaricamento] = useState(true);
  const [errore, setErrore] = useState("");
  const [apertoCreaGruppo, setApertoCreaGruppo] = useState(false);
  const [nuovaDescrizione, setNuovaDescrizione] = useState("");
  const [creandoGruppo, setCreandoGruppo] = useState(false);
  const [gruppoInUpload, setGruppoInUpload] = useState<number | null>(null);

  useEffect(() => {
    let attivo = true;
    elencoArchivio()
      .then((g) => {
        if (attivo) {
          setGruppi(g);
          setErrore("");
        }
      })
      .catch((e) => {
        if (attivo) {
          setErrore(
            e instanceof ApiErrore
              ? e.dettaglio
              : "Impossibile caricare l'archivio.",
          );
        }
      })
      .finally(() => {
        if (attivo) setInCaricamento(false);
      });
    return () => {
      attivo = false;
    };
  }, []);

  const handleCreaGruppo = async () => {
    const desc = nuovaDescrizione.trim();
    if (!desc) {
      setErrore("Inserisci una descrizione per il gruppo.");
      return;
    }
    setErrore("");
    setCreandoGruppo(true);
    try {
      const nuovo = await creaGruppoArchivio({ descrizione: desc });
      setGruppi((prev) => [...prev, nuovo]);
      setNuovaDescrizione("");
      setApertoCreaGruppo(false);
    } catch (e) {
      setErrore(
        e instanceof ApiErrore
          ? e.dettaglio
          : "Errore durante la creazione del gruppo.",
      );
    } finally {
      setCreandoGruppo(false);
    }
  };

  const handleEliminaGruppo = async (gruppoId: number) => {
    setErrore("");
    try {
      await eliminaGruppoArchivio(gruppoId);
      setGruppi((prev) => prev.filter((g) => g.id !== gruppoId));
    } catch (e) {
      setErrore(
        e instanceof ApiErrore
          ? e.dettaglio
          : "Errore durante l'eliminazione del gruppo.",
      );
    }
  };

  const handleUploadFoto = async (gruppoId: number, file: File | null) => {
    if (!file) return;
    setErrore("");
    setGruppoInUpload(gruppoId);
    try {
      const fotoCaricata = await caricaFotoArchivio(gruppoId, file);
      setGruppi((prev) =>
        prev.map((g) =>
          g.id === gruppoId ? { ...g, foto: [...g.foto, fotoCaricata] } : g,
        ),
      );
    } catch (e) {
      setErrore(
        e instanceof ApiErrore
          ? e.dettaglio
          : "Errore durante il caricamento della foto.",
      );
    } finally {
      setGruppoInUpload(null);
    }
  };

  const handleEliminaFoto = async (gruppoId: number, fotoId: number) => {
    setErrore("");
    try {
      await eliminaFotoArchivio(fotoId);
      setGruppi((prev) =>
        prev.map((g) =>
          g.id === gruppoId
            ? { ...g, foto: g.foto.filter((f) => f.id !== fotoId) }
            : g,
        ),
      );
    } catch (e) {
      setErrore(
        e instanceof ApiErrore
          ? e.dettaglio
          : "Errore durante l'eliminazione della foto.",
      );
    }
  };

  return (
    <Paper withBorder p="md" radius="sm">
      <Stack gap="md">
        <div>
          <Title order={3}>Archivio della bottega (facoltativo)</Title>
          <Text size="sm" c="dimmed" mt={2}>
            Foto sempre valide: il laboratorio, tu al lavoro, la vetrina, i
            pezzi a cui tieni. Le usiamo quando in una campagna le foto nuove
            non bastano a tenere il ritmo che hai scelto. Si caricano a gruppi,
            con una descrizione, come nella pagina Campagna. Qui finiscono da
            sole anche le foto buone delle tue campagne.
          </Text>
        </div>

        {errore && (
          <Alert color="red" title="Attenzione">
            {errore}
          </Alert>
        )}

        {inCaricamento ? (
          <Group justify="center" py="md">
            <Loader size="sm" />
            <Text size="sm">Caricamento archivio...</Text>
          </Group>
        ) : (
          <Stack gap="md">
            {gruppi.length === 0 ? (
              <Text size="sm" c="dimmed">
                Nessun gruppo presente nell'archivio. Aggiungi un primo gruppo
                per iniziare a caricare foto storiche o ricorrenti della tua
                bottega.
              </Text>
            ) : (
              gruppi.map((g) => (
                <Paper
                  key={g.id}
                  withBorder
                  p="sm"
                  radius="sm"
                  style={{ backgroundColor: "var(--mantine-color-gray-0)" }}
                >
                  <Stack gap="xs">
                    <Group justify="space-between" align="flex-start">
                      <div>
                        <Text size="sm" fw={600}>
                          {g.descrizione || "Gruppo senza descrizione"}
                        </Text>
                        <Text size="xs" c="dimmed">
                          {g.foto.length} di 20 foto
                        </Text>
                      </div>
                      <Group gap="xs">
                        <FileButton
                          onChange={(file) => handleUploadFoto(g.id, file)}
                          accept="image/png,image/jpeg,image/webp"
                          disabled={
                            g.foto.length >= 20 || gruppoInUpload === g.id
                          }
                        >
                          {(props) => (
                            <Button
                              {...props}
                              variant="default"
                              size="xs"
                              loading={gruppoInUpload === g.id}
                              disabled={g.foto.length >= 20}
                            >
                              + Aggiungi foto
                            </Button>
                          )}
                        </FileButton>
                        <Button
                          variant="subtle"
                          color="red"
                          size="xs"
                          onClick={() => handleEliminaGruppo(g.id)}
                        >
                          Elimina gruppo
                        </Button>
                      </Group>
                    </Group>

                    {g.foto.length > 0 ? (
                      <SimpleGrid
                        cols={{ base: 3, xs: 4, sm: 6 }}
                        spacing="xs"
                        mt={4}
                      >
                        {g.foto.map((foto) => (
                          <Paper
                            key={foto.id}
                            withBorder
                            radius="sm"
                            style={{
                              position: "relative",
                              aspectRatio: "1",
                              overflow: "hidden",
                              backgroundColor: "var(--mantine-color-white)",
                            }}
                          >
                            <Image
                              src={urlFotoFile(foto.file, foto.id)}
                              alt="Foto archivio"
                              fit="cover"
                              w="100%"
                              h="100%"
                            />
                            <Tooltip label="Rimuovi foto dall'archivio">
                              <ActionIcon
                                variant="filled"
                                color="rgba(0, 0, 0, 0.6)"
                                size="sm"
                                radius="xl"
                                aria-label="Rimuovi foto"
                                style={{
                                  position: "absolute",
                                  top: 4,
                                  right: 4,
                                }}
                                onClick={() => handleEliminaFoto(g.id, foto.id)}
                              >
                                ×
                              </ActionIcon>
                            </Tooltip>
                          </Paper>
                        ))}
                      </SimpleGrid>
                    ) : (
                      <Text size="xs" c="dimmed" mt={2}>
                        Nessuna foto in questo gruppo. Carica JPG, PNG o WEBP
                        (fino a 10 MB, lato corto ≥ 1080 px).
                      </Text>
                    )}
                  </Stack>
                </Paper>
              ))
            )}

            {apertoCreaGruppo ? (
              <Paper withBorder p="sm" radius="sm">
                <Stack gap="xs">
                  <Text size="sm" fw={500}>
                    Nuovo gruppo dell'archivio
                  </Text>
                  <TextInput
                    label="Descrizione del gruppo *"
                    placeholder="Es. Il laboratorio, i dettagli in legno, la bottega..."
                    value={nuovaDescrizione}
                    onChange={(e) => setNuovaDescrizione(e.currentTarget.value)}
                  />
                  <Group justify="flex-end" gap="xs">
                    <Button
                      variant="default"
                      size="xs"
                      onClick={() => {
                        setApertoCreaGruppo(false);
                        setNuovaDescrizione("");
                      }}
                      disabled={creandoGruppo}
                    >
                      Annulla
                    </Button>
                    <Button
                      size="xs"
                      color="verde"
                      onClick={handleCreaGruppo}
                      loading={creandoGruppo}
                    >
                      Crea gruppo
                    </Button>
                  </Group>
                </Stack>
              </Paper>
            ) : (
              <Button
                variant="default"
                size="xs"
                onClick={() => setApertoCreaGruppo(true)}
              >
                + Aggiungi un gruppo di foto all'archivio
              </Button>
            )}

            <Text size="xs" c="dimmed">
              Requisiti foto: JPG, PNG o WEBP, fino a 10 MB, lato corto ≥ 1080
              px, massimo 20 foto per gruppo (spec R-13).
            </Text>
          </Stack>
        )}
      </Stack>
    </Paper>
  );
}
