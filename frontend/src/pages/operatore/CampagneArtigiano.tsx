/**
 * Le campagne di un artigiano viste dall'operatore
 * (docs/pagine/AdFlow-operatore-artigiano-campagne.html, spec R-38, CA-94):
 * in cima quelle in corso e da approvare, poi lo storico. Un clic apre Vedi
 * campagna; la bozza si apre solo dopo l'invio.
 */
import { Alert, Anchor, Center, Loader, Text } from "@mantine/core";
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { schedaArtigiano, type SchedaArtigiano } from "../../api/artigiani";
import { elenco, type CampagnaElencoItem } from "../../api/campagne";
import { ApiErrore } from "../../api/http";
import { ElencoCampagne } from "../../components/campagne/ElencoCampagne";
import { sezioniDi } from "../../components/campagne/sezioni";
import { Guscio } from "../../components/Guscio";

export function CampagneArtigiano() {
  const id = Number(useParams().id);
  const [scheda, setScheda] = useState<SchedaArtigiano | null>(null);
  const [lista, setLista] = useState<CampagnaElencoItem[] | null>(null);
  const [errore, setErrore] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([schedaArtigiano(id), elenco(undefined, id)])
      .then(([s, l]) => {
        setScheda(s);
        setLista(l);
      })
      .catch((e: unknown) =>
        setErrore(
          e instanceof ApiErrore && e.stato === 404
            ? "Artigiano non trovato."
            : "Impossibile caricare le campagne. Riprova.",
        ),
      );
  }, [id]);

  const bottega = scheda?.profilo?.nome ?? scheda?.nome;

  return (
    <Guscio titolo={bottega ? `Campagne · ${bottega}` : "Campagne"} largo={900}>
      <Anchor component={Link} to={`/artigiani/${id}`} size="sm">
        ← Pagina artigiano
      </Anchor>
      <Text c="dimmed" mt="sm" mb="lg">
        In cima quelle in corso e da approvare; poi lo storico. Un clic apre
        Vedi campagna.
      </Text>

      {errore && (
        <Alert color="red" variant="light">
          {errore}
        </Alert>
      )}
      {!lista && !errore && (
        <Center py="xl">
          <Loader color="verde" />
        </Center>
      )}
      {lista && (
        <ElencoCampagne
          sezioni={sezioniDi("operatore", lista)}
          lato="operatore"
          link={(c) => (c.stato === "bozza" ? null : `/campagne/${c.id}`)}
          vuoto="Questo artigiano non ha ancora campagne."
        />
      )}
    </Guscio>
  );
}
