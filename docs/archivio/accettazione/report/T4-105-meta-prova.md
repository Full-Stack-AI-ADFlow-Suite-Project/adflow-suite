# T4-105 · Una pubblicazione controllata sulla pagina Meta di prova

Decisione 7 della §12: Meta si tocca **una volta sola**, a mano, sulla pagina
di prova di `.env`. Nei test resta solo l'adattatore finto.

## Che cosa è stato fatto

Il 31/10/2026, con la configurazione di `backend/.env` così com'è
(`SOCIAL_PROVIDER=meta`, token della Pagina presente, `META_INSTAGRAM_ID`
vuoto), una chiamata diretta all'adattatore vero
(`app/adapters/social/meta.py`) con:

- canale **facebook**;
- un'immagine di prova 1080 × 1080 generata sul momento (quadrata, JPEG);
- il testo: «AdFlow · prova di accettazione T4-105 del 31/10/2026. Post di
  prova, da ignorare: verifica del percorso di pubblicazione.» e due hashtag;
- nessun indirizzo pubblico (Facebook carica i byte della foto).

## Esito

| Voce | Valore |
|---|---|
| Esito | **ok** |
| Canale | facebook |
| Durata della chiamata | **4,42 s** |
| Id esterno prodotto | sì (valore **non riportato**, come chiede il brief) |
| Instagram | non configurato → simulato (ripiego D1 del perimetro) |

Una sola pubblicazione, come da decisione 7. Il token e gli id non compaiono in
questo report né nei log salvati.

## Che cosa dice la prova

- L'adattatore vero **pubblica davvero** sulla Pagina di prova: il percorso
  dalla foto ai byte, dalla didascalia all'API di Meta funziona.
- Con `META_INSTAGRAM_ID` vuoto il canale Instagram resta simulato, come deciso
  in D1: la demo mostra solo Facebook.
- Il tempo (4,4 s) è dominato dalla rete verso Meta; non è un numero di
  riferimento per il worker (che pubblica in un job, fuori dalla richiesta).

## Che cosa non dice

- Non prova il percorso completo dell'app (campagna approvata → tick → post):
  quella catena è provata con l'adattatore finto (T4-103, T4-104) e, con Meta
  vero, dalla chiusura di T3-07 secondo `qa/corsia9/T3-927/`.
- Non prova la scadenza o la revoca del token: se il token scade, il post
  diventa `fallito` con un errore definitivo (comportamento coperto dai test
  dell'adattatore). La rotazione del token non è automatizzata (R-07/D5 della
  roadmap).
