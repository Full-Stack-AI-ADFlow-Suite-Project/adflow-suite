import layout from "../../../components/Layout.module.css";
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
  Stack,
  Text,
  Title,
} from "@mantine/core";

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

/** I testi degli avvisi di R-25; `foto_poche` dice quanti post avranno un'immagine AI. */
function testoAvviso(avviso: string, daCreareConAI: number): string | null {
  switch (avviso) {
    case "foto_poche":
      return `Le foto caricate sono meno dei post chiesti: ${daCreareConAI} post per canale avranno un'immagine creata con l'AI.`;
    case "riempitivi_molti":
      return "I post senza una tua foto sono più di uno ogni due foto caricate: aggiungine qualcuna, se puoi.";
    case "frequenza_alta":
      return "Il ritmo è alto rispetto alle foto che hai dichiarato di poter fare: valuta se abbassarlo nel profilo.";
    case "campagne_sovrapposte":
      return "Nello stesso periodo hai già un'altra campagna: i post delle due campagne usciranno insieme sulla tua pagina.";
    default:
      return null;
  }
}

/** Che cosa uscirà su un canale, con `n` post chiesti e `nFoto` foto caricate. */
function stimaCanale(n: number, nFoto: number): string {
  if (nFoto === 0) return `${n} post, tutti con un'immagine creata dall'AI`;
  if (nFoto < n)
    return `${n} post · ${nFoto} con le tue foto · ${
      n - nFoto
    } con un'immagine creata dall'AI`;
  if (nFoto === n) return `${n} post con le tue foto`;
  return `${n} post con le tue foto · usiamo le ${n} migliori secondo l'analisi; le altre restano tra le foto della campagna`;
}

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
  const [dichiarazione, setDichiarazione] = useState(false);

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
      blocchi.push(`Racconta cosa mostrano le foto della serie ${i + 1}.`);
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
      await invia(campagna.id, dichiarazione);
      await onInviata();
    } catch (e) {
      setErrore(
        e instanceof ApiErrore
          ? e.dettaglio
          : "Impossibile completare l’operazione. Riprova.",
      );
      setInCorso(false);
    }
  };

  return (
    <Paper withBorder radius="md" p={{ base: "md", sm: "xl" }}>
      {onIndietro && (
        <Text
          size="sm"
          c="verde"
          td="underline"
          mb="xs"
          component="button"
          mih={44}
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
        Hai controllato tutto prima di inviare?
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
            Quanti post usciranno?
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
            valore={`${nFoto} foto in ${gruppiFoto.length} serie`}
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
              valore={stimaCanale(
                campagna.post_chiesti_per_canale[c] ?? chiesti,
                nFoto,
              )}
            />
          ))}
        </div>
        {avvisi.length > 0 && (
          <Alert color="orange" variant="light">
            <b>Avvisi, puoi inviare lo stesso.</b>
            <ul style={{ margin: "6px 0 0", paddingLeft: 20 }}>
              {avvisi.map((a) => (
                <li key={a}>{a}</li>
              ))}
            </ul>
          </Alert>
        )}
        {mancanti > 0 && (
          <Alert color="verde" variant="light">
            Le immagini create dall'AI mostrano ambienti, materiali, attrezzi,
            lavorazioni, atmosfere e stagioni: mai un prodotto finito come se
            fosse tuo, mai persone riconoscibili, testi o marchi. Sono quadrate
            e il post dice "Immagine creata con AI". Le controlla il consorzio
            prima che escano.
          </Alert>
        )}
        <Checkbox
          color="verde"
          required
          checked={dichiarazione}
          onChange={(e) => setDichiarazione(e.currentTarget.checked)}
          label="Le foto mostrano prodotti della mia bottega; le persone riconoscibili hanno dato il consenso."
          error={
            dichiarazione
              ? undefined
              : "Per inviare conferma la dichiarazione sulle foto."
          }
        />
        {blocchi.length > 0 && (
          <Alert
            color="red"
            variant="light"
            title="Cosa manca per inviare la campagna?"
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
        <Group className={layout.azioni} justify="space-between" mt="sm">
          {onIndietro ? (
            <Button variant="light" onClick={onIndietro}>
              ← Torna alle foto
            </Button>
          ) : (
            <div />
          )}
          <Button
            color="verde"
            size="lg"
            loading={inCorso}
            disabled={blocchi.length > 0 || !dichiarazione}
            onClick={manda}
          >
            Invia all'operatore
          </Button>
        </Group>
      </Stack>
    </Paper>
  );
}
