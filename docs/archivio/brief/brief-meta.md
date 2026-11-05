# Brief · Area Meta (T3-41…T3-43)

Per chi lavora sull'area Meta. Leggi prima `constitution.md` e `perimetro-mvp.md` (D1, "Meta in breve"). Una sola pagina di prova del team, da `.env`, per tutti gli artigiani dell'MVP. Dove il codice è diverso da come è descritto qui, vale il codice.

**Dove siamo.** `adapters/social/` ha l'interfaccia `pubblica(testo, hashtag, foto: list[bytes]) → EsitoPubblicazione` (ok, `id_esterno`, errore `temporaneo` o `definitivo`) e il finto. `pubblicazione/service.py` registra il tentativo prima della chiamata, legge i file dall'archivio, chiama `pubblica()` e ritenta gli errori temporanei: questo non cambia.

## T3-41 · Configurazione (da fare subito: ha tempi di attesa)

1. Una persona del team crea, o usa, un account Facebook personale, una **Pagina di prova** e un **account Instagram professionale** collegato alla Pagina. Ne è amministratore.
2. Su developers.facebook.com: app di tipo **Business**, con il caso d'uso per gestire una Pagina e quello per l'API di Instagram, nella strada **Instagram API with Facebook Login**. Con lo **Standard Access** l'app agisce sulle risorse di chi la sviluppa: niente App Review e niente verifica aziendale.
3. Permessi: `pages_show_list`, `pages_manage_posts`, `pages_read_engagement`, `instagram_basic`, `instagram_content_publish`.
4. **Token**: da Graph API Explorer un token utente con quei permessi → scambio con un token di lunga durata → token della Pagina (`GET /me/accounts`). L'id dell'account Instagram: `GET /{page-id}?fields=instagram_business_account`. Controllare la scadenza con lo strumento di debug dei token.
5. **Page Publishing Authorization**: se la Pagina la chiede, completarla subito, perché blocca la pubblicazione e non si sa prima.
6. **Prova a mano**, prima del codice: un post con foto sulla Pagina (`POST /{page-id}/photos` con `source` o `url` e `message`) e uno su Instagram (`POST /{ig-id}/media` con `image_url` e `caption`, poi `POST /{ig-id}/media_publish` con `creation_id`). Per Instagram serve un JPEG a un indirizzo pubblico.
7. In `backend/.env` (mai in git) e in `.env.example` con valori finti: `SOCIAL_PROVIDER`, `META_PAGINA_ID`, `META_INSTAGRAM_ID`, `META_TOKEN_PAGINA`, `META_GRAPH_VERSIONE`, `FOTO_URL_PUBBLICO`. La procedura va nel README del backend.

## T3-42 · Adattatore Meta

1. **Interfaccia** (`adapters/social/base.py`): `pubblica(canale, testo, hashtag, foto, url_foto)`. `foto` sono i byte (per Facebook), `url_foto` gli indirizzi pubblici delle stesse foto (per Instagram). Si aggiornano il finto e la chiamata in `pubblicazione/service.py`, che passa `post.canale`, i byte della foto **sistemata** per il canale (T3-21) e il suo indirizzo pubblico (T3-23). Il task tocca un'interfaccia comune: lo rivede il referente.
2. **File nuovo** `adapters/social/meta.py`, classe `SocialMeta`. `ottieni_social()` la crea con `SOCIAL_PROVIDER=meta`. Pagina, account Instagram e token da `.env`: `account_social` non si legge. Se `META_INSTAGRAM_ID` è vuoto, Instagram passa al finto: è il ripiego di D1.
3. **Didascalia**: testo, una riga vuota, gli hashtag con `#`.
4. **Facebook**: `POST /{META_GRAPH_VERSIONE}/{page-id}/photos` con la foto caricata (`source`) e `message` → `id_esterno` = `post_id` della risposta.
5. **Instagram**: `POST /{ig-id}/media` con `image_url` e `caption` → id del contenitore; `POST /{ig-id}/media_publish` con `creation_id`. Se il contenitore non è pronto, due nuovi tentativi a pochi secondi; poi errore `temporaneo` (il prossimo tick riprova con un contenitore nuovo). Niente attese lunghe nel tick.
6. **Errori**: tempo scaduto, connessione, 5xx, codici Graph di limite o temporanei (1, 2, 4, 17, 32, 613) → `temporaneo`; token non valido (190), permessi (10, 200), parametri (100) e il resto → `definitivo`, con il messaggio di Meta. Mai il token nei log.
7. **HTTP**: la libreria HTTP già nel progetto; se ne serve una nuova, si dichiara nella PR (nome, motivo, licenza).
8. **Test** in `tests/adapters/social/test_meta.py`, senza rete: risposte HTTP simulate per ok, contenitore non pronto, ogni famiglia di errore (CA-83). CA-36…CA-38 restano verdi con il finto.

## T3-43 · Pubblicazione reale provata

1. **Tunnel** di sola lettura verso l'API locale, per esempio `cloudflared tunnel --url http://localhost:8000`: l'indirizzo che stampa va in `FOTO_URL_PUBBLICO`. Instagram scarica la foto da `GET /foto/{id}/pubblica` con la firma a tempo (T3-23).
2. **Percorso**: campagna della demo approvata, `OROLOGIO_GIORNI_AVANTI` per arrivare alla data, worker acceso con `SOCIAL_PROVIDER=meta`: il tick pubblica, il post si vede su Facebook e su Instagram, `id_esterno` salvato.
3. **Ripiego** (D1): se Instagram non pubblica entro il 23/10, si svuota `META_INSTAGRAM_ID`: Facebook resta reale, Instagram passa al finto, e la PR lo dice.
