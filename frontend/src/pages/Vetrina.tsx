/**
 * Vetrina: pagina pubblica di arrivo (/) per chi non ha una sessione.
 * Hero a tutto schermo su foto di bottega (public/vetrina-hero-4k.jpg) con
 * nav a pillola e CTA; sotto, benefici e come funziona. Solo contenuto
 * statico più il contatto del consorzio (GET /api/consorzio, senza
 * accesso). «Entra» porta ad /accesso. Chi ha già una sessione va
 * diretto alla propria pagina di partenza (App.tsx, Partenza).
 */
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Button, Text } from "@mantine/core";

import { consorzio } from "../api/consorzio";
import type { Consorzio } from "../api/accesso";
import { Wordmark } from "../components/Wordmark";
import stili from "./Vetrina.module.css";

const BENEFICI = [
  {
    titolo: "Contenuti su misura",
    testo: "Testi e immagini creati sul profilo della tua bottega: prodotti, tono di voce e clienti che vuoi raggiungere.",
    icona: "M12 20h9 M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z",
  },
  {
    titolo: "Un calendario pronto",
    testo: "Settimane di post già programmati e rivisti dal consorzio prima che esca qualsiasi cosa.",
    icona: "M8 2v4 M16 2v4 M3 10h18 M5 4h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2Z",
  },
  {
    titolo: "Pubblicazione automatica",
    testo: "I post approvati escono su Facebook e Instagram all'ora giusta, senza che tu debba ricordartene.",
    icona: "M22 2 11 13 M22 2l-7 20-4-9-9-4Z",
  },
];

const PASSI = [
  {
    titolo: "Racconti la tua bottega",
    testo: "Compili il profilo una volta: cosa fai, dove sei, che clienti hai.",
  },
  {
    titolo: "Scegli e carichi, noi prepariamo",
    testo: "Periodo, canali e foto della bottega li dai tu; testi e immagini li prepara AdFlow.",
  },
  {
    titolo: "Il consorzio approva e i post escono da soli",
    testo: "Ogni post passa prima dal consorzio; poi esce sui social giorno dopo giorno.",
  },
];

export function Vetrina() {
  const [contatto, setContatto] = useState<Consorzio | null>(null);

  useEffect(() => {
    consorzio()
      .then(setContatto)
      .catch(() => setContatto(null));
  }, []);

  return (
    <div className={stili.pagina}>
      <section className={stili.hero} aria-label="Presentazione">
        <header className={stili.topbar}>
          <div className={stili.brand}>
            <Wordmark chiaro />
          </div>
          <nav className={stili.navPill} aria-label="Sezioni della pagina">
            <a href="#benefici">Benefici</a>
            <a href="#come-funziona">Come funziona</a>
            <Link to="/accesso">Entra</Link>
          </nav>
          <a className={stili.contattiLink} href="#contatti">
            Contatti
          </a>
        </header>

        <div className={stili.heroBase}>
          <h1 className={stili.titolo}>
            I social della tua bottega, curati da chi li sa fare.
          </h1>
          <p className={stili.sottotitolo}>
            AdFlow prepara per te testi, immagini e un calendario di
            pubblicazione. Il consorzio approva ogni post, poi esce su
            Facebook e Instagram.
          </p>
          <Button
            component={Link}
            to="/accesso"
            size="lg"
            radius="xl"
            variant="white"
            color="dark"
          >
            Accedi al tuo account
          </Button>
        </div>
      </section>

      <main>
        <section className={stili.sezione} id="benefici">
          <h2 className={stili.titoloSezione}>Pensato per la bottega</h2>
          <p className={stili.sottotitoloSezione}>
            Niente strumenti complicati da imparare: la campagna la prepara il
            consorzio, tu vedi solo quello che serve.
          </p>
          <div className={stili.griglia}>
            {BENEFICI.map((b) => (
              <article key={b.titolo} className={stili.voce}>
                <span className={stili.voceIcona}>
                  <svg
                    width="20"
                    height="20"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    aria-hidden
                  >
                    <path d={b.icona} />
                  </svg>
                </span>
                <h3 className={stili.voceTitolo}>{b.titolo}</h3>
                <p className={stili.voceTesto}>{b.testo}</p>
              </article>
            ))}
          </div>
        </section>

        <section className={stili.sezione} id="come-funziona">
          <h2 className={stili.titoloSezione}>Come funziona</h2>
          <p className={stili.sottotitoloSezione}>
            Tre passi, dall'iscrizione alla pubblicazione.
          </p>
          <div className={stili.passi}>
            {PASSI.map((p) => (
              <div key={p.titolo} className={stili.passo}>
                <h3 className={stili.voceTitolo}>{p.titolo}</h3>
                <p className={stili.voceTesto}>{p.testo}</p>
              </div>
            ))}
          </div>
        </section>
      </main>

      <footer className={stili.footer} id="contatti">
        <span className={stili.footerBrand}>
          <Wordmark chiaro dimensione={15} /> · La vetrina delle botteghe del
          consorzio
        </span>
        <span className={stili.footerDestra}>
          {contatto && (
            <Text component="span" size="sm" c="inherit">
              {contatto.nome} · Tel. {contatto.telefono} · {contatto.email}
            </Text>
          )}
          <Link to="/privacy" className={stili.footerLink}>
            Privacy
          </Link>
        </span>
      </footer>
    </div>
  );
}
