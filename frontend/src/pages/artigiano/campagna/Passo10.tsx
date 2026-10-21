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
import { IconaCanale } from "../../../components/IconaCanale";
import stile from "./Passo10.module.css";

const NOMI_CANALI: Record<string, string> = {
  facebook: "Facebook",
  instagram: "Instagram",
};

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
  const numeroCanaliCollegati = canali.filter((c) => c.collegato).length;

  const scegliDurata = (giorni: number) => {
    const d = new Date(inizio + "T00:00:00");
    d.setDate(d.getDate() + giorni - 1);
    setFine(d.toISOString().slice(0, 10));
  };

  const valida = (): boolean => {
    const e: Record<string, string> = {};
    if (!titolo.trim()) e.titolo = "Il nome non può essere vuoto.";
    if (giorniTra(dataISO(0), inizio) < 4)
      e.inizio = "L'inizio deve cadere almeno 3 giorni dopo oggi.";
    if (durata < 7) e.fine = "La campagna dura almeno 7 giorni.";
    if (durata > 92) e.fine = "La campagna dura al massimo 3 mesi.";
    const collegati = canali.filter((c) => c.collegato).map((c) => c.canale);
    if (!scelti.length) e.canali = "Scegli almeno un canale.";
    else if (!scelti.every((c) => collegati.includes(c)))
      e.canali = "Un canale scelto non è collegato: contatta il consorzio.";
    if (!descrizione.trim())
      e.descrizione = "La descrizione non può essere vuota.";
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
      radius="lg"
      p={{ base: "md", sm: "xl" }}
      component="form"
      onSubmit={invia}
      className={stile.form}
    >
      <header className={stile.intestazione}>
        <Text className={stile.sopratitolo}>
          Nuova campagna · Passaggio 1 di 3
        </Text>
        <Title order={2} className={stile.titolo}>
          Configurazione della campagna
        </Title>
        <Text className={stile.descrizione}>
          Imposta il periodo di programmazione, i canali attivi e le indicazioni
          editoriali per la redazione dei post.
        </Text>
        <div className={stile.avanzamento} aria-label="Passaggio 1 di 3">
          <span />
          <span />
          <span />
        </div>
      </header>

      <Stack gap="lg" className={stile.campi}>
        <TextInput
          label="Nome della campagna"
          required
          value={titolo}
          error={errori.titolo}
          onChange={(e) => setTitolo(e.currentTarget.value)}
          placeholder="Campagna Ottobre 2026"
        />
        <section className={stile.sezione}>
          <Text className={stile.titoloSezione}>Periodo della campagna</Text>
          <SimpleGrid cols={{ base: 1, sm: 2 }} mt="sm">
            <TextInput
              label="Inizio"
              type="date"
              required
              min={dataISO(3)}
              value={inizio}
              error={errori.inizio}
              onChange={(e) => setInizio(e.currentTarget.value)}
            />
            <TextInput
              label="Fine"
              type="date"
              required
              min={inizio}
              value={fine}
              error={errori.fine}
              onChange={(e) => setFine(e.currentTarget.value)}
            />
          </SimpleGrid>
          <Text className={stile.aiuto}>
            Inizio tra almeno 3 giorni; durata da 7 giorni a 3 mesi, per dare al
            consorzio il tempo di approvare i post.
          </Text>
          <div className={stile.durate}>
            <Text className={stile.etichetta}>Durata rapida</Text>
            <Group gap="xs">
              <Chip
                checked={durata === 14}
                onChange={() => scegliDurata(14)}
                color="verde"
              >
                2 settimane
              </Chip>
              <Chip
                checked={durata >= 28 && durata <= 31}
                onChange={() => scegliDurata(31)}
                color="verde"
              >
                1 mese
              </Chip>
              <Chip
                checked={durata >= 59 && durata <= 62}
                onChange={() => scegliDurata(61)}
                color="verde"
              >
                2 mesi
              </Chip>
            </Group>
          </div>
        </section>
        <section className={stile.sezione}>
          <Group justify="space-between" align="center">
            <Text className={stile.titoloSezione}>
              Canali di questa campagna *
            </Text>
            <Text size="xs" c="dimmed">
              {numeroCanaliCollegati} collegati
            </Text>
          </Group>
          <div className={stile.canali}>
            {canali.map((c) =>
              c.collegato ? (
                <Checkbox
                  key={c.canale}
                  label={
                    <span className={stile.etichettaCanale}>
                      <IconaCanale canale={c.canale} />
                      <span>{NOMI_CANALI[c.canale] ?? c.canale}</span>
                    </span>
                  }
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
                    label={
                      <span className={stile.etichettaCanale}>
                        <IconaCanale canale={c.canale} />
                        <span>
                          {NOMI_CANALI[c.canale] ?? c.canale} non è collegato
                        </span>
                      </span>
                    }
                    disabled
                  />
                </Tooltip>
              ),
            )}
          </div>
          {errori.canali && (
            <Text size="xs" c="red" mt={4}>
              {errori.canali}
            </Text>
          )}
          <Text className={stile.aiuto}>
            Puoi selezionare solo i canali collegati al profilo. La frequenza
            impostata vale per ciascun canale.
          </Text>
        </section>
        <Textarea
          label="Descrizione e commenti della campagna"
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
        <Group justify="flex-end" className={stile.azioni}>
          <Button
            type="submit"
            color="verde"
            loading={inCorso}
            className={stile.continua}
          >
            Continua →
          </Button>
        </Group>
      </Stack>
    </Paper>
  );
}
