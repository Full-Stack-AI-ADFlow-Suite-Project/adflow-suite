/**
 * Privacy: informativa raggiungibile dalla vetrina e dalla pagina di
 * accesso, senza sessione. La struttura segue gli artt. 13-14 GDPR e i
 * rilievi di T4-107 (RL-040…RL-044): i punti ancora aperti sono marcati
 * «in fase di definizione con il consorzio»; i contatti del titolare
 * arrivano da GET /api/consorzio.
 */
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Anchor, Container, List, Text, Title } from "@mantine/core";

import { consorzio } from "../api/consorzio";
import type { Consorzio } from "../api/accesso";
import stili from "./Privacy.module.css";

const MANCANTE = "in fase di definizione con il consorzio";

export function Privacy() {
  const [contatto, setContatto] = useState<Consorzio | null>(null);

  useEffect(() => {
    consorzio()
      .then(setContatto)
      .catch(() => setContatto(null));
  }, []);

  const titolare = contatto
    ? `${contatto.nome} (tel. ${contatto.telefono}, ${contatto.email})`
    : MANCANTE;

  return (
    <main className={stili.pagina}>
      <Container size={720} py="xl">
        <Title order={1} className={stili.titolo}>
          Informativa privacy
        </Title>
        <Text c="dimmed" size="sm" mb="xl">
          Struttura ex artt. 13-14 GDPR · i punti segnati sono {MANCANTE}
        </Text>

        <section className={stili.sezione}>
          <Title order={2} className={stili.titoloSezione}>
            Titolare del trattamento
          </Title>
          <Text>
            Il titolare del trattamento è il consorzio {titolare}. Eventuale
            DPO/referente privacy: {MANCANTE}.
          </Text>
        </section>

        <section className={stili.sezione}>
          <Title order={2} className={stili.titoloSezione}>
            Dati trattati
          </Title>
          <List spacing={4}>
            <List.Item>
              Account: email, nome e ruolo di artigiani, operatori e admin
            </List.Item>
            <List.Item>
              Profilo della bottega: nome, referente, città, contatti e
              descrizione dell'attività
            </List.Item>
            <List.Item>
              Foto caricate dall'artigiano, che possono ritrarre persone:
              servono il consenso di chi è ritratto ({MANCANTE})
            </List.Item>
            <List.Item>
              Testi e immagini generati con AI e relativi storici di
              generazione
            </List.Item>
            <List.Item>
              Dati tecnici di sessione: un cookie di sessione necessario e,
              solo se richiesto («Ricordami»), l'email salvata nel browser
            </List.Item>
          </List>
        </section>

        <section className={stili.sezione}>
          <Title order={2} className={stili.titoloSezione}>
            Finalità e base giuridica
          </Title>
          <Text>
            I dati servono a creare e pubblicare campagne social per le
            botteghe del consorzio: preparazione di testi e immagini con AI,
            calendario editoriale, pubblicazione su Facebook e Instagram,
            gestione degli accessi. Base giuridica: esecuzione del servizio
            richiesto dall'artigiano; per le foto che ritraggono persone, il
            consenso ({MANCANTE}).
          </Text>
        </section>

        <section className={stili.sezione}>
          <Title order={2} className={stili.titoloSezione}>
            Destinatari e trasferimenti
          </Title>
          <Text>
            I contenuti approvati sono pubblicati su Facebook e Instagram
            (Meta). Testi e immagini passano per il fornitore AI configurato
            ({MANCANTE}): possibili trasferimenti fuori dall'UE da inquadrare
            con gli accordi ex art. 28 e capo V GDPR (rilievo RL-042).
          </Text>
        </section>

        <section className={stili.sezione}>
          <Title order={2} className={stili.titoloSezione}>
            Conservazione
          </Title>
          <Text>
            Tempi di conservazione per ciascun dato, storico AI incluso:
            {` ${MANCANTE}`} (rilievi RL-019, RL-040).
          </Text>
        </section>

        <section className={stili.sezione}>
          <Title order={2} className={stili.titoloSezione}>
            Diritti dell'interessato
          </Title>
          <Text>
            Artt. 15-22 GDPR: accesso, rettifica, cancellazione, limitazione,
            portabilità, opposizione. Si esercitano scrivendo al consorzio ai
            contatti indicati sopra; la procedura di
            cancellazione/anonimizzazione va definita (rilievo RL-041).
            Reclamo al Garante per la protezione dei dati personali.
          </Text>
        </section>

        <Text size="sm" mt="xl">
          <Anchor component={Link} to="/">
            ← Torna alla home
          </Anchor>
        </Text>
      </Container>
    </main>
  );
}
