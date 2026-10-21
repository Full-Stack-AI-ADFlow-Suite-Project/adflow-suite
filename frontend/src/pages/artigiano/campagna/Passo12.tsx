/**
 * Passo 12 · Riepilogo e invio: riepilogo in sola lettura, la stima di ciò
 * che uscirà (foto dell'artigiano e immagini AI, R-28), gli avvisi R-25 dal
 * dettaglio, la dichiarazione obbligatoria (R-41) e i blocchi ricontrollati
 * prima di "Invia all'operatore". Nessun minimo di foto.
 */
import { useEffect, useState } from "react";
import {
  Alert,
  Button,
  Checkbox,
  Group,
  Paper,
  SimpleGrid,
  Stack,
  Text,
  Title,
} from "@mantine/core";

import { invia, type CampagnaDettaglio } from "../../../api/campagne";
import { canali as apiCanali } from "../../../api/artigiani";
import { ApiErrore } from "../../../api/http";
import { BadgeCanale, EtichettaCanale } from "../../../components/IconaCanale";
import stile from "./Passo10.module.css";
import { Riga } from "./Riga";

const POST_A_SETTIMANA: Record<string, number> = {
  f1_2: 2,
  f3_4: 3,
  f5_piu: 5,
  decidete_voi: 3,
};

/** I testi degli avvisi di R-25; `foto_poche` dice quanti post avranno un'immagine AI. */
function testoAvviso(avviso: string, daCreareConAI: number): string | null {
  switch (avviso) {
    case "foto_poche":
      return `Le foto caricate sono meno dei post chiesti: ${daCreareConAI} post per canale avranno un'immagine creata con l'AI.`;
    case "riempitivi_molti":
      return "I post senza una tua foto sono più di uno ogni due foto caricate: aggiungine qualcuna, se puoi.";
    case "frequenza_alta":
      return "Il ritmo è alto rispetto alle foto che hai dichiarato di poter fare: valuta se abbassarlo nel profilo.";
    default:
      return null;
  }
}

/** Che cosa uscirà su un canale, con `n` post chiesti e `nFoto` foto caricate. */
function stimaCanale(n: number, nFoto: number): string {
  if (nFoto === 0) return `${n} post programmati (tutti con immagine AI)`;
  if (nFoto < n)
    return `${n} post · ${nFoto} da scatti caricati · ${
      n - nFoto
    } con immagine AI`;
  if (nFoto === n) return `${n} post da scatti caricati`;
  return `${n} post da scatti caricati (selezione automatica dei ${n} scatti più idonei)`;
}

function dataIT(iso: string): string {
  const [a, m, g] = iso.split("-");
  return `${g}/${m}/${a}`;
}

export function Passo12({
  campagna,
  onInviata,
  onIndietro,
}: {
  campagna: CampagnaDettaglio;
  onInviata: () => Promise<void>;
  onIndietro?: () => void;
}) {
  const [errore, setErrore] = useState("");
  const [inCorso, setInCorso] = useState(false);
  const [collegati, setCollegati] = useState<string[]>([]);
  const [dichiarazione, setDichiarazione] = useState(false);
  const [tentatoInvio, setTentatoInvio] = useState(false);

  useEffect(() => {
    apiCanali()
      .then((lista) =>
        setCollegati(lista.filter((c) => c.collegato).map((c) => c.canale)),
      )
      .catch(() => setCollegati([]));
  }, []);

  const gruppiFoto = campagna.gruppi.filter((g) => g.origine === "caricate");
  const nFoto = gruppiFoto.reduce((n, g) => n + g.foto.length, 0);
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

  const avvisi = campagna.avvisi
    .map((a) => testoAvviso(a, mancanti))
    .filter((t): t is string => t !== null);

  const blocchi: string[] = [];
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
    setTentatoInvio(true);
    if (!dichiarazione || blocchi.length > 0) return;
    setErrore("");
    setInCorso(true);
    try {
      await invia(campagna.id, dichiarazione);
      await onInviata();
    } catch (e) {
      setErrore(e instanceof ApiErrore ? e.dettaglio : "Errore inatteso.");
      setInCorso(false);
    }
  };

  return (
    <Paper radius="lg" p={{ base: "md", sm: "xl" }} className={stile.form}>
      <header className={stile.intestazione}>
        {onIndietro && (
          <Text
            size="sm"
            c="verde"
            fw={600}
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
        <Text className={stile.sopratitolo}>
          Nuova campagna · Passaggio 3 di 3
        </Text>
        <Title order={2} className={stile.titolo}>
          Verifica e invio al consorzio
        </Title>
        <Text className={stile.descrizione}>
          Verifica i parametri della campagna e conferma la dichiarazione per
          procedere con l'invio.
        </Text>
        <div className={stile.avanzamento} aria-label="Passaggio 3 di 3">
          <span className={stile.attivo} />
          <span className={stile.attivo} />
          <span className={stile.attivo} />
        </div>
      </header>
      <Stack gap="md" className={stile.campi}>
        <section className={stile.sezione}>
          <Group justify="space-between" align="center" mb="sm" wrap="wrap">
            <div>
              <Text size="xs" c="dimmed" fw={600} tt="uppercase" lts={0.5}>
                Campagna
              </Text>
              <Title order={3} size="h4" mt={2}>
                {campagna.titolo}
              </Title>
            </div>
            <Group gap={6} wrap="wrap">
              {(campagna.canali ?? []).map((c) => (
                <BadgeCanale key={c} canale={c} size="sm" />
              ))}
            </Group>
          </Group>

          <SimpleGrid cols={{ base: 2, sm: 4 }} spacing="xs" mb="sm">
            <Paper radius="md" p="sm" bg="#ffffff">
              <Text size="xs" c="dimmed" fw={600}>
                Periodo
              </Text>
              <Text size="sm" fw={600} mt={2}>
                {dataIT(campagna.inizio)} → {dataIT(campagna.fine)}
              </Text>
              <Text size="xs" c="dimmed">
                {giorni} giorni
              </Text>
            </Paper>
            <Paper radius="md" p="sm" bg="#ffffff">
              <Text size="xs" c="dimmed" fw={600}>
                Ritmo
              </Text>
              <Text size="sm" fw={600} mt={2}>
                {postSett} post / sett.
              </Text>
              <Text size="xs" c="dimmed">
                per ogni canale
              </Text>
            </Paper>
            <Paper radius="md" p="sm" bg="#ffffff">
              <Text size="xs" c="dimmed" fw={600}>
                Foto caricate
              </Text>
              <Text size="sm" fw={600} mt={2}>
                {nFoto} foto
              </Text>
              <Text size="xs" c="dimmed">
                in {gruppiFoto.length} gruppi
              </Text>
            </Paper>
            <Paper radius="md" p="sm" bg="#ffffff">
              <Text size="xs" c="dimmed" fw={600}>
                Uscite previste
              </Text>
              <Text size="sm" fw={600} mt={2}>
                {chiesti} post / canale
              </Text>
              <Text size="xs" c="dimmed">
                {mancanti > 0 ? `${mancanti} con AI` : "tutte con tue foto"}
              </Text>
            </Paper>
          </SimpleGrid>

          {(campagna.canali ?? []).map((c) => (
            <Riga
              key={c}
              nome={<EtichettaCanale canale={c} size={16} />}
              valore={stimaCanale(
                campagna.post_chiesti_per_canale[c] ?? chiesti,
                nFoto,
              )}
            />
          ))}
        </section>

        {avvisi.length > 0 && (
          <Alert color="orange" variant="light" py="sm">
            <Text size="xs" fw={600}>
              Nota: {avvisi[0]}
            </Text>
          </Alert>
        )}

        <Paper
          withBorder
          radius="md"
          p="md"
          style={{
            background: dichiarazione ? "#e8f7f5" : "#ffffff",
            borderColor: dichiarazione
              ? "rgba(0, 121, 116, 0.35)"
              : "rgba(16, 29, 33, 0.1)",
          }}
        >
          <Checkbox
            color="verde"
            checked={dichiarazione}
            onChange={(e) => {
              setDichiarazione(e.currentTarget.checked);
              if (e.currentTarget.checked) setTentatoInvio(false);
            }}
            label="Confermo i dati della campagna; eventuali foto caricate appartengono alla mia bottega e hanno il consenso delle persone ritratte."
            error={
              tentatoInvio && !dichiarazione
                ? "Spunta la casella per inviare la campagna."
                : undefined
            }
          />
        </Paper>

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
        <Group justify="space-between" mt="xs" className={stile.azioni}>
          {onIndietro ? (
            <Button variant="default" onClick={onIndietro}>
              ← Torna alle foto
            </Button>
          ) : (
            <div />
          )}
          <Button
            color="verde"
            loading={inCorso}
            disabled={blocchi.length > 0}
            onClick={manda}
            className={stile.continua}
          >
            Invia all'operatore →
          </Button>
        </Group>
      </Stack>
    </Paper>
  );
}
