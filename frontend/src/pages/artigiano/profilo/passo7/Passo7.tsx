import { useEffect, useState } from "react";
import {
  Alert,
  Button,
  Loader,
  Select,
  SimpleGrid,
  Stack,
  Text,
} from "@mantine/core";
import { leggiProfilo } from "../../../../api/artigiani";

import type {
  DatiProfilo,
  SCELTE as ScelteTipo,
} from "../../../../api/artigiani";
import { SezioneArchivio } from "./SezioneArchivio";

export function Passo7({
  dati,
  cambia,
  scelte,
}: {
  dati: DatiProfilo;
  cambia: <K extends keyof DatiProfilo>(
    campo: K,
    valore: DatiProfilo[K],
  ) => void;
  scelte: typeof ScelteTipo;
}) {
  const [profilo, setProfilo] = useState<
    "caricamento" | "presente" | "assente" | "errore"
  >("caricamento");
  const [tentativo, setTentativo] = useState(0);

  useEffect(() => {
    let attivo = true;
    leggiProfilo()
      .then((p) => {
        if (attivo) setProfilo(p ? "presente" : "assente");
      })
      .catch(() => {
        if (attivo) setProfilo("errore");
      });
    return () => {
      attivo = false;
    };
  }, [tentativo]);

  const policy = (
    campo: "quantita_mese" | "chi_scatta" | "persone",
    label: string,
  ) => (
    <Select
      label={label}
      data={scelte[campo]}
      clearable
      value={
        typeof dati?.foto_policy?.[campo] === "string"
          ? (dati.foto_policy[campo] as string)
          : null
      }
      onChange={(v) => {
        const p = { ...dati?.foto_policy };
        if (v) p[campo] = v;
        else delete p[campo];
        cambia("foto_policy", Object.keys(p).length ? p : null);
      }}
    />
  );

  return (
    <Stack gap="lg">
      <SimpleGrid cols={{ base: 1, sm: 3 }} spacing="md">
        {policy("quantita_mese", "Quante fotografie puoi fornire al mese?")}
        {policy("chi_scatta", "Chi scatta le fotografie?")}
        {policy("persone", "Persone riconoscibili nelle foto")}
      </SimpleGrid>

      {profilo === "presente" ? (
        <SezioneArchivio />
      ) : profilo === "assente" ? (
        <Alert color="blue" title="Prima salva il profilo">
          L'archivio della bottega sarà disponibile dopo il primo salvataggio.
          Completa il passo 9, poi riapri Profilo bottega e torna al passo 7 per
          caricare le foto.
        </Alert>
      ) : profilo === "errore" ? (
        <Alert color="red" title="Archivio non disponibile">
          <Text size="sm">
            Non riesco a verificare se il profilo è già salvato. Riprova.
          </Text>
          <Button
            mt="sm"
            variant="default"
            onClick={() => {
              setProfilo("caricamento");
              setTentativo((n) => n + 1);
            }}
          >
            Riprova
          </Button>
        </Alert>
      ) : (
        <Stack align="center" gap="xs">
          <Loader size="sm" aria-label="Verifica del profilo" />
          <Text size="sm" c="dimmed">
            Verifico se l'archivio è disponibile.
          </Text>
        </Stack>
      )}
    </Stack>
  );
}
