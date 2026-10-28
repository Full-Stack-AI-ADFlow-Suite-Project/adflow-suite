/**
 * Storico dell'AI (R-50): ogni chiamata all'AI con i filtri del brief-richieste
 * §1.3. Un clic su una riga apre il dettaglio.
 */
import {
  Alert,
  Badge,
  Button,
  Center,
  Group,
  Loader,
  Pagination,
  Paper,
  Select,
  SimpleGrid,
  Stack,
  Text,
  TextInput,
} from "@mantine/core";
import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import {
  elencoChiamate,
  ESITI,
  etichettaEsito,
  etichettaTipo,
  TIPI,
  type FiltriStorico,
  type PaginaChiamateAI,
} from "../../api/storico";
import { Guscio } from "../../components/Guscio";
import { dataOra } from "./campagna/util";
import { costo, durata } from "./storico-ai/formati";
import { NumeriStorico } from "./storico-ai/NumeriStorico";

export function StoricoAI() {
  const [filtri, setFiltri] = useState<FiltriStorico>({});
  const [pagina, setPagina] = useState(1);
  const [dati, setDati] = useState<PaginaChiamateAI | null>(null);
  const [errore, setErrore] = useState<string | null>(null);
  // Le scelte dei filtri nascono dalla prima pagina senza filtri.
  const [scelte, setScelte] = useState<PaginaChiamateAI | null>(null);

  useEffect(() => {
    elencoChiamate({}, 1)
      .then(setScelte)
      .catch(() => {});
  }, []);

  useEffect(() => {
    let attivo = true;
    elencoChiamate(filtri, pagina)
      .then((p) => {
        if (!attivo) return;
        setErrore(null);
        setDati(p);
      })
      .catch(
        () => attivo && setErrore("Impossibile caricare lo storico. Riprova."),
      );
    return () => {
      attivo = false;
    };
  }, [filtri, pagina]);

  const opzioni = useMemo(() => {
    const voci = scelte?.voci ?? [];
    const campagne = new Map(
      voci.map((c) => [c.campagna_id, c.campagna_titolo]),
    );
    return {
      campagne: [...campagne].map(([value, label]) => ({
        value: String(value),
        label,
      })),
      modelli: [...new Set(voci.map((c) => c.modello_ai))],
      versioni: [
        ...new Set(voci.map((c) => c.versione_prompt).filter(Boolean)),
      ] as string[],
    };
  }, [scelte]);

  const imposta = (cambio: Partial<FiltriStorico>) => {
    setPagina(1);
    setFiltri((f) => ({ ...f, ...cambio }));
  };
  const pagine = dati
    ? Math.max(1, Math.ceil(dati.totale / dati.per_pagina))
    : 1;

  return (
    <Guscio titolo="Storico AI" largo={1100}>
      <Text c="dimmed" size="sm" mb="md">
        Ogni chiamata all'AI, riuscita o no, dalla più recente. Apri una riga
        per vedere che cosa è stato chiesto e che cosa è tornato.
      </Text>

      <SimpleGrid cols={{ base: 1, sm: 2, md: 3 }} spacing="sm" mb="md">
        <Select
          label="Campagna"
          placeholder="Tutte"
          clearable
          data={opzioni.campagne}
          value={filtri.campagna_id ? String(filtri.campagna_id) : null}
          onChange={(v) => imposta({ campagna_id: v ? Number(v) : undefined })}
        />
        <Select
          label="Tipo"
          placeholder="Tutti"
          clearable
          data={TIPI}
          value={filtri.tipo ?? null}
          onChange={(v) => imposta({ tipo: v ?? undefined })}
        />
        <Select
          label="Modello"
          placeholder="Tutti"
          clearable
          data={opzioni.modelli}
          value={filtri.modello ?? null}
          onChange={(v) => imposta({ modello: v ?? undefined })}
        />
        <Select
          label="Versione del prompt"
          placeholder="Tutte"
          clearable
          data={opzioni.versioni}
          value={filtri.versione_prompt ?? null}
          onChange={(v) => imposta({ versione_prompt: v ?? undefined })}
        />
        <Select
          label="Esito"
          placeholder="Tutti"
          clearable
          data={ESITI.map((e) => ({ value: e, label: etichettaEsito(e) }))}
          value={filtri.esito ?? null}
          onChange={(v) => imposta({ esito: v ?? undefined })}
        />
        <Group grow gap="xs" align="flex-end" wrap="nowrap">
          <TextInput
            label="Dal"
            type="date"
            value={filtri.dal ?? ""}
            onChange={(e) =>
              imposta({ dal: e.currentTarget.value || undefined })
            }
          />
          <TextInput
            label="Al"
            type="date"
            value={filtri.al ?? ""}
            onChange={(e) =>
              imposta({ al: e.currentTarget.value || undefined })
            }
          />
        </Group>
      </SimpleGrid>
      {Object.values(filtri).some(Boolean) && (
        <Button
          variant="subtle"
          size="xs"
          mb="sm"
          onClick={() => {
            setPagina(1);
            setFiltri({});
          }}
        >
          Azzera i filtri
        </Button>
      )}

      <NumeriStorico filtri={filtri} />

      {errore && (
        <Alert color="red" variant="light" mb="md">
          {errore}
        </Alert>
      )}
      {!dati && !errore && (
        <Center py="xl">
          <Loader color="verde" />
        </Center>
      )}

      {dati && (
        <Stack gap="xs">
          <Text size="sm" c="dimmed">
            {dati.totale} chiamate
          </Text>
          {dati.voci.map((c) => (
            <Paper
              key={c.id}
              withBorder
              radius="md"
              p="sm"
              component={Link}
              to={`/storico-ai/${c.id}`}
              style={{ color: "inherit", textDecoration: "none" }}
            >
              <Group justify="space-between" wrap="wrap" gap="xs">
                <div style={{ minWidth: 0 }}>
                  <Group gap="xs">
                    <Text fw={600} size="sm">
                      {etichettaTipo(c.tipo)}
                    </Text>
                    <Badge
                      variant="light"
                      color={c.esito === "ok" ? "verde" : "red"}
                    >
                      {etichettaEsito(c.esito)}
                    </Badge>
                  </Group>
                  <Text size="sm" c="dimmed">
                    {dataOra(c.creata_il)} · {c.campagna_titolo}
                    {c.bottega ? ` · ${c.bottega}` : ""}
                  </Text>
                </div>
                <Group gap="md" wrap="wrap">
                  <Text size="xs" c="dimmed">
                    {c.modello_ai}
                    {c.versione_prompt ? ` · ${c.versione_prompt}` : ""}
                  </Text>
                  <Text size="xs" c="dimmed">
                    {durata(c.durata_ms)}
                  </Text>
                  <Text size="xs" c="dimmed">
                    {costo(c.costo_usd)}
                  </Text>
                </Group>
              </Group>
            </Paper>
          ))}
          {!dati.voci.length && (
            <Paper
              withBorder
              radius="md"
              p="lg"
              style={{ borderStyle: "dashed" }}
            >
              <Text c="dimmed" size="sm">
                Nessuna chiamata con questi filtri.
              </Text>
            </Paper>
          )}
          {pagine > 1 && (
            <Pagination
              mt="sm"
              total={pagine}
              value={pagina}
              onChange={setPagina}
              color="verde"
            />
          )}
        </Stack>
      )}
    </Guscio>
  );
}
