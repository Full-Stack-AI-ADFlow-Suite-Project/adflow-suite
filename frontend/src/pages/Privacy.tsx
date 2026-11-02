/**
 * Privacy: informativa segnaposto raggiungibile dalla vetrina e dalla
 * pagina di accesso, senza sessione. La struttura segue gli artt. 13-14
 * GDPR e i rilievi di T4-107 (RL-040…RL-044): i dati del titolare e i
 * testi definitivi li deve fornire il consorzio — ogni segnaposto è
 * marcato «da completare».
 */
import { Link } from "react-router-dom";
import { Anchor, Container, List, Text, Title } from "@mantine/core";

import stili from "./Privacy.module.css";

const SEGNE = "[da completare col consorzio]";

export function Privacy() {
  return (
    <div className={stili.pagina}>
      <Container size={720} py="xl">
        <Title order={1} className={stili.titolo}>
          Informativa privacy
        </Title>
        <Text c="dimmed" size="sm" mb="xl">
          Bozza di struttura ex artt. 13-14 GDPR · {SEGNE}
        </Text>

        <section className={stili.sezione}>
          <Title order={2} className={stili.titoloSezione}>
            Titolare del trattamento
          </Title>
          <Text>
            Il titolare del trattamento è il consorzio {SEGNE}, raggiungibile
            ai contatti indicati in fondo alla pagina. Eventuale DPO/referente
            privacy: {SEGNE}.
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
              servono il consenso di chi è ritratto {SEGNE}
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
            consenso {SEGNE}.
          </Text>
        </section>

        <section className={stili.sezione}>
          <Title order={2} className={stili.titoloSezione}>
            Destinatari e trasferimenti
          </Title>
          <Text>
            I contenuti approvati sono pubblicati su Facebook e Instagram
            (Meta). Testi e immagini passano per il fornitore AI configurato
            {SEGNE}: possibili trasferimenti fuori dall'UE da inquadrare con
            gli accordi ex art. 28 e capo V GDPR (rilievo RL-042).
          </Text>
        </section>

        <section className={stili.sezione}>
          <Title order={2} className={stili.titoloSezione}>
            Conservazione
          </Title>
          <Text>
            Tempi di conservazione per ciascun dato, storico AI incluso:
            {` ${SEGNE}`} (rilievi RL-019, RL-040).
          </Text>
        </section>

        <section className={stili.sezione}>
          <Title order={2} className={stili.titoloSezione}>
            Diritti dell'interessato
          </Title>
          <Text>
            Artt. 15-22 GDPR: accesso, rettifica, cancellazione, limitazione,
            portabilità, opposizione. Si esercitano scrivendo al consorzio ai
            contatti sotto; la procedura di cancellazione/anonimizzazione va
            definita (rilievo RL-041). Reclamo al Garante per la protezione
            dei dati personali.
          </Text>
        </section>

        <Text size="sm" mt="xl">
          <Anchor component={Link} to="/">
            ← Torna alla home
          </Anchor>
        </Text>
      </Container>
    </div>
  );
}
