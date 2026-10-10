import { useEffect, useRef, useState } from "react";
import type { ReactNode } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import {
  Alert,
  Anchor,
  Badge,
  Button,
  Center,
  Checkbox,
  Group,
  Loader,
  MultiSelect,
  NumberInput,
  Paper,
  Progress,
  Select,
  SimpleGrid,
  Stack,
  Text,
  Textarea,
  TextInput,
  Title,
} from "@mantine/core";

import { Guscio } from "../../../components/Guscio";
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

const DESCRIZIONI_PASSI = [
  "I dati anagrafici della bottega, per intestare correttamente profilo e campagne.",
  "Il materiale grezzo con cui l'AI scriverà i testi: più è concreto, meno i post sembreranno generici.",
  "Guida il tono dei testi, gli hashtag e le linee guida per le foto.",
  "Per chi lavori e cosa vuoi ottenere attraverso i canali social.",
  "Come devono suonare i post e come ti rivolgi ai clienti.",
  "Preferenze per le campagne, post a settimana e social già utilizzati.",
  "Le foto reali alimentano ogni post: quanti scatti puoi fornire e chi fotografa.",
  "Date da tenere a mente, periodi di chiusura e orari di apertura.",
  "Controlla il profilo prima di salvarlo. Puoi tornare a ogni passo per correggerlo.",
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
    if (Object.keys(problemi).length) return;

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

  const policy = (
    campo: "quantita_mese" | "chi_scatta" | "persone",
    label: string,
  ) => (
    <Select
      label={label}
      data={SCELTE[campo]}
      clearable
      value={
        typeof dati?.foto_policy?.[campo] === "string"
          ? (dati.foto_policy[campo] as string)
          : null
      }
      onChange={(v) => {
        const p = { ...dati?.foto_policy };
        if (v) p[campo] = v;
        else delete p[campo];
        cambia("foto_policy", Object.keys(p).length ? p : null);
      }}
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
    <Guscio
      titolo="Profilo bottega"
      nav={[{ label: "Campagna" }, { label: "Profilo bottega", attivo: true }]}
    >
      <Group gap="xs" mb="sm">
        <Anchor component={Link} to="/campagna" size="sm">
          Area Bottega
        </Anchor>
        <Text size="sm" c="dimmed">
          /
        </Text>
        <Text size="sm" c="dimmed">
          Profilo bottega (passi 1–9)
        </Text>
      </Group>

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
        <Paper withBorder p={{ base: "md", sm: "xl" }} radius="md" mt="xs">
          <Group justify="space-between" align="center" mb="xs">
            <Badge color="verde" size="md">
              Passo {passo + 1} di 9
            </Badge>
            <Text size="xs" c="dimmed">
              I campi con * sono obbligatori
            </Text>
          </Group>

          <Progress
            value={((passo + 1) / 9) * 100}
            color="verde"
            size="sm"
            mb="lg"
            aria-label={`Passo ${passo + 1} di 9`}
          />

          <Title order={2} mb="xs" ref={intestazione} tabIndex={-1}>
            {PASSI[passo]}
          </Title>
          <Text c="dimmed" size="sm" mb="lg">
            {DESCRIZIONI_PASSI[passo]}
          </Text>

          <form
            onSubmit={(e) => {
              e.preventDefault();
              if (passo === 8) void salva();
              else setPasso((n) => n + 1);
            }}
            noValidate
          >
            <fieldset
              disabled={salvando}
              style={{ border: 0, padding: 0, margin: 0, minWidth: 0 }}
            >
              <Stack gap="md">
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
                    {testo("storia", "Racconta la tua storia", true)}
                    {testo("origine", "Come è nata la bottega", true)}
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
                      {scelta("cortesia", "Come rivolgersi ai clienti")}
                    </SimpleGrid>
                    {testo("vincoli", "Cose da non dire", true)}
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
                            label={v.label}
                          />
                        ))}
                      </Group>
                    </Checkbox.Group>
                    <Text c="dimmed" size="xs">
                      Sono le preferenze per le campagne. Il collegamento degli
                      account è gestito dal consorzio.
                    </Text>
                    {scelta("frequenza", "Post a settimana per ogni canale")}
                    <Text c="dimmed" size="xs">
                      La frequenza è un impegno: i post che le foto non coprono
                      saranno completati con i riempitivi.
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
                        <Checkbox value="facebook" label="Facebook" />
                        <Checkbox value="instagram" label="Instagram" />
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
                      label="Cosa funziona già sui social"
                      value={String(dati.social_esistenti?.cosa_funziona ?? "")}
                      onChange={(e) =>
                        sociale("cosa_funziona", e.currentTarget.value)
                      }
                    />
                  </>
                )}

                {passo === 6 && (
                  <>
                    <SimpleGrid cols={{ base: 1, sm: 3 }} spacing="md">
                      {policy(
                        "quantita_mese",
                        "Quante fotografie puoi fornire al mese?",
                      )}
                      {policy("chi_scatta", "Chi scatta le fotografie?")}
                      {policy("persone", "Persone riconoscibili nelle foto")}
                    </SimpleGrid>
                    <Alert color="blue" variant="light">
                      <Text size="sm">
                        Logo e archivio della bottega saranno disponibili qui
                        nel prossimo passaggio.
                      </Text>
                    </Alert>
                  </>
                )}

                {passo === 7 && (
                  <>
                    <Title order={3}>Eventi ricorrenti</Title>
                    {errori.eventi_ricorrenti && (
                      <Alert color="red">{errori.eventi_ricorrenti}</Alert>
                    )}
                    {(dati.eventi_ricorrenti ?? []).map((v, i) => (
                      <Paper key={i} withBorder p="md" radius="sm">
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

                {passo === 8 && (
                  <>
                    <Text size="sm">
                      Controlla il profilo prima di salvarlo. Puoi tornare a
                      ogni passo per correggerlo.
                    </Text>
                    {Object.keys(errori).length > 0 && (
                      <Alert color="red" title="Il profilo non è stato salvato">
                        <Stack gap="xs">
                          {Object.entries(errori).map(([k, messaggio]) => (
                            <Button
                              key={k}
                              variant="subtle"
                              color="red"
                              justify="start"
                              onClick={() => setPasso(PASSO_CAMPO[k] ?? 0)}
                            >
                              {ETICHETTE[k] ?? k}: {messaggio}
                            </Button>
                          ))}
                        </Stack>
                      </Alert>
                    )}
                    {PASSI.slice(0, 8).map((label, i) => (
                      <Paper key={label} withBorder p="md" radius="sm">
                        <Group justify="space-between" mb="xs">
                          <Title order={3}>
                            {i + 1}. {label}
                          </Title>
                          <Button
                            variant="subtle"
                            size="xs"
                            onClick={() => setPasso(i)}
                          >
                            Modifica {label.toLowerCase()}
                          </Button>
                        </Group>
                        <Riepilogo dati={dati} passo={i} />
                      </Paper>
                    ))}
                  </>
                )}

                {errore && (
                  <Alert color="red" role="alert">
                    {errore}
                  </Alert>
                )}

                <Group justify="space-between" mt="xl" pt="md">
                  <Button
                    variant="default"
                    disabled={passo === 0 || salvando}
                    onClick={() => setPasso((n) => n - 1)}
                  >
                    Indietro
                  </Button>
                  <Button type="submit" color="verde" loading={salvando}>
                    {passo === 8 ? "Salva e vai alla campagna" : "Continua"}
                  </Button>
                </Group>
              </Stack>
            </fieldset>
          </form>
        </Paper>
      )}
    </Guscio>
  );
}

function Riepilogo({ dati: p, passo }: { dati: DatiProfilo; passo: number }) {
  const etichetta = (campo: keyof typeof SCELTE, valore: string | null) =>
    SCELTE[campo].find((v) => v.value === valore)?.label ?? "Non indicato";

  let righe: [string, string | null][] = [];

  switch (passo) {
    case 0:
      righe = [
        ["Bottega", p.nome],
        ["Referente", p.referente],
        ["Città", p.citta],
        ["Anni di attività", p.anni_attivita?.toString() ?? null],
        ["Sito", p.sito],
      ];
      break;
    case 1:
      righe = [
        ["Storia", p.storia],
        ["Origine", p.origine],
      ];
      break;
    case 2:
      righe = [
        ["Tipo di prodotto", etichetta("tipo_prodotto", p.tipo_prodotto)],
        ["Prodotti", p.gamma],
        [
          "Valori",
          p.valori?.map((v) => etichetta("valori", v)).join(", ") ?? null,
        ],
        ["Fascia di prezzo", etichetta("fascia_prezzo", p.fascia_prezzo)],
        ["Stagionalità", p.stagionalita],
      ];
      break;
    case 3:
      righe = [
        ["Clienti ideali", p.clienti_ideali],
        ["Obiettivo", etichetta("obiettivo", p.obiettivo)],
        ["Zona", p.zona],
      ];
      break;
    case 4:
      righe = [
        ["Tono", p.tono?.map((v) => etichetta("tono", v)).join(", ") ?? null],
        ["Cortesia", etichetta("cortesia", p.cortesia)],
        ["Cose da non dire", p.vincoli],
      ];
      break;
    case 5:
      righe = [
        ["Canali", p.canali.map((v) => etichetta("canali", v)).join(", ")],
        ["Frequenza", etichetta("frequenza", p.frequenza)],
        [
          "Social già usati",
          Array.isArray(p.social_esistenti?.canali)
            ? p.social_esistenti.canali.join(", ")
            : null,
        ],
        [
          "Profili social",
          typeof p.social_esistenti?.profili === "string"
            ? p.social_esistenti.profili
            : null,
        ],
        [
          "Cosa funziona",
          typeof p.social_esistenti?.cosa_funziona === "string"
            ? p.social_esistenti.cosa_funziona
            : null,
        ],
      ];
      break;
    case 6:
      righe = [
        [
          "Fotografie al mese",
          etichetta(
            "quantita_mese",
            String(p.foto_policy?.quantita_mese ?? ""),
          ),
        ],
        [
          "Chi scatta",
          etichetta("chi_scatta", String(p.foto_policy?.chi_scatta ?? "")),
        ],
        ["Persone", etichetta("persone", String(p.foto_policy?.persone ?? ""))],
      ];
      break;
    case 7:
    default:
      righe = [
        [
          "Eventi",
          p.eventi_ricorrenti
            ?.map(
              (v) =>
                `${v.nome || "Nome mancante"} · ${
                  v.quando || "Data mancante"
                } · ${etichetta("tipo_evento", v.tipo)}`,
            )
            .join("; ") ?? null,
        ],
        ["Chiusure", p.chiusure],
        [
          "Orari",
          !Array.isArray(p.orari) && typeof p.orari?.nota === "string"
            ? p.orari.nota
            : null,
        ],
      ];
      break;
  }

  return (
    <Stack gap={4} mt="xs">
      {righe.map(([nome, valore]) => (
        <Text
          key={nome}
          size="sm"
          style={{ overflowWrap: "anywhere", whiteSpace: "pre-wrap" }}
        >
          <b>{nome}:</b> {valore?.trim() || "Non indicato"}
        </Text>
      ))}
    </Stack>
  );
}
