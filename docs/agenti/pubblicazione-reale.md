# Pubblicazione reale su Facebook e Instagram

Proposta per il gruppo (corsia 4, revisione di gruppo). Oggi
`ottieni_social()` restituisce solo `SocialFinto`: nessun post esce davvero.
Plan §5 prevede due implementazioni dell'adattatore social, «simulato e
Meta». Obiettivo: post reali visibili → app Meta in modalità sviluppo +
pagina di test di nostra proprietà, publishing via Graph API, **senza App
Review e senza automazione browser** (§9).

Il lavoro va in due fasi, da confermare con il coordinatore:

- **Fase A · Demo a pagina singola**: credenziali di una pagina di test in
  configurazione, interfaccia `SocialAdapter` **invariata**,
  `SOCIAL_PROVIDER=finto|meta`. Basta a mostrare un post vero.
- **Fase B · Multi-artigiano**: token per bottega in `account_social.permesso`
  (cifrato), destinazione passata a `pubblica()`, `collega_account()` OAuth,
  endpoint media firmato per Instagram. Coincide con lo sprint 3 (T3-13,
  T3-41, T3-43) e va oltre la demo.

## 0. Processo prima di iniziare

- [ ] Chiedere al coordinatore la riga in `tasks.md`. Bozza (ID da assegnare
      allo sprint corrente; l'adattatore simulato di T1-41 è già su `main`):

  `T?-4x | Adattatore social Meta: SocialMeta con httpx, POST /{page}/photos, mappatura errori → temporaneo/definitivo, config SOCIAL_PROVIDER/META_* (con corsia 0) | plan §5; constitution §3 | T1-41 | publish vero verificato su pagina di test + test verdi | ☐`

- [ ] Avvisare che si toccano `core/config.py` e `.env.example` → corsia 0;
      stessa PR con revisione di gruppo (precedente: issue #16–19).
- [ ] Chiarire col prof: basta Facebook in demo o serve anche Instagram? Per
      IG serve un URL pubblico per le foto (§4) — costo diverso.
- [ ] Branch: `feature/T?-4x-adattatore-meta` (ID del task assegnato).

## 1. Setup Meta manuale (browser, ~30–60 min)

- [ ] Pagina Facebook di test (es. «AdFlow Test»), admin = noi.
- [ ] App su developers.facebook.com, tipo *Business*: resta in modalità
      sviluppo. Da *App Settings → Basic*: App ID e App Secret.
- [ ] Graph API Explorer → selezionare l'app → *Generate Access Token* con
      `pages_manage_posts`, `pages_read_engagement`, `pages_show_list`
      (per la fase IG anche `instagram_basic`, `instagram_content_publish`,
      `business_management`).
- [ ] `GET /me/accounts` → `id` della pagina e `access_token` **di pagina**
      (è quello da salvare).
- [ ] Long-lived (~60 gg):
      `GET /oauth/access_token?grant_type=fb_exchange_token&client_id={APP_ID}&client_secret={APP_SECRET}&fb_exchange_token={TOKEN}`
- [ ] Solo per IG: `GET /{page_id}?fields=instagram_business_account` →
      `instagram_business_account.id`. L'account IG deve essere Business/
      Creator e collegato alla pagina.
- [ ] Valori in `backend/.env` (mai in git); procedura di rinnovo del token
      documentata in `docs/novita/` con la nota della PR.

## 2. Configurazione (corsia 0 — nella stessa PR, revisione di gruppo)

`core/config.py` e `.env.example` con valori finti:

```env
SOCIAL_PROVIDER=finto
GRAPH_VERSION=v21.0
META_PAGE_ID=
META_PAGE_TOKEN=
META_IG_USER_ID=        # solo fase A-IG o fase B demo
PUBLIC_BASE_URL=        # base pubblica per gli image_url di IG; vuoto = off
SOCIAL_CHIAVE_CIFRA=    # fase B: chiave Fernet per account_social.permesso
```

Nessuna libreria nuova: `httpx2` (importato come `httpx`) e `cryptography`
sono già in `requirements.txt`.

## 3. Flussi API di pubblicazione

Base: `https://graph.facebook.com/{GRAPH_VERSION}`. Token nel body dei
parametri, mai nell'URL né nei log.

### Facebook — foto su pagina

- **Una foto**: `POST /{page_id}/photos`, multipart `source` (i byte del
  file), `caption` = testo + hashtag, `access_token`. I byte dall'archivio
  bastano, niente URL pubblici.
- **Più foto**: per ognuna `POST /{page_id}/photos` con `published=false` →
  `id`; poi `POST /{page_id}/feed` con `message` e
  `attached_media[i]={"media_fbid":"..."}` (JSON), in ordine.
- Evidenza: `GET /{post_id}?fields=permalink_url`.
- Timeout 30 s sulle chiamate.

### Instagram — Content Publishing API

Vincolo: **`image_url` pubblicamente raggiungibile** — IG scarica la foto
dai suoi server, il multipart non esiste. JPEG/PNG; proporzioni 4:5–1.91:1
(le scelte MVP di R-21, 1:1 e 4:5, sono compatibili).

- **Una immagine**: `POST /{ig_user_id}/media` con `image_url`, `caption` →
  `id` contenitore; attesa `GET /{id}?fields=status_code` fino a `FINISHED`;
  `POST /{ig_user_id}/media_publish` con `creation_id` → `id` media.
- **Carosello (2–10)**: un contenitore per immagine con
  `is_carousel_item=true` (attesa `FINISHED` per ognuno), poi contenitore
  `media_type=CAROUSEL` con `children=<id1,id2,…>` e `caption`; poi
  `media_publish`.
- Il contenitore scade (~24 h): si crea e pubblica nel tick.
- Evidenza: `GET /{media_id}?fields=permalink`.
- Limite piattaforma: ~25 pubblicazioni API per account nelle 24 h.

## 4. Il vincolo `image_url` di Instagram

Le foto stanno nell'archivio locale: per IG serve esporle.

- **Demo/sviluppo**: tunnel verso il backend — `cloudflared tunnel --url
  http://localhost:8787` dà un `https://…trycloudflare.com` senza account né
  modifiche al codice (lo script di §7 lo usa con `--public-base`).
- **Produzione**: endpoint pubblico `GET /media/{foto_id}/file?scade=&firma=`
  con firma HMAC e scadenza breve, attivo solo se `PUBLIC_BASE_URL` è
  configurato — cambio di architettura da concordare (corsia 0). Un bucket
  pubblico sarebbe un servizio nuovo: sconsigliato per l'MVP
  (constitution §2).

## 5. Design del codice

```
adapters/social/
  base.py    SocialAdapter, EsitoPubblicazione            (fase B: + DestinazioneSocial)
  finto.py   invariato (fase B: solo firma aggiornata)
  meta.py    SocialMeta: implementazione reale via Graph API
```

**Fase A (demo, interfaccia invariata)**:

- `SocialMeta(SocialAdapter)`: `pubblica(testo, hashtag, foto)` con
  `foto: list[bytes]` dal service (`pubblica_dovuti` passa già i byte letti
  con `archivio.leggi`, non serve accedere ai file).
- Page id e token da `leggi_impostazioni()`; `ottieni_social()` istanzia
  `SocialMeta` quando `SOCIAL_PROVIDER=meta`, altrimenti `SocialFinto`.
  Config mancante → errore chiaro all'avvio, non a metà di un tick.
- **Attenzione al canale**: la firma non porta il canale, quindi `SocialMeta`
  non può distinguere un post Facebook da uno Instagram. In demo si risolve
  così: l'artigiano di prova ha **solo Facebook** collegato in
  `account_social` — R-22 impedisce di creare campagne sul canale non
  collegato, i post IG non nascono. Se si vuole IG in demo serve la fase B
  (firma con destinazione).

**Fase B (multi-artigiano)**:

- `pubblica()` riceve la destinazione: proposta
  `pubblica(destinazione: DestinazioneSocial, testo, hashtag, foto)` con
  `DestinazioneSocial(piattaforma, id_pagina, token)`. `SocialFinto` la
  ignora; `SocialMeta` la usa per scegliere FB o IG e le credenziali.
- `pubblicazione.service` la legge con `artigiani.account_social()` (firma
  corsia 0 in T3-01, corpo corsia 1 in T3-13) al posto del solo controllo
  `canali_collegati`; il token si decifra con `cifra_segreta`/
  `decifra_segreta` in `core/security.py` (corsia 0).
- `collega_account()` OAuth (plan §5, T3-41 oggi simulato) e
  `leggi_metriche()` restano le altre firme.

## 6. Mappatura errori → `tipo_errore` (critico per T1-43)

`pubblica_dovuti()` riprova solo i `temporaneo`; i `definitivo` portano il
post a `fallito`. La risposta Meta ha `error.code`, `error.error_subcode`,
`error.is_transient`, `error.message`:

- `is_transient=true`, timeout di rete, HTTP 5xx, rate limit (code 4, 17,
  32, 613) → `temporaneo`: il tentativo resta `in_corso`, riprova il tick
  dopo, fino a `TENTATIVI_MAX`.
- `code 190` (token invalido/scaduto), `code 10`/`200` (permesso negato) →
  `definitivo`. In fase B è anche il gancio di R-07: account `scaduto` →
  campagna `sospesa` con avvisi (T3-43).
- `code 100`/`error_subcode` su media (formato, proporzioni, URL non
  raggiungibile) → `definitivo` (il ritaglio di T3-33 lo previene, ma va
  gestito).
- `message` va in `pubblicazione.errore` per l'operatore, **senza token né
  dati personali** (constitution §3).

## 7. Prova una tantum (già pronta)

`backend/scripts/pubblica_reale.py` — pubblica un post vero senza toccare
l'adattatore, con i flussi del §3. Configurazione in `backend/.env` (mai in
git): `META_ACCESS_TOKEN`, `META_PAGE_ID`, `META_IG_USER_ID`, `GRAPH_VERSION`
facoltativa.

```bash
cd backend
# solo Facebook: i file locali bastano
uv run python scripts/pubblica_reale.py --confermo \
  --testo "Prova di pubblicazione" --hashtag adflow prova \
  --foto archivio_foto/una.jpg --canali facebook

# Instagram: servono URL pubblici. Lo script espone le foto su
# localhost:8787; in un altro terminale:
#   cloudflared tunnel --url http://localhost:8787
uv run python scripts/pubblica_reale.py --confermo \
  --testo "Prova" --foto archivio_foto/una.jpg \
  --public-base https://xxx-yyy.trycloudflare.com
```

`--confermo` è obbligatorio; il token non viene mai stampato. Evidenza da
allegare: i permalink stampati, screenshot dei post, (fase A) la riga
`pubblicazione` su DB quando il tick pubblica davvero.

## 8. Test

- Suite esistente invariata: gira su `SocialFinto` (constitution §3: nessuna
  chiamata di rete nei test).
- Nuovi test unitari di `meta.py` con risposte HTTP simulate (stub del
  client, es. `httpx.MockTransport`): ok, temporaneo, definitivo, timeout —
  uno per voce della mappatura del §6.
- Prova manuale finale: `SOCIAL_PROVIDER=meta` + token → publish vero sulla
  pagina di test.

## 9. Alternativa scartata: Playwright via UI

Posting via browser automatizzato viola i ToS Meta (ban probabile anche su
account di test), è fragile (selettori che cambiano) e pesante nel worker.
Tenuto come unico fallback se il prof rifiuta l'app Meta; Playwright può
restare per test E2E in sola lettura (verificare che il post appaia).

## 10. Bozza dei task (per `tasks.md`, quando il gruppo approva)

| ID | Corsia | Task | Tocca | Dipende da | Fatto quando |
|---|---|---|---|---|---|
| T?-01 | 0 | Config social reale: `SOCIAL_PROVIDER`, `GRAPH_VERSION`, `META_*`, `PUBLIC_BASE_URL` in `config.py` e `.env.example`; in fase B anche `SOCIAL_CHIAVE_CIFRA` e `cifra_segreta`/`decifra_segreta` in `core/security.py` | `core/config.py`, `core/security.py`, `.env.example`, `docs/agenti/` | task assegnato | variabili dichiarate, valori finti, nessuna logica |
| T?-41 | 4 | `SocialMeta` Facebook: upload foto singola e multi-foto (`/photos` + `/feed` con `attached_media`), timeout, mappatura errori del §6; `ottieni_social()` sceglie da `SOCIAL_PROVIDER` | `adapters/social/meta.py` (nuovo), `adapters/social/__init__.py`, `tests/adapters/social/` | T?-01 | post FB vero su pagina di test; test con risposte simulate verdi |
| T?-42 | 4 | `SocialMeta` Instagram: flusso contenitori; foto servite via tunnel (demo) o endpoint firmato (prod, fase B) | `adapters/social/meta.py`, endpoint media se si sceglie, i test | T?-41 | post IG vero; contenitore scaduto → nuovo tentativo |
| T?-43 | 4 | Fase B: `DestinazioneSocial` e firma estesa, token cifrato in `account_social.permesso` via `account_social()`, limite ~25 post IG/24 h, `leggi_metriche()` se serve alla demo | `adapters/social/`, `pubblicazione/service.py`, i test | T3-13, T3-43 | post con account della bottega; R-07 agganciata |

## 11. Domande aperte per il gruppo

1. Demo: basta Facebook (artigiano di test con solo quel canale) o serve
   anche Instagram subito?
2. `image_url` di IG in produzione: endpoint firmato o hosting esterno?
3. `collega_account()`: OAuth vero o token inserito a mano dall'operatore
   per l'MVP?
4. Su quale staging pubblico puntare `PUBLIC_BASE_URL` — si aggancia
   all'evidenza della issue #17?
5. Serve App Review avanzata se si pubblicherà su pagine non amministrate
   dal consorzio?
