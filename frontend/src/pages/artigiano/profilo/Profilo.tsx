import { useEffect, useRef, useState } from "react";
import type { ReactNode } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import {
  Alert,
  Button,
  Center,
  Checkbox,
  Group,
  Loader,
  MultiSelect,
  NumberInput,
  Paper,
  Select,
  SimpleGrid,
  Stack,
  Text,
  Textarea,
  TextInput,
  Title,
} from "@mantine/core";

import { Guscio } from "../../../components/Guscio";
import { EtichettaCanale } from "../../../components/IconaCanale";
import { useAuth } from "../../../contesto-auth";
import {
  datiScrittura,
  erroriProfilo,
  ETICHETTE,
  leggiProfilo,
  PASSI,
  PASSO_CAMPO,
  profiloVuoto,
  salvaProfilo,
  SCELTE,
  type DatiProfilo,
} from "../../../api/artigiani";
import { Passo7 } from "./passo7";
import stile from "./Profilo.module.css";

const PASSI_MODULO = PASSI.slice(0, 8);

const DESCRIZIONI_PASSI = [
  "Dati identificativi dell'attività, utilizzati per intestare il profilo e le campagne.",
  "Elementi distintivi e storia dell'impresa per contestualizzare i contenuti editoriali.",
  "Specializzazione produttiva, valori aziendali e posizionamento sul mercato.",
  "Target di riferimento e obiettivi principali della presenza sui canali social.",
  "Registro comunicativo, tono di voce ed eventuali indicazioni da escludere.",
  "Canali di pubblicazione, frequenza settimanale e presidi social già attivi.",
  "Disponibilità di materiale fotografico e modalità di produzione degli scatti.",
  "Ricorrenze commerciali, periodi di chiusura e orari di apertura al pubblico.",
];

/** Guard di /campagna: un profilo assente porta al passo 1, gli altri errori si mostrano. */
export function RichiedeProfilo({ children }: { children: ReactNode }) {
  const { utente } = useAuth();
  const [esito, setEsito] = useState<"attesa" | "presente" | "assente">(
    "attesa",
  );
  const [errore, setErrore] = useState("");
  const [tentativo, setTentativo] = useState(0);

  useEffect(() => {
    let attivo = true;
    leggiProfilo()
      .then((p) => {
        if (attivo) {
          setErrore("");
          setEsito(p ? "presente" : "assente");
        }
      })
      .catch(() => {
        if (attivo) setErrore("Non riesco a leggere il profilo. Riprova.");
      });
    return () => {
      attivo = false;
    };
  }, [utente?.id, tentativo]);

  if (errore) {
    return (
      <Guscio titolo="Profilo bottega">
        <Alert color="red">{errore}</Alert>
        <Button mt="md" onClick={() => setTentativo((n) => n + 1)}>
          Riprova
        </Button>
      </Guscio>
    );
  }
  if (esito === "attesa") {
    return (
      <Center py="xl">
        <Loader aria-label="Caricamento profilo" />
      </Center>
    );
  }
  if (esito === "assente") {
    return <Navigate to="/profilo" replace />;
  }
  return children;
}

export function Profilo() {
  const naviga = useNavigate();
  const { utente } = useAuth();
  const [dati, setDati] = useState<DatiProfilo | null>(null);
  const [passo, setPasso] = useState(0);
  const [errori, setErrori] = useState<Record<string, string>>({});
  const [errore, setErrore] = useState("");
  const [tentativo, setTentativo] = useState(0);
  const [salvando, setSalvando] = useState(false);
  const bloccoSalvataggio = useRef(false);
  const intestazione = useRef<HTMLHeadingElement>(null);

  useEffect(() => {
    let attivo = true;
    leggiProfilo()
      .then((p) => {
        if (attivo) {
          setDati(p ? datiScrittura(p) : profiloVuoto());
          setErrore("");
        }
      })
      .catch(() => {
        if (attivo) setErrore("Non riesco a leggere il profilo. Riprova.");
      });
    return () => {
      attivo = false;
    };
  }, [utente?.id, tentativo]);

  useEffect(() => {
    intestazione.current?.focus();
  }, [passo]);

  const cambia = <K extends keyof DatiProfilo>(
    campo: K,
    valore: DatiProfilo[K],
  ) => {
    setDati((p) => (p ? { ...p, [campo]: valore } : p));
    setErrori((e) => {
      const copia = { ...e };
      delete copia[campo];
      return copia;
    });
    setErrore("");
  };

  const salva = async () => {
    if (!dati || bloccoSalvataggio.current) return;
    const problemi = erroriProfilo(dati);
    setErrori(problemi);
    const primoCampoErrato = Object.keys(problemi)[0];
    if (primoCampoErrato) {
      setPasso(PASSO_CAMPO[primoCampoErrato] ?? 0);
      return;
    }

    bloccoSalvataggio.current = true;
    setSalvando(true);
    setErrore("");
    try {
      await salvaProfilo(dati);
      naviga("/campagna", { replace: true });
    } catch (e) {
      setErrore(
        e instanceof Error
          ? e.message
          : "Il profilo non è stato salvato. Riprova.",
      );
    } finally {
      bloccoSalvataggio.current = false;
      setSalvando(false);
    }
  };

  const testo = (
    campo: keyof DatiProfilo,
    label: string,
    lungo = false,
    required = false,
  ) => {
    const Componente = lungo ? Textarea : TextInput;
    return (
      <Componente
        label={label}
        required={required}
        value={typeof dati?.[campo] === "string" ? (dati[campo] as string) : ""}
        error={errori[campo]}
        onChange={(e) => cambia(campo, e.currentTarget.value)}
      />
    );
  };

  const scelta = (
    campo:
      | "tipo_prodotto"
      | "obiettivo"
      | "fascia_prezzo"
      | "cortesia"
      | "frequenza",
    label: string,
    required = false,
  ) => (
    <Select
      label={label}
      required={required}
      data={SCELTE[campo]}
      value={dati?.[campo] || null}
      error={errori[campo]}
      clearable={!required}
      onChange={(v) => cambia(campo, required ? v ?? "" : v)}
    />
  );

  const sociale = (campo: string, valore: string | string[]) =>
    cambia("social_esistenti", { ...dati?.social_esistenti, [campo]: valore });

  const evento = (
    i: number,
    campo: "nome" | "quando" | "tipo",
    valore: string,
  ) =>
    cambia(
      "eventi_ricorrenti",
      (dati?.eventi_ricorrenti ?? []).map((v, n) =>
        n === i ? { ...v, [campo]: valore } : v,
      ),
    );

  return (
    <Guscio titolo="Profilo bottega">
      {dati === null ? (
        errore ? (
          <Stack mt="md">
            <Alert color="red">{errore}</Alert>
            <Button onClick={() => setTentativo((n) => n + 1)}>Riprova</Button>
          </Stack>
        ) : (
          <Center py="xl">
            <Loader aria-label="Caricamento profilo" />
          </Center>
        )
      ) : (
        <div className={stile.layout}>
          <aside className={stile.indice} aria-label="Passi del profilo">
            <div className={stile.indiceTitolo}>Configurazione · 8 passi</div>
            <div className={stile.indiceLista}>
              {PASSI_MODULO.map((label, indice) => {
                const attivo = indice === passo;
                const completato = indice < passo;
                const classi = [
                  stile.vocePasso,
                  attivo ? stile.vocePassoAttiva : "",
                  completato ? stile.vocePassoCompletata : "",
                ]
                  .filter(Boolean)
                  .join(" ");
                return (
                  <button
                    key={label}
                    type="button"
                    className={classi}
                    onClick={() => setPasso(indice)}
                  >
                    <span className={stile.voceNumero}>
                      {completato ? "✓" : indice + 1}
                    </span>
                    <span>{label}</span>
                  </button>
                );
              })}
            </div>
          </aside>

          <Paper
            p={{ base: "md", sm: "xl" }}
            radius="lg"
            className={stile.wizard}
          >
            <div className={stile.intestazione}>
              <div>
                <Text className={stile.sopratitolo}>
                  Profilo bottega · passo {passo + 1} di 8
                </Text>
                <Title
                  order={2}
                  className={stile.titoloPasso}
                  ref={intestazione}
                  tabIndex={-1}
                >
                  {PASSI_MODULO[passo]}
                </Title>
                <Text className={stile.descrizione}>
                  {DESCRIZIONI_PASSI[passo]}
                </Text>
              </div>
              <div
                className={stile.segmenti}
                role="progressbar"
                aria-valuemin={1}
                aria-valuemax={8}
                aria-valuenow={passo + 1}
                aria-label={`Passo ${passo + 1} di 8`}
              >
                {PASSI_MODULO.map((_, indice) => (
                  <span
                    key={indice}
                    className={
                      indice <= passo
                        ? `${stile.segmento} ${stile.segmentoCompletato}`
                        : stile.segmento
                    }
                  />
                ))}
              </div>
            </div>

            <form
              onSubmit={(e) => {
                e.preventDefault();
                if (passo === 7) void salva();
                else setPasso((n) => n + 1);
              }}
              noValidate
            >
              <fieldset
                disabled={salvando}
                style={{ border: 0, padding: 0, margin: 0, minWidth: 0 }}
              >
                <Stack gap="lg" className={stile.campi}>
                  {passo === 0 && (
                    <>
                      <SimpleGrid cols={{ base: 1, sm: 2 }} spacing="md">
                        {testo("nome", "Nome della bottega", false, true)}
                        {testo("referente", "Referente", false, true)}
                      </SimpleGrid>
                      <SimpleGrid cols={{ base: 1, sm: 2 }} spacing="md">
                        {testo("citta", "Città", false, true)}
                        <NumberInput
                          label="Anni di attività"
                          min={0}
                          max={2147483647}
                          allowDecimal={false}
                          value={dati.anni_attivita ?? ""}
                          error={errori.anni_attivita}
                          onChange={(v) =>
                            cambia("anni_attivita", v === "" ? null : Number(v))
                          }
                        />
                      </SimpleGrid>
                      {testo("sito", "Sito web")}
                    </>
                  )}

                  {passo === 1 && (
                    <>
                      {testo("storia", "Storia e profilo dell'attività", true)}
                      {testo(
                        "origine",
                        "Origini e tradizione del laboratorio",
                        true,
                      )}
                    </>
                  )}

                  {passo === 2 && (
                    <>
                      <SimpleGrid cols={{ base: 1, sm: 2 }} spacing="md">
                        {scelta("tipo_prodotto", "Tipo di prodotto", true)}
                        {scelta("fascia_prezzo", "Fascia di prezzo")}
                      </SimpleGrid>
                      {testo("gamma", "Prodotti e lavorazioni", true)}
                      <MultiSelect
                        label="Valori della bottega"
                        data={SCELTE.valori}
                        value={dati.valori ?? []}
                        onChange={(v) => cambia("valori", v)}
                        clearable
                      />
                      {testo("stagionalita", "Stagionalità", true)}
                    </>
                  )}

                  {passo === 3 && (
                    <>
                      {testo("clienti_ideali", "Clienti ideali", true, true)}
                      <SimpleGrid cols={{ base: 1, sm: 2 }} spacing="md">
                        {scelta("obiettivo", "Obiettivo", true)}
                        {testo("zona", "Zona dei tuoi clienti")}
                      </SimpleGrid>
                    </>
                  )}

                  {passo === 4 && (
                    <>
                      <SimpleGrid cols={{ base: 1, sm: 2 }} spacing="md">
                        <MultiSelect
                          label="Tono della comunicazione"
                          data={SCELTE.tono}
                          value={dati.tono ?? []}
                          onChange={(v) => cambia("tono", v)}
                          clearable
                        />
                        {scelta("cortesia", "Formula di cortesia")}
                      </SimpleGrid>
                      {testo(
                        "vincoli",
                        "Argomenti o espressioni da evitare",
                        true,
                      )}
                    </>
                  )}

                  {passo === 5 && (
                    <>
                      <Checkbox.Group
                        label="Canali preferiti"
                        required
                        value={dati.canali}
                        error={errori.canali}
                        onChange={(v) => cambia("canali", v)}
                      >
                        <Group mt="xs">
                          {SCELTE.canali.map((v) => (
                            <Checkbox
                              key={v.value}
                              value={v.value}
                              label={
                                <EtichettaCanale
                                  canale={v.value}
                                  testo={v.label}
                                />
                              }
                            />
                          ))}
                        </Group>
                      </Checkbox.Group>
                      <Text c="dimmed" size="xs">
                        Sono le preferenze per le campagne. Il collegamento
                        degli account è gestito dal consorzio.
                      </Text>
                      {scelta("frequenza", "Post a settimana per ogni canale")}
                      <Text c="dimmed" size="xs">
                        La frequenza è un impegno: i post che le foto non
                        coprono avranno un'immagine creata con l'AI.
                      </Text>
                      <Checkbox.Group
                        label="Social già usati"
                        value={
                          Array.isArray(dati.social_esistenti?.canali)
                            ? dati.social_esistenti.canali.filter(
                                (v): v is string => typeof v === "string",
                              )
                            : []
                        }
                        onChange={(v) => {
                          const precedente = dati.social_esistenti?.canali;
                          const primaNessuno =
                            Array.isArray(precedente) &&
                            precedente.includes("nessuno");
                          sociale(
                            "canali",
                            v.includes("nessuno") && !primaNessuno
                              ? ["nessuno"]
                              : v.filter((c) => c !== "nessuno"),
                          );
                        }}
                      >
                        <Group mt="xs">
                          <Checkbox
                            value="facebook"
                            label={<EtichettaCanale canale="facebook" />}
                          />
                          <Checkbox
                            value="instagram"
                            label={<EtichettaCanale canale="instagram" />}
                          />
                          <Checkbox value="nessuno" label="Nessuno" />
                        </Group>
                      </Checkbox.Group>
                      <TextInput
                        label="Pagine e profili social"
                        value={String(dati.social_esistenti?.profili ?? "")}
                        onChange={(e) =>
                          sociale("profili", e.currentTarget.value)
                        }
                      />
                      <Textarea
                        label="Contenuti con maggiore riscontro"
                        value={String(
                          dati.social_esistenti?.cosa_funziona ?? "",
                        )}
                        onChange={(e) =>
                          sociale("cosa_funziona", e.currentTarget.value)
                        }
                      />
                    </>
                  )}

                  {passo === 6 && (
                    <Passo7 dati={dati} cambia={cambia} scelte={SCELTE} />
                  )}

                  {passo === 7 && (
                    <>
                      <Title order={3}>Eventi ricorrenti</Title>
                      {errori.eventi_ricorrenti && (
                        <Alert color="red">{errori.eventi_ricorrenti}</Alert>
                      )}
                      {(dati.eventi_ricorrenti ?? []).map((v, i) => (
                        <Paper key={i} p="md" className={stile.evento}>
                          <Stack gap="xs">
                            <SimpleGrid cols={{ base: 1, sm: 2 }} spacing="md">
                              <TextInput
                                label={`Nome evento ${i + 1}`}
                                value={v.nome}
                                onChange={(e) =>
                                  evento(i, "nome", e.currentTarget.value)
                                }
                              />
                              <TextInput
                                label={`Quando si svolge l'evento ${i + 1}`}
                                value={v.quando}
                                onChange={(e) =>
                                  evento(i, "quando", e.currentTarget.value)
                                }
                              />
                            </SimpleGrid>
                            <Select
                              label={`Tipo evento ${i + 1}`}
                              data={SCELTE.tipo_evento}
                              value={v.tipo || null}
                              onChange={(s) => evento(i, "tipo", s ?? "")}
                            />
                            <Group justify="flex-end">
                              <Button
                                variant="subtle"
                                color="red"
                                size="xs"
                                onClick={() =>
                                  cambia(
                                    "eventi_ricorrenti",
                                    dati.eventi_ricorrenti?.filter(
                                      (_, n) => n !== i,
                                    ) ?? null,
                                  )
                                }
                              >
                                Rimuovi evento {i + 1}
                              </Button>
                            </Group>
                          </Stack>
                        </Paper>
                      ))}
                      <Button
                        variant="default"
                        onClick={() =>
                          cambia("eventi_ricorrenti", [
                            ...(dati.eventi_ricorrenti ?? []),
                            { nome: "", quando: "", tipo: "" },
                          ])
                        }
                      >
                        Aggiungi evento
                      </Button>
                      {testo("chiusure", "Periodi di chiusura", true)}
                      <Textarea
                        label="Orari e disponibilità"
                        value={
                          !Array.isArray(dati.orari) &&
                          typeof dati.orari?.nota === "string"
                            ? dati.orari.nota
                            : ""
                        }
                        onChange={(e) =>
                          cambia("orari", {
                            ...dati.orari,
                            nota: e.currentTarget.value,
                          })
                        }
                      />
                    </>
                  )}

                  {Object.keys(errori).length > 0 && (
                    <Alert color="red" title="Controlla i campi obbligatori">
                      <Stack gap={4}>
                        {Object.entries(errori).map(([k, messaggio]) => (
                          <Button
                            key={k}
                            variant="subtle"
                            color="red"
                            size="xs"
                            justify="start"
                            onClick={() => setPasso(PASSO_CAMPO[k] ?? 0)}
                          >
                            {ETICHETTE[k] ?? k}: {messaggio}
                          </Button>
                        ))}
                      </Stack>
                    </Alert>
                  )}

                  {errore && (
                    <Alert color="red" role="alert">
                      {errore}
                    </Alert>
                  )}

                  <Group
                    justify="space-between"
                    mt="xl"
                    className={stile.azioni}
                  >
                    {passo > 0 ? (
                      <Button
                        variant="default"
                        disabled={salvando}
                        onClick={() => setPasso((n) => n - 1)}
                      >
                        Indietro
                      </Button>
                    ) : (
                      <span />
                    )}
                    <Button type="submit" color="verde" loading={salvando}>
                      {passo === 7 ? "Salva e vai alla campagna" : "Continua"}
                    </Button>
                  </Group>
                </Stack>
              </fieldset>
            </form>
          </Paper>
        </div>
      )}
    </Guscio>
  );
}
