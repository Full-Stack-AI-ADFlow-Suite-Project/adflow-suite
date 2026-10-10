import { Select, SimpleGrid, Stack } from "@mantine/core";

import type {
  DatiProfilo,
  SCELTE as ScelteTipo,
} from "../../../../api/artigiani";
import { SezioneLogo } from "./SezioneLogo";
import { SezioneArchivio } from "./SezioneArchivio";

export function Passo7({
  dati,
  cambia,
  scelte,
  logo,
  onLogoCambiato,
}: {
  dati: DatiProfilo;
  cambia: <K extends keyof DatiProfilo>(
    campo: K,
    valore: DatiProfilo[K],
  ) => void;
  scelte: typeof ScelteTipo;
  logo: string | null;
  onLogoCambiato: (nuovoLogo: string | null) => void;
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
        {policy("quantita_mese", "Quante fotografie puoi fornire al mese?")}
        {policy("chi_scatta", "Chi scatta le fotografie?")}
        {policy("persone", "Persone riconoscibili nelle foto")}
      </SimpleGrid>

      <SezioneLogo logo={logo} onLogoCambiato={onLogoCambiato} />

      <SezioneArchivio />
    </Stack>
  );
}
