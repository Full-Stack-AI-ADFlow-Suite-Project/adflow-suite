/**
 * Passo 12 · Riepilogo e invio: riepilogo in sola lettura, la stima di ciò
 * che uscirà (sprint 1: le cartoline), gli avvisi R-25 dal dettaglio e i
 * blocchi ricontrollati prima di "Invia all'operatore".
 */
import { useEffect, useState } from "react";
import { Alert, Button, Group, Paper, Stack, Text, Title } from "@mantine/core";

import { invia, type CampagnaDettaglio } from "../../../api/campagne";
import {
  canali as apiCanali,
  type ProfiloBottega,
} from "../../../api/artigiani";
import { ApiErrore } from "../../../api/http";
import { Riga } from "./Riga";

const POST_A_SETTIMANA: Record<string, number> = {
  f1_2: 2,
  f3_4: 3,
  f5_piu: 5,
  decidete_voi: 3,
};

const TESTI_AVVISI: Record<string, string> = {
  foto_poche:
    "Le foto sono meno dei post chiesti: i post che mancano saranno cartoline.",
  riempitivi_molti:
    "Più di un post su due sarà una cartolina: con qualche foto in più escono più post con le tue foto.",
  frequenza_alta:
    "Il ritmo è alto rispetto alle foto che hai dichiarato di poter fare: valuta se abbassarlo nel profilo.",
};

function dataIT(iso: string): string {
  const [a, m, g] = iso.split("-");
  return `${g}/${m}/${a}`;
}

export function Passo12({
  campagna,
  profilo,
  onInviata,
  onIndietro,
}: {
  campagna: CampagnaDettaglio;
  profilo: ProfiloBottega;
  onInviata: () => Promise<void>;
  onIndietro?: () => void;
}) {
  const [errore, setErrore] = useState("");
  const [inCorso, setInCorso] = useState(false);
  const [collegati, setCollegati] = useState<string[]>([]);

  useEffect(() => {
    apiCanali()
      .then((lista) =>
        setCollegati(lista.filter((c) => c.collegato).map((c) => c.canale)),
      )
      .catch(() => setCollegati([]));
  }, []);

  const gruppiFoto = campagna.gruppi.filter((g) => g.origine === "caricate");
  const nFoto = gruppiFoto.reduce((n, g) => n + g.foto.length, 0);
  const nStelle = gruppiFoto.reduce(
    (n, g) => n + g.foto.filter((f) => f.da_usare).length,
    0,
  );
  const chiesti = Math.max(
    0,
    ...Object.values(campagna.post_chiesti_per_canale),
  );
  const mancanti = Math.max(0, chiesti - nFoto);
  const postSett = POST_A_SETTIMANA[campagna.frequenza ?? ""] ?? 3;
  const giorni =
    Math.round(
      (new Date(campagna.fine + "T00:00:00").getTime() -
        new Date(campagna.inizio + "T00:00:00").getTime()) /
        86400000,
    ) + 1;

  const blocchi: string[] = [];
  if (nFoto < 4) blocchi.push("Servono almeno 4 foto caricate.");
  campagna.gruppi.forEach((g, i) => {
    if (!g.descrizione?.trim())
      blocchi.push(`Il gruppo ${i + 1} non ha la descrizione.`);
  });
  (campagna.canali ?? [])
    .filter((c) => !collegati.includes(c))
    .forEach((c) =>
      blocchi.push(`${c} non è collegato: contatta il consorzio.`),
    );

  const manda = async () => {
    setErrore("");
    setInCorso(true);
    try {
      await invia(campagna.id);
      await onInviata();
    } catch (e) {
      setErrore(e instanceof ApiErrore ? e.dettaglio : "Errore inatteso.");
      setInCorso(false);
    }
  };

  return (
    <Paper withBorder radius="md" p="xl">
      {onIndietro && (
        <Text
          size="sm"
          c="verde"
          td="underline"
          mb="xs"
          component="button"
          onClick={onIndietro}
          style={{
            background: "none",
            border: "none",
            cursor: "pointer",
            padding: 0,
          }}
        >
          ← Torna alle foto
        </Text>
      )}
      <Text ff="monospace" size="xs" c="verde">
        12 · RIEPILOGO
      </Text>
      <Title order={2} mt={4} mb="lg">
        Rivedi prima di inviare
      </Title>
      <Stack gap="lg">
        <div>
          <Title order={4} mb={4}>
            Identità
          </Title>
          <Riga nome="Bottega" valore={profilo.bottega} />
          <Riga nome="Referente" valore={profilo.referente} />
          <Riga nome="Città" valore={profilo.citta} />
        </div>
        <div>
          <Title order={4} mb={4}>
            Prodotti e pubblico
          </Title>
          <Riga nome="Tipo di prodotto" valore={profilo.tipo_prodotto} />
          <Riga nome="Obiettivo" valore={profilo.obiettivo} />
        </div>
        <div>
          <Title order={4} mb={4}>
            Logistica
          </Title>
          <Riga
            nome="Ritmo scelto"
            valore={`${postSett} a settimana per canale · con ${
              (campagna.canali ?? []).length
            } canali ${
              postSett * (campagna.canali ?? []).length
            } post a settimana`}
          />
        </div>
        <div>
          <Title order={4} mb={4}>
            Durata e canali
          </Title>
          <Riga nome="Nome campagna" valore={campagna.titolo} />
          <Riga
            nome="Periodo"
            valore={`${dataIT(campagna.inizio)} → ${dataIT(
              campagna.fine,
            )} · ${giorni} giorni`}
          />
          <Riga nome="Canali" valore={(campagna.canali ?? []).join(", ")} />
          <Riga nome="Post chiesti" valore={`${chiesti} per canale`} />
        </div>
        <div>
          <Title order={4} mb={4}>
            Foto della campagna
          </Title>
          <Riga
            nome="Foto caricate"
            valore={`${nFoto} foto in ${gruppiFoto.length} gruppi · ${nStelle} con la stella`}
          />
        </div>
        <div>
          <Title order={4} mb={4}>
            Che cosa uscirà · stima
          </Title>
          {(campagna.canali ?? []).map((c) => (
            <Riga
              key={c}
              nome={c}
              valore={
                mancanti > 0
                  ? `${
                      campagna.post_chiesti_per_canale[c] ?? chiesti
                    } post · ${Math.min(
                      nFoto,
                      campagna.post_chiesti_per_canale[c] ?? chiesti,
                    )} con le foto di questa campagna · ${Math.max(
                      0,
                      (campagna.post_chiesti_per_canale[c] ?? chiesti) - nFoto,
                    )} cartoline`
                  : `${
                      campagna.post_chiesti_per_canale[c] ?? chiesti
                    } post con le foto di questa campagna`
              }
            />
          ))}
        </div>
        {mancanti > 0 && (
          <Alert color="orange" variant="light">
            <b>Avviso, puoi inviare lo stesso.</b> Con {nFoto} foto, {mancanti}{" "}
            dei {chiesti} post per canale saranno cartoline. Aggiungine{" "}
            {mancanti} per avere solo foto.
          </Alert>
        )}
        {campagna.avvisi.map((a) =>
          a in TESTI_AVVISI &&
          a !== "foto_poche" &&
          a !== "riempitivi_molti" ? (
            <Alert key={a} color="orange" variant="light">
              {TESTI_AVVISI[a]}
            </Alert>
          ) : null,
        )}
        {blocchi.length > 0 && (
          <Alert
            color="red"
            variant="light"
            title="Da sistemare prima dell'invio"
          >
            <ul style={{ margin: 0, paddingLeft: 18 }}>
              {blocchi.map((b) => (
                <li key={b}>{b}</li>
              ))}
            </ul>
          </Alert>
        )}
        {errore && (
          <Alert color="red" variant="light">
            {errore}
          </Alert>
        )}
        <Group justify="space-between" mt="sm">
          {onIndietro ? (
            <Button variant="default" onClick={onIndietro}>
              ← Torna alle foto
            </Button>
          ) : (
            <div />
          )}
          <Button
            color="verde"
            size="lg"
            loading={inCorso}
            disabled={blocchi.length > 0}
            onClick={manda}
          >
            Invia all'operatore
          </Button>
        </Group>
      </Stack>
    </Paper>
  );
}
