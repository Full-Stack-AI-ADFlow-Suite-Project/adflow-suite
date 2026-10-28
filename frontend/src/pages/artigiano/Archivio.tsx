/**
 * L'archivio foto dell'artigiano (docs/pagine/AdFlow-archivio-foto.html, spec
 * R-47, ADR-117, H4): le sue foto campagna per campagna, in sola lettura.
 * Le immagini AI compaiono con l'approvazione della campagna.
 */
import { Alert, Center, Loader, Text } from "@mantine/core";
import { useEffect, useState } from "react";

import { archivioFoto, type BloccoArchivio } from "../../api/campagne";
import { ArchivioFoto } from "../../components/ArchivioFoto";
import { Guscio } from "../../components/Guscio";

export function Archivio() {
  const [blocchi, setBlocchi] = useState<BloccoArchivio[] | null>(null);
  const [errore, setErrore] = useState<string | null>(null);

  useEffect(() => {
    archivioFoto()
      .then(setBlocchi)
      .catch(() => setErrore("Impossibile caricare l’archivio foto. Riprova."));
  }, []);

  return (
    <Guscio titolo="Archivio foto" largo={1000}>
      <Text c="dimmed" mb="lg">
        Le foto della bottega, campagna per campagna: quelle che hai caricato e
        le immagini create dall&apos;AI. Un clic apre la foto grande.
      </Text>
      {errore && (
        <Alert color="red" variant="light">
          {errore}
        </Alert>
      )}
      {!blocchi && !errore && (
        <Center py="xl">
          <Loader color="verde" />
        </Center>
      )}
      {blocchi && <ArchivioFoto blocchi={blocchi} lato="artigiano" />}
    </Guscio>
  );
}
