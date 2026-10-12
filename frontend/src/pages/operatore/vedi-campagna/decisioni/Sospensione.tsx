/**
 * Sospendi, riattiva e annulla (R-33). Ognuna ha la sua conferma: sospendere
 * ferma le uscite, riattivare chiede cosa fare dei post in arretrato, annullare
 * chiude la campagna per sempre.
 */
import {
  Alert,
  Button,
  Checkbox,
  Group,
  Modal,
  Stack,
  Text,
} from "@mantine/core";
import { useState } from "react";

import { annulla, riattiva, sospendi } from "../../../../api/decisioni";
import { dataOra, NOME_CANALE } from "../../campagna/util";
import { useInvio } from "./useInvio";

export interface PostInArretrato {
  postId: number;
  uscita: number;
  canale: string;
  dataOra: string;
}

function Azioni({
  occupato,
  errore,
  chiudi,
  conferma,
  testo,
  colore = "verde",
}: {
  occupato: boolean;
  errore: string | null;
  chiudi: () => void;
  conferma: () => void;
  testo: string;
  colore?: string;
}) {
  return (
    <>
      {errore && (
        <Alert color="red" variant="light" py="xs">
          {errore}
        </Alert>
      )}
      <Group justify="flex-end">
        <Button variant="default" onClick={chiudi}>
          Indietro
        </Button>
        <Button color={colore} loading={occupato} onClick={conferma}>
          {testo}
        </Button>
      </Group>
    </>
  );
}

export function Sospendi({
  campagnaId,
  chiudi,
  fatto,
}: {
  campagnaId: number;
  chiudi: () => void;
  fatto: () => void;
}) {
  const { occupato, errore, esegui } = useInvio(fatto);
  return (
    <Modal opened onClose={chiudi} title="Sospendi la campagna">
      <Stack gap="sm">
        <Text size="sm">
          Nessun post esce finché non la riattivi. Il contenuto non cambia.
        </Text>
        <Azioni
          occupato={occupato}
          errore={errore}
          chiudi={chiudi}
          conferma={() => void esegui(() => sospendi(campagnaId))}
          testo="Sospendi"
        />
      </Stack>
    </Modal>
  );
}

export function Annulla({
  campagnaId,
  chiudi,
  fatto,
}: {
  campagnaId: number;
  chiudi: () => void;
  fatto: () => void;
}) {
  const { occupato, errore, esegui } = useInvio(fatto);
  return (
    <Modal opened onClose={chiudi} title="Annulla la campagna">
      <Stack gap="sm">
        <Alert color="red" variant="light" py="xs">
          È definitivo: i post approvati e non ancora usciti diventano annullati
          e non si pubblicano più.
        </Alert>
        <Azioni
          occupato={occupato}
          errore={errore}
          chiudi={chiudi}
          conferma={() => void esegui(() => annulla(campagnaId))}
          testo="Annulla la campagna"
          colore="red"
        />
      </Stack>
    </Modal>
  );
}

export function Riattiva({
  campagnaId,
  arretrati,
  chiudi,
  fatto,
}: {
  campagnaId: number;
  /** Post approvati con la data già passata. */
  arretrati: PostInArretrato[];
  chiudi: () => void;
  fatto: () => void;
}) {
  const [scelti, setScelti] = useState<number[]>([]);
  const { occupato, errore, esegui } = useInvio(fatto);

  return (
    <Modal opened onClose={chiudi} title="Riattiva la campagna" size="lg">
      <Stack gap="sm">
        {arretrati.length === 0 ? (
          <Text size="sm">
            Nessun post è rimasto indietro: le uscite riprendono alle date
            stabilite.
          </Text>
        ) : (
          <>
            <Text size="sm">
              {arretrati.length === 1
                ? "Un post aveva la data già passata."
                : `${arretrati.length} post avevano la data già passata.`}{" "}
              Spunta quelli da pubblicare adesso: gli altri diventano annullati.
            </Text>
            <Stack gap={6}>
              {arretrati.map((a) => (
                <Checkbox
                  key={a.postId}
                  checked={scelti.includes(a.postId)}
                  onChange={(e) =>
                    setScelti((s) =>
                      e.currentTarget.checked
                        ? [...s, a.postId]
                        : s.filter((x) => x !== a.postId),
                    )
                  }
                  label={`Uscita ${a.uscita} · ${
                    NOME_CANALE[a.canale] ?? a.canale
                  } · era per ${dataOra(a.dataOra)}`}
                />
              ))}
            </Stack>
          </>
        )}
        <Azioni
          occupato={occupato}
          errore={errore}
          chiudi={chiudi}
          conferma={() => void esegui(() => riattiva(campagnaId, scelti))}
          testo="Riattiva"
        />
      </Stack>
    </Modal>
  );
}
