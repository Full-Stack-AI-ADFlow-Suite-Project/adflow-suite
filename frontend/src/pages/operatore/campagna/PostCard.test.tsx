import { fireEvent, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { PostVista } from "../../../api/revisione";
import { disegna } from "../../../test/render";
import { PostCard } from "./PostCard";

function post(extra: Partial<PostVista> = {}): PostVista {
  return {
    post_id: 7,
    canale: "instagram",
    formato: "foto",
    riempitivo: null,
    data_ora: "2030-01-09T12:00:00Z",
    stato: "da_approvare",
    da_rivedere: false,
    controllato_da: null,
    controllato_il: null,
    intervento_in_corso: null,
    intervento_dal: null,
    versioni: [],
    interventi: [],
    versione_corrente: {
      id: 1,
      numero: 1,
      testo: "Un vaso nuovo, fatto a mano.",
      hashtag: ["ceramica"],
      autore_id: null,
      tipo_intervento: "generazione",
      testo_proposto: null,
      nota: null,
      provider_ai: null,
      modello_ai: null,
      versione_prompt: null,
      errori_validazione: null,
      creata_il: "2030-01-01T10:00:00Z",
      foto: [{ foto_id: 41, posizione: 1 }],
    },
    foto: {
      anteprima_url: "/api/post/7/foto/anteprima",
      varianti: {
        disponibili: ["originale", "standard"],
        uguali: ["standard"],
        scelta: "standard",
      },
      zone_privacy: { numero: 0, decise: 0 },
      avvisi: [],
    },
    ...extra,
  };
}

function disegnaCard(p: PostVista) {
  return disegna(
    <PostCard
      post={p}
      bottega="Ceramiche Rossi"
      citta="Faenza"
      tema="Vasi di primavera"
      statoCampagna="in_revisione"
      ricarica={() => {}}
    />,
  );
}

describe("PostCard · foto", () => {
  it("mostra l'immagine dell'anteprima, con il testo alternativo", () => {
    disegnaCard(post());
    const img = screen.getByAltText("Foto 41");
    expect(img).toHaveAttribute("src", "/api/post/7/foto/anteprima");
  });

  it("senza anteprima torna all'originale", () => {
    disegnaCard(post({ foto: null }));
    expect(screen.getByAltText("Foto 41")).toHaveAttribute(
      "src",
      "/api/foto/41/file",
    );
  });

  it("mostra il caricamento finché l'immagine non arriva", () => {
    disegnaCard(post());
    expect(screen.getByLabelText("Caricamento della foto")).toBeInTheDocument();
    fireEvent.load(screen.getByAltText("Foto 41"));
    expect(
      screen.queryByLabelText("Caricamento della foto"),
    ).not.toBeInTheDocument();
    expect(screen.getByAltText("Foto 41")).toBeVisible();
  });

  it("mostra un messaggio se l'immagine non arriva", () => {
    disegnaCard(post());
    fireEvent.error(screen.getByAltText("Foto 41"));
    expect(screen.getByRole("alert")).toHaveTextContent(
      "Anteprima non disponibile",
    );
    expect(screen.queryByAltText("Foto 41")).not.toBeInTheDocument();
  });

  it("l'immagine creata con AI ha il suo testo alternativo", () => {
    disegnaCard(post({ riempitivo: "immagine_ai" }));
    expect(screen.getByAltText("Immagine creata con AI")).toBeInTheDocument();
  });
});
