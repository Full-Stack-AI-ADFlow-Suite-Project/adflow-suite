import layout from "../../../components/Layout.module.css";
/**
 * Passo 10 · Durata e canali (R-08, R-22): nome, inizio ≥ oggi+3, fine con
 * durata 7–92 giorni, canali solo tra quelli collegati, descrizione.
 */
import { useEffect, useState } from "react";
import {
  Alert,
  Button,
  Checkbox,
  Chip,
  Group,
  Paper,
  SimpleGrid,
  Stack,
  Text,
  Textarea,
  TextInput,
  Title,
  Tooltip,
} from "@mantine/core";

import type { CampagnaCrea, CampagnaDettaglio } from "../../../api/campagne";
import {
  canali as apiCanali,
  type CanaleCollegato,
  type ProfiloBottega,
} from "../../../api/artigiani";

const NOMI_CANALI: Record<string, string> = {
  facebook: "Facebook",
  instagram: "Instagram",
};

/** Durata in giorni e testo del pulsante (R-08). */
const DURATE_RAPIDE: [number, string][] = [
  [7, "1 settimana"],
  [14, "2 settimane"],
  [30, "1 mese"],
];

function dataISO(giorniDaOggi: number): string {
  const d = new Date();
  d.setDate(d.getDate() + giorniDaOggi);
  return d.toISOString().slice(0, 10);
}

function giorniTra(inizio: string, fine: string): number {
  return (
    Math.round(
      (new Date(fine + "T00:00:00").getTime() -
        new Date(inizio + "T00:00:00").getTime()) /
        86400000,
    ) + 1
  );
}

export function Passo10({
  profilo,
  campagna,
  errore,
  onContinua,
}: {
  profilo: ProfiloBottega;
  campagna?: CampagnaDettaglio | null;
  errore: string;
  onContinua: (dati: CampagnaCrea) => Promise<void>;
}) {
  const [canali, setCanali] = useState<CanaleCollegato[]>([]);
  const [titolo, setTitolo] = useState(campagna?.titolo ?? "");
  const [inizio, setInizio] = useState(campagna?.inizio ?? dataISO(4));
  const [fine, setFine] = useState(campagna?.fine ?? dataISO(34));
  const [scelti, setScelti] = useState<string[]>(
    campagna?.canali && campagna.canali.length > 0
      ? campagna.canali
      : profilo.canali_preferiti,
  );
  const [descrizione, setDescrizione] = useState(campagna?.descrizione ?? "");
  const [errori, setErrori] = useState<Record<string, string>>({});
  const [inCorso, setInCorso] = useState(false);
  // L'errore del server riguarda i dati inviati: se cambiano, non vale più.
  const [inviati, setInviati] = useState("");
  const dati = JSON.stringify([titolo, inizio, fine, scelti, descrizione]);

  useEffect(() => {
    apiCanali()
      .then(setCanali)
      .catch(() => setCanali([]));
  }, []);

  const durata = giorniTra(inizio, fine);

  const scegliDurata = (giorni: number) => {
    const d = new Date(inizio + "T00:00:00");
    d.setDate(d.getDate() + giorni - 1);
    // Data locale: toISOString() la porterebbe indietro di un giorno in Italia.
    const due = (n: number) => String(n).padStart(2, "0");
    setFine(`${d.getFullYear()}-${due(d.getMonth() + 1)}-${due(d.getDate())}`);
  };

  const valida = (): boolean => {
    const e: Record<string, string> = {};
    if (!titolo.trim()) e.titolo = "Dai un nome alla tua campagna.";
    if (giorniTra(dataISO(0), inizio) < 4)
      e.inizio = "Scegli una data di inizio almeno 3 giorni dopo oggi.";
    if (durata < 7) e.fine = "Scegli un periodo di almeno 7 giorni.";
    if (durata > 92) e.fine = "Scegli un periodo di massimo 3 mesi.";
    const collegati = canali.filter((c) => c.collegato).map((c) => c.canale);
    if (!scelti.length) e.canali = "Scegli almeno un canale.";
    else if (!scelti.every((c) => collegati.includes(c)))
      e.canali = "Un canale scelto non è collegato: contatta il consorzio.";
    if (!descrizione.trim())
      e.descrizione = "Racconta cosa vuoi far conoscere con questa campagna.";
    setErrori(e);
    return Object.keys(e).length === 0;
  };

  const invia = async (evento: React.FormEvent) => {
    evento.preventDefault();
    if (!valida()) return;
    setInCorso(true);
    setInviati(dati);
    await onContinua({
      titolo: titolo.trim(),
      inizio,
      fine,
      descrizione: descrizione.trim(),
      canali: scelti,
    });
    setInCorso(false);
  };

  return (
    <Paper
      withBorder
      radius="md"
      p={{ base: "md", sm: "xl" }}
      component="form"
      onSubmit={invia}
    >
      <Text ff="monospace" size="xs" c="verde">
        10 · DURATA E CANALI
      </Text>
      <Title order={2} mt={4} mb="md">
        Cosa vuoi far conoscere con questa campagna?
      </Title>
      <Stack gap="md">
        <TextInput
          label="Come vuoi chiamare la campagna?"
          required
          value={titolo}
          error={errori.titolo}
          onChange={(e) => setTitolo(e.currentTarget.value)}
          placeholder="Campagna Ottobre 2026"
        />
        <SimpleGrid cols={{ base: 1, sm: 2 }}>
          <TextInput
            label="Quando vuoi iniziare?"
            type="date"
            required
            min={dataISO(3)}
            value={inizio}
            error={errori.inizio}
            onChange={(e) => setInizio(e.currentTarget.value)}
          />
          <TextInput
            label="Quando vuoi concludere?"
            type="date"
            required
            min={inizio}
            value={fine}
            error={errori.fine}
            onChange={(e) => setFine(e.currentTarget.value)}
          />
        </SimpleGrid>
        <Text size="xs" c="dimmed">
          L'inizio deve cadere almeno 3 giorni dopo oggi: il consorzio deve
          avere il tempo di approvare i post prima che partano. La campagna dura
          almeno 7 giorni e al massimo 3 mesi.
        </Text>
        <Group gap="xs">
          {DURATE_RAPIDE.map(([giorni, etichetta]) => (
            <Chip
              key={giorni}
              checked={durata === giorni}
              onChange={() => scegliDurata(giorni)}
              color="verde"
            >
              {etichetta}
            </Chip>
          ))}
        </Group>
        <div>
          <Text size="sm" fw={500} mb={6}>
            Su quali social vuoi far uscire i post? *
          </Text>
          <Group gap="xs">
            {canali.map((c) =>
              c.collegato ? (
                <Checkbox
                  key={c.canale}
                  label={NOMI_CANALI[c.canale] ?? c.canale}
                  checked={scelti.includes(c.canale)}
                  onChange={(e) =>
                    setScelti(
                      e.currentTarget.checked
                        ? [...scelti, c.canale]
                        : scelti.filter((k) => k !== c.canale),
                    )
                  }
                />
              ) : (
                <Tooltip key={c.canale} label="Contatta il consorzio">
                  <Checkbox
                    label={`${
                      NOMI_CANALI[c.canale] ?? c.canale
                    } non è collegato`}
                    disabled
                  />
                </Tooltip>
              ),
            )}
          </Group>
          {errori.canali && (
            <Text size="xs" c="red" mt={4}>
              {errori.canali}
            </Text>
          )}
          <Text size="xs" c="dimmed" mt={6}>
            Ritrovi i social scelti nel profilo: puoi usare quelli collegati. Il
            numero di post a settimana vale per ciascun social.
          </Text>
        </div>
        <Textarea
          label="Cosa vuoi raccontare ai tuoi clienti in questo periodo?"
          required
          minRows={3}
          value={descrizione}
          error={errori.descrizione}
          onChange={(e) => setDescrizione(e.currentTarget.value)}
        />
        {errore && inviati === dati && (
          <Alert color="red" variant="light">
            {errore}
          </Alert>
        )}
        <Group className={layout.azioni} justify="flex-end">
          <Button type="submit" color="verde" loading={inCorso}>
            Continua →
          </Button>
        </Group>
      </Stack>
    </Paper>
  );
}
