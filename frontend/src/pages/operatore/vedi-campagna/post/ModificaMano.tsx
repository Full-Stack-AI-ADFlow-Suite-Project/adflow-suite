/** Modifica a mano di testo e hashtag: nasce una nuova versione dell'operatore (R-30). */
import {
  Alert,
  Button,
  Group,
  Modal,
  Stack,
  Text,
  Textarea,
  TextInput,
} from "@mantine/core";
import { useState } from "react";

import { ApiErrore } from "../../../../api/http";
import { modificaPost } from "../../../../api/interventi";
import type { PostVista } from "../../../../api/revisione";
import { NOME_CANALE } from "../../campagna/util";
import {
  AVVISO_CAMPAGNA_APPROVATA,
  conCancelletto,
  daCampoHashtag,
} from "./regole";

export function ModificaMano({
  post,
  aperto,
  approvata = false,
  chiudi,
  fatto,
}: {
  post: PostVista;
  aperto: boolean;
  /** Campagna attiva o sospesa: la versione nuova la approva l'operatore. */
  approvata?: boolean;
  chiudi: () => void;
  fatto: () => void;
}) {
  const corrente = post.versione_corrente;
  const [testo, setTesto] = useState(corrente?.testo ?? "");
  const [hashtag, setHashtag] = useState(
    conCancelletto(corrente?.hashtag ?? []),
  );
  const [occupato, setOccupato] = useState(false);
  const [errore, setErrore] = useState<string | null>(null);

  const salva = async () => {
    setOccupato(true);
    setErrore(null);
    try {
      await modificaPost(post.post_id, testo, daCampoHashtag(hashtag));
      fatto();
    } catch (e) {
      setErrore(
        e instanceof ApiErrore
          ? e.message
          : "Impossibile salvare la modifica. Riprova.",
      );
    } finally {
      setOccupato(false);
    }
  };

  return (
    <Modal
      opened={aperto}
      onClose={chiudi}
      title={`Modifica a mano · ${NOME_CANALE[post.canale] ?? post.canale}`}
      size="lg"
    >
      <Stack gap="sm">
        <Text size="sm" c="dimmed">
          Il salvataggio crea una nuova versione a tuo nome e la fa passare dal
          controllo. Non conta tra le rigenerazioni e toglie la spunta "va
          bene". Con un blocco la versione non si salva.
        </Text>
        <Textarea
          label="Testo"
          value={testo}
          onChange={(e) => setTesto(e.currentTarget.value)}
          autosize
          minRows={5}
          maxRows={14}
          data-autofocus
        />
        <TextInput
          label="Hashtag"
          description="Separati da spazio o virgola."
          value={hashtag}
          onChange={(e) => setHashtag(e.currentTarget.value)}
        />
        {errore && (
          <Alert color="red" variant="light" py="xs">
            {errore}
          </Alert>
        )}
        {approvata && (
          <Alert color="yellow" variant="light" py="xs">
            {AVVISO_CAMPAGNA_APPROVATA}
          </Alert>
        )}
        <Group justify="flex-end">
          <Button variant="default" onClick={chiudi}>
            Annulla
          </Button>
          <Button color="verde" loading={occupato} onClick={() => void salva()}>
            Salva la modifica
          </Button>
        </Group>
      </Stack>
    </Modal>
  );
}
