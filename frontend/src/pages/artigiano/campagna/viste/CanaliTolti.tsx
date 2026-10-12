/**
 * Il canale tolto dal consorzio (spec §4): la vista lo dice, con la nota
 * dell'operatore. Le altre note interne l'artigiano non le vede mai: qui si
 * leggono solo le decisioni `canale_tolto`.
 */
import { Alert } from "@mantine/core";

import type { CampagnaDettaglio } from "../../../../api/campagne";

const NOME_CANALE: Record<string, string> = {
  facebook: "Facebook",
  instagram: "Instagram",
};

export function CanaliTolti({ campagna }: { campagna: CampagnaDettaglio }) {
  const tolti = campagna.canali_tolti ?? [];
  if (tolti.length === 0) return null;
  const note = (campagna.decisioni ?? []).filter(
    (d) => d.esito === "canale_tolto",
  );
  return (
    <>
      {tolti.map((canale) => {
        const nota = note.find((d) => d.canale === canale)?.nota;
        return (
          <Alert key={canale} color="orange" variant="light" mb="md">
            <b>{NOME_CANALE[canale] ?? canale} è stato tolto dalla campagna.</b>{" "}
            Su questo canale non esce nessun post.
            {nota && <> Nota del consorzio: "{nota}"</>}
          </Alert>
        );
      })}
    </>
  );
}
