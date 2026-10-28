/**
 * Passo 7 · Foto e contenuti: solo le tre preferenze sulle foto. Nell'MVP
 * non ci sono né l'archivio della bottega (A10, congelato: SezioneArchivio
 * resta nel codice, nascosta) né il logo (A7, tolto: è una foto come le
 * altre). Le foto si caricano in ogni campagna.
 */
import { Alert, Select, SimpleGrid, Stack } from "@mantine/core";

import type {
  DatiProfilo,
  SCELTE as ScelteTipo,
} from "../../../../api/artigiani";

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
        {policy("quantita_mese", "Quante foto puoi preparare al mese?")}
        {policy("chi_scatta", "Chi scatta le tue foto?")}
        {policy("persone", "Nelle tue foto ci sono persone riconoscibili?")}
      </SimpleGrid>

      <Alert color="verde" variant="light">
        In ogni campagna puoi caricare le tue foto, raccolte in serie. Se in una
        campagna le foto non bastano per i post a settimana che hai scelto, per
        quelli che mancano creiamo un'immagine con l'AI: ambienti, materiali,
        attrezzi e atmosfere, mai un prodotto che non è tuo. Se hai un logo,
        caricalo come una foto qualsiasi.
      </Alert>
    </Stack>
  );
}
