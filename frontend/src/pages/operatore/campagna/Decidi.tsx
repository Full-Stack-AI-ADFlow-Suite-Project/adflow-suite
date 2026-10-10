/**
 * La barra della decisione in cima a Vedi campagna: cosa chiede lo stato
 * corrente e le tre azioni dello sprint 1 (Approva, Prosegui, Riprova),
 * con l'ultimo errore della generazione accanto a Riprova (R-35).
 */
import {
  Alert,
  Anchor,
  Badge,
  Button,
  Card,
  Group,
  Loader,
  Stack,
  Text,
  Title,
} from "@mantine/core";
import { useState } from "react";

import { ApiErrore } from "../../../api/http";
import type { VediCampagna } from "../../../api/revisione";
import { approva, prosegui, riprova } from "../../../api/revisione";
import { Riga } from "../../artigiano/campagna/Riga";
import { dataOra, erroriDi, NOME_CANALE } from "./util";

function Conti({ vista }: { vista: VediCampagna }) {
  const post = vista.uscite.flatMap((u) => u.post);
  const n = (stato: string) => post.filter((p) => p.stato === stato).length;
  const da = post.filter((p) => p.stato === "da_approvare");
  const rivedere = da.filter((p) => p.da_rivedere).length;
  const conAvvisi = da.filter((p) =>
    erroriDi(p).some((e) => e.livello === "avviso"),
  ).length;
  return (
    <Group gap={6} mt="xs">
      {da.length > 0 && <Badge variant="light">{da.length} da approvare</Badge>}
      {rivedere > 0 && (
        <Badge color="red" variant="light">
          {rivedere} da rivedere
        </Badge>
      )}
      {conAvvisi > 0 && (
        <Badge color="yellow" variant="light">
          {conAvvisi} con avvisi
        </Badge>
      )}
      {n("approvato") > 0 && (
        <Badge variant="light">{n("approvato")} in programma</Badge>
      )}
      {n("pubblicato") > 0 && (
        <Badge color="verde" variant="light">
          {n("pubblicato")} pubblicati
        </Badge>
      )}
      {n("fallito") > 0 && (
        <Badge color="red" variant="light">
          {n("fallito")} falliti
        </Badge>
      )}
      {n("scaduto") > 0 && (
        <Badge color="red" variant="light">
          {n("scaduto")} scaduti
        </Badge>
      )}
      {n("scartato") > 0 && (
        <Badge variant="light">{n("scartato")} scartati</Badge>
      )}
      {n("annullato") > 0 && (
        <Badge color="red" variant="light">
          {n("annullato")} annullati
        </Badge>
      )}
    </Group>
  );
}

function primoDaApprovare(vista: VediCampagna): string | null {
  const date = vista.uscite
    .flatMap((u) => u.post)
    .filter((p) => p.stato === "da_approvare")
    .map((p) => p.data_ora)
    .sort();
  return date[0] ?? null;
}

export function Decidi({
  vista,
  ricarica,
}: {
  vista: VediCampagna;
  ricarica: () => void;
}) {
  const stato = vista.campagna.stato;
  const [conferma, setConferma] = useState(false);
  const [occupato, setOccupato] = useState(false);
  const [errore, setErrore] = useState<string | null>(null);

  const post = vista.uscite.flatMap((u) => u.post);
  const daApprovare = post.filter((p) => p.stato === "da_approvare");
  const daRivedere = daApprovare.filter((p) => p.da_rivedere);
  const inCorso = daApprovare.filter((p) => p.intervento_in_corso);
  const blocca =
    daRivedere.length > 0 || inCorso.length > 0 || !daApprovare.length;

  const agisci = async (azione: () => Promise<unknown>) => {
    setOccupato(true);
    setErrore(null);
    try {
      await azione();
      ricarica();
    } catch (e) {
      setErrore(
        e instanceof ApiErrore ? e.message : "Qualcosa non ha funzionato.",
      );
    } finally {
      setOccupato(false);
      setConferma(false);
    }
  };

  let contenuto = null;
  if (stato === "inviata" || stato === "in_generazione") {
    contenuto = (
      <>
        <Title order={2} size="h3">
          Generazione in corso
        </Title>
        <Text size="sm" c="dimmed">
          {vista.piano
            ? "Il piano e ciò che era già salvato non si rifanno: la generazione riparte dai testi che mancano."
            : "Analisi delle foto e piano editoriale."}{" "}
          Se resta ferma per 30 minuti passa a generazione fallita.
        </Text>
        <Group gap="xs" mt="xs" c="yellow">
          <Loader size="xs" color="yellow" />
          <Text size="sm">L'AI sta lavorando.</Text>
        </Group>
      </>
    );
  } else if (stato === "generazione_fallita") {
    const e = vista.ultimo_errore;
    contenuto = (
      <Group justify="space-between" align="flex-start" wrap="wrap">
        <Stack gap={6} style={{ flex: "1 1 420px" }}>
          <Title order={2} size="h3">
            Generazione fallita
          </Title>
          <Text size="sm" c="dimmed">
            La generazione si è fermata. Riprova riparte da dove si era fermata:
            ciò che è salvato non si rifà.
          </Text>
          {e && (
            <Stack gap={0} mt={4}>
              <Riga
                nome="Tipo di errore"
                valore={
                  <>
                    <Badge color="red" variant="light" ff="monospace">
                      {e.tipo}
                    </Badge>{" "}
                    {e.tipo === "temporaneo" || e.tipo === "risposta"
                      ? "Riprovare serve."
                      : "Riprovare non serve finché qualcuno non interviene."}
                  </>
                }
              />
              <Riga nome="Messaggio" valore={e.messaggio} />
              <Riga
                nome="Dove"
                valore={`Tappa: ${e.tappa} · canale: ${
                  e.canale ? NOME_CANALE[e.canale] ?? e.canale : "—"
                } · ${dataOra(e.creata_il)}`}
              />
            </Stack>
          )}
          <Conti vista={vista} />
        </Stack>
        <Stack gap="xs" align="stretch">
          <Button
            color="verde"
            loading={occupato}
            onClick={() => void agisci(() => riprova(vista.campagna.id))}
          >
            Riprova
          </Button>
        </Stack>
      </Group>
    );
  } else if (stato === "piano_da_rivedere") {
    contenuto = (
      <Group justify="space-between" align="flex-start" wrap="wrap">
        <Stack gap={6} style={{ flex: "1 1 420px" }}>
          <Title order={2} size="h3">
            Piano da rivedere
          </Title>
          <Text size="sm" c="dimmed">
            Il piano è debole e la generazione si è fermata prima dei testi:
            guarda il piano e le foto, poi decidi.
          </Text>
          {primoDaApprovare(vista) && (
            <Text size="sm">
              <b>Entro quando:</b> il primo post da approvare è{" "}
              {dataOra(primoDaApprovare(vista) ?? "")}. Senza piano la campagna
              scade alle 00:00 del giorno di inizio.
            </Text>
          )}
          <Conti vista={vista} />
        </Stack>
        <Button
          color="verde"
          loading={occupato}
          onClick={() => void agisci(() => prosegui(vista.campagna.id))}
        >
          Prosegui: scrivi i testi
        </Button>
      </Group>
    );
  } else if (stato === "in_revisione") {
    contenuto = (
      <>
        <Group justify="space-between" align="flex-start" wrap="wrap">
          <Stack gap={6} style={{ flex: "1 1 420px" }}>
            <Title order={2} size="h3">
              Decisione sulla campagna
            </Title>
            {primoDaApprovare(vista) && (
              <Text size="sm">
                <b>
                  Entro quando: il primo post da approvare è{" "}
                  {dataOra(primoDaApprovare(vista) ?? "")}.
                </b>{" "}
                Ogni post scade quando passa la sua data.
              </Text>
            )}
            <Conti vista={vista} />
          </Stack>
          <Button
            color="verde"
            disabled={blocca}
            onClick={() => setConferma(true)}
          >
            Approva {daApprovare.length} post
          </Button>
        </Group>
        {daRivedere.length > 0 && (
          <Text size="sm" mt="sm">
            <Text span c="red" fw={500}>
              Non si può approvare:
            </Text>{" "}
            {daRivedere.map((p, i) => (
              <span key={p.post_id}>
                {i > 0 && ", "}
                <Anchor href={`#post-${p.post_id}`}>
                  uscita {vista.uscite.find((u) => u.post.includes(p))?.numero}{" "}
                  · {NOME_CANALE[p.canale] ?? p.canale}
                </Anchor>
              </span>
            ))}{" "}
            da rivedere. Il post con un blocco si sistema dalla 2b.
          </Text>
        )}
        {inCorso.length > 0 && (
          <Text size="sm" mt="xs">
            <Text span c="red" fw={500}>
              Non si può approvare:
            </Text>{" "}
            intervento in corso su {inCorso.length} post.
          </Text>
        )}
        {conferma && !blocca && (
          <Card withBorder radius="md" mt="md" bg="var(--mantine-color-body)">
            <Title order={3} size="h5">
              Approvi {daApprovare.length} post?
            </Title>
            <Text size="sm" c="dimmed" mt={4}>
              La campagna diventa attiva e i post escono da soli alle date
              stabilite. Dopo, il contenuto non si modifica più.
            </Text>
            <Group mt="sm">
              <Button
                color="verde"
                loading={occupato}
                onClick={() => void agisci(() => approva(vista.campagna.id))}
              >
                Conferma: approva {daApprovare.length} post
              </Button>
              <Button variant="default" onClick={() => setConferma(false)}>
                Annulla
              </Button>
            </Group>
          </Card>
        )}
      </>
    );
  } else if (stato === "attiva" || stato === "sospesa") {
    const adesso =
      // eslint-disable-next-line react/purity
      new Date().toISOString();
    const prossimo = post
      .filter((p) => p.stato === "approvato" && p.data_ora > adesso)
      .sort((a, b) => a.data_ora.localeCompare(b.data_ora))[0];
    contenuto = (
      <>
        <Title order={2} size="h3">
          {stato === "attiva" ? "Campagna attiva" : "Campagna sospesa"}
        </Title>
        <Text size="sm" c="dimmed">
          {stato === "attiva"
            ? prossimo
              ? `Prossima pubblicazione: ${dataOra(prossimo.data_ora)} · ${
                  NOME_CANALE[prossimo.canale] ?? prossimo.canale
                }.`
              : "Nessun post in attesa."
            : "Nessun post esce finché non la riattivi."}{" "}
          Il contenuto non si modifica più.
        </Text>
        <Conti vista={vista} />
      </>
    );
  } else {
    const titoli: Record<string, [string, string]> = {
      respinta: [
        "Campagna respinta",
        "Chiusa: resta nello storico e l'artigiano ne crea una nuova.",
      ],
      scaduta: [
        "Campagna scaduta",
        "I post rimasti sono scaduti e l'artigiano è stato avvisato.",
      ],
      conclusa: [
        "Campagna conclusa",
        "Ogni post è chiuso: pubblicato, fallito, scaduto o scartato.",
      ],
      annullata: [
        "Campagna annullata",
        "Non esce più niente: i post non usciti sono nello stato annullato.",
      ],
    };
    const [titolo, sotto] = titoli[stato] ?? ["Campagna", ""];
    contenuto = (
      <>
        <Title order={2} size="h3">
          {titolo}
        </Title>
        <Text size="sm" c="dimmed">
          {sotto}
        </Text>
        <Conti vista={vista} />
      </>
    );
  }

  return (
    <Card withBorder radius="lg" p="lg" aria-label="Decisione sulla campagna">
      <Stack gap="sm">
        {contenuto}
        {errore && (
          <Alert color="red" variant="light">
            {errore}
          </Alert>
        )}
      </Stack>
    </Card>
  );
}
