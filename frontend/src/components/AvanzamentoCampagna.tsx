/**
 * Barra di avanzamento della campagna (brief-richieste §1.1, T3-915).
 * Mostra i 5 passi: Inviata → Preparazione → Revisione → Pubblicazione → Conclusa.
 * inviata accende il passo 1, in_generazione il 2, in_revisione il 3, attiva il 4, conclusa il 5.
 * generazione_fallita mostra il passo 2 in errore; sospesa il passo 4 in pausa;
 * respinta, scaduta, annullata fermano la barra al passo raggiunto, con l'etichetta di components/stati.ts.
 * A 375 px resta leggibile mostrando il passo corrente con «3 di 5».
 */
import { Badge, Box, Flex, Group, Progress, Stack, Text } from "@mantine/core";
import { etichettaStato } from "./stati";

export interface AvanzamentoCampagnaProps {
  stato: string;
}

interface PassoInfo {
  numero: number;
  nome: string;
}

const PASSI: PassoInfo[] = [
  { numero: 1, nome: "Inviata" },
  { numero: 2, nome: "Preparazione" },
  { numero: 3, nome: "Revisione" },
  { numero: 4, nome: "Pubblicazione" },
  { numero: 5, nome: "Conclusa" },
];

function calcolaAvanzamento(stato: string): {
  passoAttivo: number;
  tipo: "normale" | "errore" | "pausa" | "fermato";
  etichetta?: string;
} {
  switch (stato) {
    case "inviata":
      return { passoAttivo: 1, tipo: "normale" };
    case "in_generazione":
      return { passoAttivo: 2, tipo: "normale" };
    case "generazione_fallita":
      return {
        passoAttivo: 2,
        tipo: "errore",
        etichetta: etichettaStato("campagna", stato),
      };
    case "in_revisione":
    case "piano_da_rivedere":
      return { passoAttivo: 3, tipo: "normale" };
    case "respinta":
      return {
        passoAttivo: 3,
        tipo: "fermato",
        etichetta: etichettaStato("campagna", stato),
      };
    case "scaduta":
      return {
        passoAttivo: 3,
        tipo: "fermato",
        etichetta: etichettaStato("campagna", stato),
      };
    case "attiva":
      return { passoAttivo: 4, tipo: "normale" };
    case "sospesa":
      return {
        passoAttivo: 4,
        tipo: "pausa",
        etichetta: etichettaStato("campagna", stato),
      };
    case "annullata":
      return {
        passoAttivo: 4,
        tipo: "fermato",
        etichetta: etichettaStato("campagna", stato),
      };
    case "conclusa":
      return { passoAttivo: 5, tipo: "normale" };
    case "bozza":
    default:
      return { passoAttivo: 1, tipo: "normale" };
  }
}

export function AvanzamentoCampagna({ stato }: AvanzamentoCampagnaProps) {
  const { passoAttivo, tipo, etichetta } = calcolaAvanzamento(stato);

  const getColorePunto = (n: number) => {
    if (n < passoAttivo) return "var(--mantine-color-verde-6)";
    if (n === passoAttivo) {
      if (tipo === "errore" || tipo === "fermato")
        return "var(--mantine-color-red-6)";
      if (tipo === "pausa") return "var(--mantine-color-yellow-6)";
      return "var(--mantine-color-verde-6)";
    }
    return "var(--mantine-color-gray-4)";
  };

  const getSfondoPunto = (n: number) => {
    if (n < passoAttivo) return "var(--mantine-color-verde-6)";
    if (n === passoAttivo) {
      if (tipo === "errore" || tipo === "fermato")
        return "var(--mantine-color-red-6)";
      if (tipo === "pausa") return "var(--mantine-color-yellow-6)";
      if (stato === "conclusa") return "var(--mantine-color-verde-6)";
      return "var(--mantine-color-verde-6)";
    }
    return "var(--mantine-color-default-hover)";
  };

  const getIconaPunto = (n: number) => {
    if (n < passoAttivo || (n === 5 && stato === "conclusa")) return "✓";
    if (n === passoAttivo) {
      if (tipo === "errore") return "!";
      if (tipo === "pausa") return "⏸";
      if (tipo === "fermato") return "✕";
    }
    return String(n);
  };

  const getEtichettaPasso = (p: PassoInfo) => {
    if (p.numero === passoAttivo && etichetta) {
      return etichetta;
    }
    return p.nome;
  };

  const getColoreMobile = () => {
    if (tipo === "errore" || tipo === "fermato") return "red";
    if (tipo === "pausa") return "yellow";
    return "verde";
  };

  const nomePassoMobile =
    passoAttivo === 5 && stato === "conclusa"
      ? "Conclusa"
      : etichetta ?? PASSI[passoAttivo - 1]?.nome;

  return (
    <Box
      p="sm"
      style={{
        backgroundColor: "var(--mantine-color-body)",
        borderRadius: 8,
        border: "1px solid var(--mantine-color-default-border)",
      }}
    >
      {/* Vista mobile (<= 375px e piccoli schermi): compatta con «X di 5» */}
      <Box hiddenFrom="sm">
        <Group justify="space-between" align="center" mb={6}>
          <Text size="xs" fw={700} c="dimmed">
            {passoAttivo} di 5
          </Text>
          <Badge size="sm" color={getColoreMobile()} variant="light">
            {nomePassoMobile}
          </Badge>
        </Group>
        <Progress
          value={(passoAttivo / 5) * 100}
          color={getColoreMobile()}
          size="sm"
          radius="xl"
        />
      </Box>

      {/* Vista desktop: tutti i 5 passi con linea di avanzamento */}
      <Box visibleFrom="sm">
        <Flex align="center" justify="space-between" gap="xs">
          {PASSI.map((passo, idx) => {
            const isCorrente = passo.numero === passoAttivo;
            const isPassato = passo.numero < passoAttivo;
            const testo = getEtichettaPasso(passo);
            const colore = getColorePunto(passo.numero);

            return (
              <Flex
                key={passo.numero}
                align="center"
                style={{ flex: idx < PASSI.length - 1 ? 1 : "0 0 auto" }}
              >
                <Group gap={8} wrap="nowrap" align="center">
                  <Box
                    style={{
                      width: 26,
                      height: 26,
                      borderRadius: "50%",
                      backgroundColor: getSfondoPunto(passo.numero),
                      color:
                        isPassato ||
                        isCorrente ||
                        (passo.numero === 5 && stato === "conclusa")
                          ? "#fff"
                          : "var(--mantine-color-dimmed)",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      fontWeight: 700,
                      fontSize: 12,
                      border: `2px solid ${colore}`,
                      flexShrink: 0,
                    }}
                  >
                    {getIconaPunto(passo.numero)}
                  </Box>
                  <Stack gap={0}>
                    <Text
                      size="xs"
                      fw={isCorrente ? 700 : isPassato ? 600 : 500}
                      c={
                        isCorrente
                          ? tipo === "errore" || tipo === "fermato"
                            ? "red"
                            : tipo === "pausa"
                            ? "yellow.8"
                            : "verde"
                          : isPassato
                          ? undefined
                          : "dimmed"
                      }
                      style={{ whiteSpace: "nowrap" }}
                    >
                      {testo}
                    </Text>
                  </Stack>
                </Group>

                {idx < PASSI.length - 1 && (
                  <Box
                    mx="xs"
                    style={{
                      flex: 1,
                      height: 2,
                      backgroundColor:
                        passo.numero < passoAttivo
                          ? "var(--mantine-color-verde-6)"
                          : "var(--mantine-color-gray-3)",
                      minWidth: 16,
                    }}
                  />
                )}
              </Flex>
            );
          })}
        </Flex>
      </Box>
    </Box>
  );
}
