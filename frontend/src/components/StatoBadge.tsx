/**
 * Lo stato di una campagna o di un post: pallino del colore, etichetta e,
 * al passaggio del mouse, la spiegazione (brief-richieste §1.1).
 */
import { Badge, Box, Tooltip } from "@mantine/core";

import {
  coloreCampagna,
  colorePost,
  etichettaStato,
  POST_DA_CORREGGERE,
  spiegazioneStato,
  type Ruolo,
  type TipoStato,
} from "./stati";

export function StatoBadge({
  tipo,
  stato,
  ruolo = "operatore",
  daRivedere = false,
  size,
}: {
  tipo: TipoStato;
  stato: string;
  ruolo?: Ruolo;
  /** Solo per i post: il validatore ha dato un blocco. */
  daRivedere?: boolean;
  size?: string;
}) {
  const correggere = tipo === "post" && daRivedere && ruolo === "operatore";
  const colore = correggere
    ? "red"
    : tipo === "campagna"
    ? coloreCampagna(stato)
    : colorePost(stato);
  const etichetta = correggere
    ? POST_DA_CORREGGERE.etichetta
    : etichettaStato(tipo, stato, ruolo);
  const spiegazione = correggere
    ? POST_DA_CORREGGERE.spiegazione
    : ruolo === "operatore"
    ? spiegazioneStato(tipo, stato)
    : undefined;

  const badge = (
    <Badge
      color={colore}
      variant="light"
      size={size}
      leftSection={
        <Box
          w={6}
          h={6}
          style={{ borderRadius: "50%", background: "currentColor" }}
        />
      }
    >
      {etichetta}
    </Badge>
  );
  return spiegazione ? (
    <Tooltip label={spiegazione} multiline maw={260} withArrow>
      {badge}
    </Tooltip>
  ) : (
    badge
  );
}
