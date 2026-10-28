/**
 * Cambia immagine (R-36, R-49, ADR-119): la finestra mostra le foto con cui si può sostituire quella
 * del post, divise in tre sezioni: «Dello stesso gruppo», «Della campagna», «Dall'archivio della bottega»,
 * con il soggetto sotto la miniatura.
 * In revisione offre una quarta scelta «Crea una nuova immagine AI» con «Indicazioni per l'immagine» e la spunta
 * «Riscrivi anche il testo per la nuova immagine» (accesa di base, con «Indicazioni per il testo»): è «Rifai il post».
 * Dopo l'approvazione né la quarta scelta né la spunta.
 */
import {
  Alert,
  Badge,
  Button,
  Center,
  Checkbox,
  Group,
  Loader,
  Modal,
  SimpleGrid,
  Stack,
  Text,
  Textarea,
} from "@mantine/core";
import { useEffect, useRef, useState } from "react";

import { ApiErrore } from "../../../../api/http";
import {
  cambiaFoto,
  fotoPossibili,
  rigeneraImmagine,
} from "../../../../api/interventi";
import type { FotoPossibile, PostVista } from "../../../../api/revisione";
import { NOME_CANALE } from "../../campagna/util";
import { AVVISO_CAMPAGNA_APPROVATA } from "./regole";

export function CambiaFoto({
  post,
  approvata,
  apriSuAI = false,
  chiudi,
  fatto,
}: {
  post: PostVista;
  /** Campagna attiva o sospesa: la versione nuova la approva l'operatore. */
  approvata: boolean;
  /** Se vero, la finestra si apre posizionata sulla quarta scelta. */
  apriSuAI?: boolean;
  chiudi: () => void;
  fatto: () => void;
}) {
  const [foto, setFoto] = useState<FotoPossibile[] | null>(null);
  const [occupata, setOccupata] = useState<number | null>(null);
  const [errore, setErrore] = useState<string | null>(null);

  // Quarta scelta: Crea una nuova immagine AI e Rifai il post (R-49, ADR-119)
  const [notaImmagine, setNotaImmagine] = useState("");
  const [riscriviTesto, setRiscriviTesto] = useState(true);
  const [notaTesto, setNotaTesto] = useState("");
  const [invioAI, setInvioAI] = useState(false);
  const aiRef = useRef<HTMLDivElement>(null);

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
              : "Impossibile caricare le foto. Riprova.",
          );
      });
    return () => {
      attivo = false;
    };
  }, [post.post_id]);

  useEffect(() => {
    if (apriSuAI && aiRef.current) {
      aiRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [apriSuAI, foto]);

  const usa = async (fotoId: number) => {
    setOccupata(fotoId);
    setErrore(null);
    try {
      await cambiaFoto(
        post.post_id,
        fotoId,
        !approvata && riscriviTesto,
        !approvata && riscriviTesto && notaTesto.trim()
          ? notaTesto.trim()
          : null,
      );
      fatto();
    } catch (e) {
      setErrore(
        e instanceof ApiErrore
          ? e.message
          : "Impossibile cambiare la foto. Riprova.",
      );
    } finally {
      setOccupata(null);
    }
  };

  const creaAI = async () => {
    setInvioAI(true);
    setErrore(null);
    try {
      await rigeneraImmagine(
        post.post_id,
        notaImmagine.trim() || null,
        riscriviTesto,
        notaTesto.trim() || null,
      );
      fatto();
    } catch (e) {
      setErrore(
        e instanceof ApiErrore
          ? e.message
          : "Impossibile creare la nuova immagine AI. Riprova.",
      );
    } finally {
      setInvioAI(false);
    }
  };

  const sezioni = [
    {
      chiave: "gruppo",
      titolo: "Dello stesso gruppo",
      voci:
        foto?.filter((f) => !f.provenienza || f.provenienza === "gruppo") ?? [],
    },
    {
      chiave: "campagna",
      titolo: "Della campagna",
      voci: foto?.filter((f) => f.provenienza === "campagna") ?? [],
    },
    {
      chiave: "archivio",
      titolo: "Dall'archivio della bottega",
      voci: foto?.filter((f) => f.provenienza === "archivio") ?? [],
    },
  ].filter((s) => s.voci.length > 0);

  return (
    <Modal
      opened
      onClose={chiudi}
      title={`Cambia immagine · ${NOME_CANALE[post.canale] ?? post.canale}`}
      size="lg"
    >
      <Stack gap="sm">
        {approvata && (
          <Alert color="yellow" variant="light" py="xs">
            {AVVISO_CAMPAGNA_APPROVATA}
          </Alert>
        )}
        <Text size="sm" c="dimmed">
          Il testo non cambia: va ricontrollato dopo la sostituzione. Sono
          escluse le foto già usate da un altro post dello stesso canale.
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
        {sezioni.map((sezione) => (
          <Stack key={sezione.chiave} gap="xs">
            <Text fw={600} size="sm">
              {sezione.titolo}
            </Text>
            <SimpleGrid cols={{ base: 1, sm: 2 }} spacing="sm">
              {sezione.voci.map((f) => (
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
                    alt={f.soggetto ?? `Foto ${f.foto_id}`}
                    style={{
                      width: "100%",
                      height: 160,
                      objectFit: "cover",
                      borderRadius: 6,
                      display: "block",
                    }}
                  />
                  {f.soggetto && (
                    <Text size="xs" c="dimmed" lineClamp={2}>
                      {f.soggetto}
                    </Text>
                  )}
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
                        Nuova foto dell’artigiano: da controllare
                      </Badge>
                    )}
                    <Button
                      size="xs"
                      color="verde"
                      loading={occupata === f.foto_id}
                      disabled={occupata !== null || invioAI}
                      onClick={() => void usa(f.foto_id)}
                    >
                      Usa questa foto
                    </Button>
                  </Group>
                </Stack>
              ))}
            </SimpleGrid>
          </Stack>
        ))}

        {!approvata && (
          <Stack
            ref={aiRef}
            gap="xs"
            p="md"
            style={{
              border: apriSuAI
                ? "2px solid var(--mantine-color-verde-6)"
                : "1px solid var(--mantine-color-default-border)",
              borderRadius: 8,
              backgroundColor: "var(--mantine-color-default-hover)",
            }}
          >
            <Text fw={600} size="sm">
              Crea una nuova immagine AI
            </Text>
            <Textarea
              label="Indicazioni per l'immagine"
              placeholder="Es. Piatti decorati con motivi invernali su fondo chiaro..."
              value={notaImmagine}
              onChange={(e) => setNotaImmagine(e.currentTarget.value)}
              maxLength={500}
              autosize
              minRows={2}
            />
            <Checkbox
              label="Riscrivi anche il testo per la nuova immagine"
              checked={riscriviTesto}
              onChange={(e) => setRiscriviTesto(e.currentTarget.checked)}
            />
            {riscriviTesto && (
              <Textarea
                label="Indicazioni per il testo"
                placeholder="Es. Sottolinea l'artigianalità del processo e le novità..."
                value={notaTesto}
                onChange={(e) => setNotaTesto(e.currentTarget.value)}
                maxLength={500}
                autosize
                minRows={2}
              />
            )}
            <Group justify="flex-end" mt="xs">
              <Button
                size="xs"
                color="verde"
                loading={invioAI}
                disabled={occupata !== null}
                onClick={() => void creaAI()}
              >
                Crea una nuova immagine AI
              </Button>
            </Group>
          </Stack>
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
