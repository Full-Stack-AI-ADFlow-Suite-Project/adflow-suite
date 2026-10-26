/**
 * Le campagne dell'artigiano (docs/pagine/AdFlow-campagne.html, ADR-117, H2):
 * prima quelle in corso, poi quelle in lavorazione, poi le passate. Un clic
 * apre la pagina Campagna su quella campagna.
 */
import { Alert, Button, Center, Group, Loader } from "@mantine/core";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { elenco, type CampagnaElencoItem } from "../../api/campagne";
import { ElencoCampagne } from "../../components/campagne/ElencoCampagne";
import { sezioniDi } from "../../components/campagne/sezioni";
import { Guscio } from "../../components/Guscio";

export function Campagne() {
  const [lista, setLista] = useState<CampagnaElencoItem[] | null>(null);
  const [errore, setErrore] = useState<string | null>(null);

  useEffect(() => {
    elenco()
      .then(setLista)
      .catch(() => setErrore("Impossibile caricare le campagne. Riprova."));
  }, []);

  const haBozza = (lista ?? []).some((c) => c.stato === "bozza");

  return (
    <Guscio titolo="Le tue campagne" largo={900}>
      {errore && (
        <Alert color="red" variant="light" mb="md">
          {errore}
        </Alert>
      )}
      {!lista && !errore && (
        <Center py="xl">
          <Loader color="verde" />
        </Center>
      )}
      {lista && (
        <>
          <Group justify="flex-end" mb="md">
            {!haBozza && (
              <Button component={Link} to="/campagna" variant="default">
                + Nuova campagna
              </Button>
            )}
          </Group>
          <ElencoCampagne
            sezioni={sezioniDi("artigiano", lista)}
            lato="artigiano"
            link={(c) => `/campagna?id=${c.id}`}
            vuoto="Non hai ancora campagne. Creane una con «Nuova campagna»."
          />
        </>
      )}
    </Guscio>
  );
}
