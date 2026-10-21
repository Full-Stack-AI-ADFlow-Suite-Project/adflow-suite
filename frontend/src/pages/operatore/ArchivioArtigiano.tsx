/**
 * L'archivio foto di un artigiano visto dall'operatore (spec R-47, CA-96): lo
 * stesso componente dell'artigiano, con il nome della bottega, il ritorno alla
 * pagina dell'artigiano e anche le immagini AI delle campagne non ancora
 * approvate. Sola lettura.
 */
import { Alert, Anchor, Center, Loader, Text } from "@mantine/core";
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { schedaArtigiano, type SchedaArtigiano } from "../../api/artigiani";
import { archivioFoto, type BloccoArchivio } from "../../api/campagne";
import { ApiErrore } from "../../api/http";
import { ArchivioFoto } from "../../components/ArchivioFoto";
import { Guscio } from "../../components/Guscio";

export function ArchivioArtigiano() {
  const id = Number(useParams().id);
  const [scheda, setScheda] = useState<SchedaArtigiano | null>(null);
  const [blocchi, setBlocchi] = useState<BloccoArchivio[] | null>(null);
  const [errore, setErrore] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([schedaArtigiano(id), archivioFoto(id)])
      .then(([s, b]) => {
        setScheda(s);
        setBlocchi(b);
      })
      .catch((e: unknown) =>
        setErrore(
          e instanceof ApiErrore && e.stato === 404
            ? "Artigiano non trovato."
            : "Non sono riuscita a leggere l'archivio foto.",
        ),
      );
  }, [id]);

  const bottega = scheda?.profilo?.nome ?? scheda?.nome;

  return (
    <Guscio
      titolo={bottega ? `Archivio foto · ${bottega}` : "Archivio foto"}
      largo={1000}
    >
      <Anchor component={Link} to={`/artigiani/${id}`} size="sm">
        ← Pagina artigiano
      </Anchor>
      <Text c="dimmed" mt="sm" mb="lg">
        Le foto caricate e le immagini AI di questa bottega, campagna per
        campagna, in sola lettura. Un clic apre la foto grande.
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
      {blocchi && (
        <ArchivioFoto
          blocchi={blocchi}
          lato="operatore"
          vuoto="Questo artigiano non ha ancora foto."
        />
      )}
    </Guscio>
  );
}
