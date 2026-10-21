/**
 * Il profilo della bottega in sola lettura, diviso come i passi 1–8 della
 * pagina Profilo dell'artigiano (spec R-38). Il passo 9 è il riepilogo del
 * form e non ha campi. Etichette e scelte sono quelle di `api/artigiani.ts`.
 */
import { Card, SimpleGrid, Stack, Text } from "@mantine/core";

import { PASSI, SCELTE, type ProfiloPubblico } from "../../../api/artigiani";

type Righe = [string, string | null | undefined][];

const scelta = (campo: keyof typeof SCELTE, valore: string | null) =>
  SCELTE[campo].find((v) => v.value === valore)?.label ?? null;

const elenco = (campo: keyof typeof SCELTE, valori: string[] | null) =>
  valori?.map((v) => scelta(campo, v) ?? v).join(", ") || null;

const testo = (v: unknown): string | null =>
  typeof v === "string" && v.trim() ? v : null;

/** Le righe «etichetta: valore» di ogni passo, nell'ordine del form. */
function passi(p: ProfiloPubblico): Righe[] {
  const foto = p.foto_policy ?? {};
  const social = p.social_esistenti ?? {};
  return [
    [
      ["Bottega", p.nome],
      ["Referente", p.referente],
      ["Città", p.citta],
      ["Anni di attività", p.anni_attivita?.toString()],
      ["Sito", p.sito],
    ],
    [
      ["Storia", p.storia],
      ["Origine", p.origine],
    ],
    [
      ["Tipo di prodotto", scelta("tipo_prodotto", p.tipo_prodotto)],
      ["Prodotti", p.gamma],
      ["Valori", elenco("valori", p.valori)],
      ["Fascia di prezzo", scelta("fascia_prezzo", p.fascia_prezzo)],
      ["Stagionalità", p.stagionalita],
    ],
    [
      ["Clienti ideali", p.clienti_ideali],
      ["Obiettivo", scelta("obiettivo", p.obiettivo)],
      ["Zona", p.zona],
    ],
    [
      ["Tono", elenco("tono", p.tono)],
      ["Cortesia", scelta("cortesia", p.cortesia)],
      ["Cose da non dire", p.vincoli],
    ],
    [
      ["Canali preferiti", elenco("canali", p.canali)],
      ["Frequenza", scelta("frequenza", p.frequenza)],
      [
        "Social già usati",
        Array.isArray(social.canali) ? social.canali.join(", ") : null,
      ],
      ["Profili social", testo(social.profili)],
      ["Cosa funziona", testo(social.cosa_funziona)],
    ],
    [
      [
        "Fotografie al mese",
        scelta("quantita_mese", testo(foto.quantita_mese)),
      ],
      ["Chi scatta", scelta("chi_scatta", testo(foto.chi_scatta))],
      ["Persone", scelta("persone", testo(foto.persone))],
    ],
    [
      [
        "Eventi",
        p.eventi_ricorrenti
          ?.map(
            (e) =>
              `${e.nome} · ${e.quando} · ${
                scelta("tipo_evento", e.tipo) ?? e.tipo
              }`,
          )
          .join("; "),
      ],
      ["Chiusure", p.chiusure],
      ["Orari", !Array.isArray(p.orari) ? testo(p.orari?.nota) : null],
    ],
  ];
}

export function ProfiloInSolaLettura({
  profilo,
}: {
  profilo: ProfiloPubblico;
}) {
  return (
    <SimpleGrid cols={{ base: 1, md: 2 }} spacing="md">
      {passi(profilo).map((righe, i) => (
        <Card key={i} withBorder radius="md" p="md">
          <Text fw={600} mb="xs">
            {i + 1} · {PASSI[i]}
          </Text>
          <Stack gap={6}>
            {righe.map(([etichetta, valore]) => (
              <div key={etichetta}>
                <Text size="xs" c="dimmed">
                  {etichetta}
                </Text>
                <Text size="sm" style={{ overflowWrap: "anywhere" }}>
                  {valore?.trim() || "Non indicato"}
                </Text>
              </div>
            ))}
          </Stack>
        </Card>
      ))}
    </SimpleGrid>
  );
}
