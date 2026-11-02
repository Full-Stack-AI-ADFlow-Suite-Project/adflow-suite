# Valutazione e piano di sicurezza

**Stato della revisione:** 30 ottobre 2026

**Ambito:** revisione statica e dinamica locale del codice, della configurazione e della documentazione presenti nel repository.
Documento operativo per decidere e verificare gli interventi; non è una certificazione, un penetration test o una verifica di un ambiente di staging remoto.

Per le istruzioni operative già definite per l'accesso, i cookie, il proxy e i log si veda anche [`sicurezza-accesso.md`](sicurezza-accesso.md). La verifica locale del proxy/TLS con certificato verificato e processo Uvicorn separato è documentata in `qa/issue-17/README.md` (follow-up #17 chiuso per la parte locale).

## Valutazione sintetica

L'applicazione ha buone difese applicative di base: password con scrypt, sessioni casuali memorizzate nel database solo come hash, cookie `HttpOnly` e `SameSite=Lax`, controllo dei ruoli lato server, verifiche di proprietà per le risorse degli artigiani, rate limit persistente del login, limite al body HTTP e controlli sui file immagine.

Non considero ancora dimostrata la sicurezza per un'esposizione pubblica con dati reali. Il task T3-09 ha aggiunto un controllo CSRF same-origin attivo in produzione, validazione HTTPS di `FOTO_URL_PUBBLICO`, probe SAST/DAST locali e un runner con log JSONL live e scrittura sincronizzata tra processi. I log riportano fasi/test e ciclo di vita HTTP in forma redatta: non includono body, query string, header, cookie o valori dei casi parametrizzati. Restano da dimostrare TLS/proxy in staging e da pianificare MFA, durata massima delle sessioni, abuso delle API, segreti e monitoraggio. Le immagini firmate accessibili anonimamente sono una scelta intenzionale per Meta, ma il link va trattato come una credenziale temporanea.

I probe dinamici eseguiti usano il client ASGI locale, non un server esposto in rete. Non sono stati eseguiti scansioni CVE, un test di penetrazione o verifiche dello staging. `scripts/esegui_valutazione_sicurezza.py` imposta `DATABASE_URL` e `DATABASE_URL_TEST` sul solo `adflow_test` locale, rifiuta destinazioni non conformi e scrive un log JSONL live ignorato da Git. La suite completa elimina e ricrea lo schema di quel database di test. La presenza di una configurazione o di un test nel repository non dimostra da sola che il deployment la applichi.

## Controlli già presenti

- **Credenziali e sessioni:** password protette con scrypt e salt casuale; token di sessione casuali, conservati nel DB come hash; cookie `HttpOnly`, `SameSite=Lax` e `Secure` in produzione; sessione rinnovata durante l'attività.
- **Autorizzazione e isolamento:** endpoint protetti con ruoli lato API; le operazioni sulle campagne e sulle foto verificano l'utente proprietario; gli accessi non autorizzati a risorse altrui possono restituire 404.
- **Abuso del login:** limite atomico e persistente per IP e account; errori generici per credenziali non valide; verifica password fittizia anche per account inesistenti; eventi di sicurezza senza credenziali o dati ricevuti dal client.
- **Richieste e immagini:** limite globale alla dimensione del body; verifica del formato e delle dimensioni/pixel delle immagini; archivio con nomi generati dal server e controlli contro path traversal; immagini pubblicate rielaborate in JPEG senza metadati EXIF/GPS.
- **Integrazioni:** il provider AI/social è selezionabile via configurazione; il codice Meta evita di includere il token nei messaggi restituiti; i test dichiarano di non chiamare servizi AI, Meta o email reali.

Questi controlli sono una buona base, ma non sostituiscono la verifica del deployment e i punti di completamento qui sotto.

## Interventi richiesti prima dell'esposizione pubblica

### P0 — TLS, proxy e confine di rete

**Stato:** da verificare in staging. I test locali con TLS sono descritti in `docs/sicurezza-accesso.md`; resta da allegare l'evidenza dell'ambiente reale al follow-up #17.

- [ ] Terminare TLS con certificato valido; reindirizzare HTTP a HTTPS e abilitare HSTS sul frontend/proxy dopo aver verificato tutti gli host coinvolti.
- [ ] Fare in modo che il backend sia raggiungibile solo dal proxy fidato, non direttamente da Internet. Configurare gli header inoltrati solo per gli IP del proxy; non usare `--forwarded-allow-ips '*'`.
- [ ] Sovrascrivere al proxy gli header `Host`, `X-Forwarded-Proto` e `X-Forwarded-For` ricevuti dal client; impedire lo spoofing di schema e IP.
- [ ] Verificare sul deployment che il cookie di login, rinnovo e logout abbia `Secure`, `HttpOnly`, `SameSite=Lax`, `Path=/` e nessun attributo `Domain`.
- [ ] Disabilitare o filtrare gli access log che registrano query string o URL completi, in particolare per i link firmati delle foto. Non registrare cookie, token, password o corpi delle richieste.
- [x] Validare all'avvio in produzione che `FOTO_URL_PUBBLICO` sia un URL HTTPS sintatticamente valido, senza credenziali, query o fragment; se Instagram Meta è configurato, richiedere l'URL.
- [ ] Verificare nello staging che il dominio HTTPS punti all'host previsto.
- [ ] Aggiungere e verificare al livello che serve il frontend (reverse proxy/CDN) gli header di sicurezza: CSP con `frame-ancestors`, `X-Content-Type-Options: nosniff`, `Referrer-Policy`, `Permissions-Policy` e protezione anti-framing. Non introdurre una policy CORS permissiva; se frontend e API sono separati, autorizzare solo le origini note.

**Criteri di completamento:** evidenza staging senza segreti che mostri HTTPS end-to-end verso il proxy, cookie corretti, header del client non fidati sovrascritti, backend non raggiungibile direttamente e redirect HTTPS funzionante.

### P0 — Configurazione di produzione e gestione dei segreti

**Stato:** il codice rifiuta in produzione il segreto di login di esempio e `COOKIE_SECURE=false`; va completata la separazione e la gestione operativa dei segreti.

- [ ] Conservare `LOGIN_LIMITE_SEGRETO`, `META_TOKEN_PAGINA` e `OPENAI_API_KEY` in un secret manager o nel sistema sicuro del deployment, mai nel repository, nelle immagini container o nei log.
- [ ] Generare segreti casuali con entropia adeguata; il controllo di lunghezza minima non dimostra che il valore scelto sia casuale.
- [ ] Separare la chiave del rate limit dalla chiave che firma gli URL pubblici delle foto. La chiave per le foto deve avere nome, scopo e procedura di rotazione propri.
- [ ] Definire rotazione e revoca dei segreti, incluse le conseguenze operative: il segreto del rate limit cambia i contatori; la chiave delle foto invalida i link firmati già emessi. Coordinare la rotazione tra tutte le istanze.
- [ ] Limitare i permessi del token Meta al minimo necessario e all'account/pagina di test previsto dall'MVP. Documentare chi può leggerlo e come revocarlo.
- [ ] Usare un account DB dedicato al runtime, con privilegi minimi; mantenere credenziali DB diverse per sviluppo, test e produzione.
- [ ] Configurare TLS verificato per la connessione al database quando DB e backend comunicano su rete non locale. Il codice di connessione imposta il fuso orario, ma non forza da solo TLS.
- [ ] Verificare proprietario e permessi dell'archivio foto e dei file di configurazione; non servire la directory dell'archivio come contenuto statico pubblico.
- [ ] Cifrare backup e volumi secondo le capacità dell'ambiente; definire retention e provare almeno una procedura di ripristino.

**Criteri di completamento:** avvio di produzione impossibile con segreti di esempio, token mancanti o URL media non HTTPS; credenziali non presenti nel repository; accessi a segreti, DB, archivio e backup limitati e documentati.

### P0 — Protezione CSRF per le API con cookie

**Stato:** il cookie usa `SameSite=Lax`; il middleware CSRF aggiunto rifiuta in produzione richieste mutanti senza un `Origin` valido e same-origin.

- [x] In produzione, le richieste `POST`, `PUT`, `PATCH` e `DELETE` richiedono `Origin` valido uguale all'origine della richiesta. La verifica copre anche gli endpoint multipart.
- [x] Aggiungere probe dinamici per origine assente, `null`, non corrispondente e stessa origine.
- [x] Rifiutare richieste con origine inattesa; coperti nei test origine assente, `null`, esterna, malformata e same-origin.
- [ ] Aggiungere e provare il caso specifico di sottodominio sibling non autorizzato.
- [ ] Mantenere le API same-origin se possibile. Se frontend/API sono separati, definire una allowlist esatta e non abilitare credenziali CORS per origini arbitrarie.
- [ ] Non affidare la protezione CSRF alla sola UI React o alla navigazione protetta: i controlli devono essere nell'API.

**Criteri di completamento residui:** verificare sul deployment proxy e host attesi; eseguire un test browser end-to-end su upload e azioni mutanti prima del rilascio.

## Esecuzione locale della valutazione

Da `backend/`, su Windows o altro ambiente di sviluppo locale:

```powershell
uv run python scripts/esegui_valutazione_sicurezza.py --security-only
uv run python scripts/esegui_valutazione_sicurezza.py
```

Il primo comando esegue solo i probe SAST/DAST locali. Il secondo esegue tutta la suite: la fixture ricrea lo schema di `adflow_test`. Il runner verifica prima che il DB sia esattamente quello locale atteso e imposta entrambi gli URL del processo su tale DB. Il log JSONL si trova in `backend/security-assessment-logs/` e non va committato; non contiene body, query string, header o credenziali.

**Ultima esecuzione locale:** 30 ottobre 2026, Linux (`adflow_test` su `localhost:5432`).

- Probe SAST/DAST e integrità multiprocesso dei log: **34 passati**.
- Verifica TLS/proxy reale (`tests/moduli/accesso/test_proxy_http_reale.py`): **2 passati** (catena HTTPS con proxy fidato `127.0.0.1` e rifiuto header da proxy non fidato `192.0.2.1`).
- Suite completa, con `DATABASE_URL` e `DATABASE_URL_TEST` entrambi diretti a `adflow_test` su `localhost:5432`: **1.997 passati, 0 falliti, 0 errori, 0 saltati**.
- Integrità del log JSONL: **valida**; nessuna riga malformata.

### P0 — MFA e durata delle sessioni privilegiate

**Stato:** login con password; non risulta MFA. La scadenza della sessione è rinnovata con l'attività e non costituisce una durata massima assoluta.

- [ ] Aggiungere MFA almeno per `operatore` e `admin` prima di consentire accesso pubblico agli operatori. Preferire passkey/WebAuthn o TOTP; proteggere e rendere monouso eventuali codici di recupero.
- [ ] Aggiungere un limite assoluto alla durata della sessione, distinto dal timeout di inattività; definire valori per ruolo e documentarli.
- [ ] Fornire una procedura affidabile per revocare tutte le sessioni di un utente e per disabilitare immediatamente un account.
- [ ] Valutare una schermata di sessioni attive e una revoca per dispositivo se l'app esce dall'MVP.
- [ ] Progettare in un task separato recupero/cambio password sicuro: token casuale monouso, hash nel DB, scadenza breve, rate limit, risposta che non riveli se l'email esiste e revoca delle sessioni dopo il reset.
- [ ] Per l'MVP, mantenere la procedura prevista per la password provvisoria mostrata una sola volta; non introdurre un cambio obbligatorio se questo cambia il perimetro concordato. Definire invece un passaggio sicuro di consegna e una procedura di reset per credenziali esposte.

**Criteri di completamento:** test di MFA, scadenza inattività, scadenza assoluta, revoca singola e globale, account disabilitato e reset password; nessun token di recupero o password nei log.

### P0 — Limiti di abuso e spesa

**Stato:** il rate limit persistente riguarda il login; non risulta un limite generale per le API o per le chiamate AI.

- [ ] Aggiungere rate limit per endpoint e utente autenticato, con limiti più stretti per creazione campagne, upload, rigenerazioni e operazioni che accodano lavoro.
- [ ] Aggiungere limiti di concorrenza e protezioni contro la creazione ripetuta di job; rendere i limiti coerenti tra istanze.
- [ ] Configurare sul provider AI un budget/alert e un interruttore di emergenza; monitorare spesa e volumi per campagna/utente.
- [ ] Decidere esplicitamente se mantenere l'assenza di un tetto di spesa descritta nel perimetro MVP. Se si vuole un limite applicativo, aggiornare prima il perimetro e i criteri di prodotto.
- [ ] Proteggere gli endpoint pubblici e l'endpoint di download foto da richieste massive con limiti di frequenza e di concorrenza al proxy, senza impedire i fetch legittimi di Meta.
- [ ] Verificare il limite di dimensione anche nel proxy, così il body non viene accettato o bufferizzato integralmente a monte dell'applicazione.

**Criteri di completamento:** test di soglia e concorrenza; risposte `429` con retry sensato; un account non può saturare worker, storage o budget AI senza attivare limiti/alert previsti.

## Interventi successivi e hardening

### Link pubblici firmati per le foto

**Stato:** endpoint anonimo necessario a Meta; firma HMAC e scadenza presenti. La durata predefinita è 24 ore e la risposta usa `Cache-Control: public, max-age=3600`.

- [ ] Usare la chiave dedicata prevista nella sezione segreti e una durata minima compatibile con il fetch del social.
- [ ] Verificare che la firma venga emessa solo dal flusso di pubblicazione autorizzato e solo per una foto associata al post/tentativo da pubblicare; non aggiungere endpoint pubblici che permettano di firmare ID arbitrari.
- [ ] Ridurre o allineare la cache alla scadenza della firma; accertarsi che CDN/proxy non servano contenuti oltre la policy stabilita.
- [ ] Non includere firme o URL firmati in log, analytics, errori o referrer. Mantenere `nosniff` e un tipo MIME controllato.
- [ ] Documentare che l'URL è una credenziale bearer temporanea e che chi lo possiede può leggere la foto fino alla scadenza.
- [ ] Testare firma alterata, scaduta, canale errato, foto inesistente, data futura e accesso anonimo atteso per Meta.

### Audit, logging e risposta agli incidenti

**Stato:** gli eventi applicativi di sicurezza registrano alcuni fallimenti di accesso e dinieghi; scrivono JSON su stderr. La documentazione richiede raccolta, rotazione e monitoraggio.

- [ ] Centralizzare i log in un sink con accesso ristretto, retention definita, rotazione e allarmi; verificare che il sink non acquisisca query string o credenziali dal proxy.
- [ ] Aggiungere eventi minimali per creazione/disattivazione utenti, cambi ruolo, operazioni amministrative, approvazione/rifiuto, avvio/esito pubblicazione e rotazione/revoca credenziali.
- [ ] Associare gli eventi a `request_id` e a un identificativo attore minimizzato; non registrare password, cookie, token, payload, URL firmati, immagini o dati personali non necessari.
- [ ] Definire allarmi per aumento di login falliti/limitati, errori del limiter, uso anomalo delle API, spesa AI, errori Meta e tentativi ripetuti di accesso a risorse.
- [ ] Preparare una procedura incidenti: contatti, revoca token Meta/AI, invalidazione sessioni, rotazione segreti, conservazione delle evidenze e comunicazione agli interessati quando applicabile.

**Criteri di completamento:** test che verificano formato e redazione dei log; allarmi provati in staging; procedura di revoca e risposta accessibile solo ai responsabili.

### Dipendenze e pipeline CI

**Stato:** backend con versioni dirette fissate e frontend con `package-lock.json`; la CI esegue i controlli SAST/DAST applicativi custom e test/lint/build. Per indicazione del docente non sono stati aggiunti scanner esterni né eseguite scansioni CVE in questa attività.

- [x] Aggiungere controlli SAST Python mirati via AST per `eval`/`exec`, shell, deserializzazione `pickle`, SQL interpolato e TLS disabilitato; aggiungere probe DAST locali su autenticazione, endpoint pubblici, link foto e CSRF.
- [x] Eseguire i controlli mirati in CI prima della suite backend.
- [ ] Valutare scanner SAST/DAST o audit CVE di dipendenze in un'attività separata solo se approvati; non sono inclusi nei test custom di questo task.
- [ ] Abilitare Dependabot/Renovate o un processo equivalente per aggiornare dipendenze e GitHub Actions; assegnare un responsabile e una scadenza agli aggiornamenti di sicurezza.
- [ ] Valutare lock completo delle dipendenze Python transitive, oltre ai pin delle dipendenze dirette.
- [ ] Aggiungere secret scanning e protezione contro l'introduzione accidentale di `.env`, token o certificati.
- [ ] Limitare i permessi `GITHUB_TOKEN` di ogni workflow al minimo necessario e fissare le GitHub Actions a commit SHA verificati.
- [ ] Aggiungere SAST e scansione delle immagini/container quando il repository introdurrà un'immagine di deployment.
- [ ] Non considerare verdi test e build come prova dell'assenza di CVE; registrare data e risultato delle scansioni.

**Criteri di completamento:** CI produce un report delle dipendenze a ogni PR; vulnerabilità critiche/alte bloccano o richiedono un'eccezione approvata e tracciata; nessun segreto reale nel repository.

### Protezione dei dati e provider AI/social

- [ ] Mappare dati personali e contenuti trattati: account, profili, campagne, foto originali, dati pubblicati, log e backup.
- [ ] Documentare quali campi del profilo e quali foto vengono inviati al provider AI, per quale scopo, in quale regione e con quale retention; verificare condizioni e accordi del provider prima di usare dati reali.
- [ ] Mantenere la minimizzazione dei dati; non inviare al modello contatti o identificativi che non gli servono. Definire avviso/consenso adeguato per l'uso di foto e servizi esterni.
- [ ] Stabilire retention e cancellazione per database, foto, backup, eventi di sicurezza e contatori scaduti; verificare che la retention sia compatibile con gli obblighi di prodotto.
- [ ] Limitare accesso a file originali e backup; verificare cifratura at-rest dell'infrastruttura e cifratura in transito per tutte le connessioni esterne.
- [ ] Verificare che i token Meta e AI non compaiano in errori, log, dump, interfacce o output di test.

**Criteri di completamento:** inventario dati approvato; flussi verso AI/social e retention documentati; un test e una procedura verificano che segreti e dati non necessari non vengano registrati.

## Test di sicurezza da mantenere

I test esistenti di accesso, proxy, sessioni, upload e foto firmate sono una buona base. Integrare o mantenere almeno i seguenti casi:

- [ ] Login: account inesistente, password errata, rate limit per IP/account, concorrenza, guasto DB e risposta senza informazioni enumerabili.
- [ ] Cookie/sessioni: `Secure`, `HttpOnly`, `SameSite`, scadenza inattività e assoluta, logout, revoca, account disabilitato e MFA.
- [ ] Autorizzazione: accesso tra artigiani, escalation di ruolo, IDOR su campagne/foto/post, e accesso negato a ogni endpoint non pubblico.
- [ ] CSRF/CORS: origini ammesse e rifiutate, form multipart, preflight e assenza di CORS wildcard con credenziali.
- [ ] Upload: body oltre limite, MIME e magic bytes discordanti, immagine corrotta, decompression bomb, pixel oltre soglia, nomi/path traversal e pulizia dopo errore.
- [ ] Foto pubbliche: firma/TTL, risposta anonima attesa, cache, `nosniff`, nessuna firma in log e nessun download dopo scadenza.
- [ ] Produzione: segreti di esempio, secret troppo corto, `COOKIE_SECURE=false`, ambiente test e URL media HTTP devono impedire l'avvio.
- [ ] Integrazioni: nessuna rete reale nei test; token AI/Meta assenti da log, eccezioni e risposte; timeout e rate limit dei provider gestiti senza retry incontrollati.
- [ ] Eseguire i test su database di test isolato e verificare che nessun controllo o test possa modificare il DB di produzione.

## Ordine di lavoro consigliato

1. **Prima di staging/pubblicazione reale:** chiudere il follow-up #17, validare la configurazione di produzione e HTTPS, definire la gestione dei segreti e completare i test di autorizzazione/CSRF.
2. **Prima di invitare operatori o artigiani esterni:** MFA operatori/admin, durata assoluta delle sessioni, limiti API/AI e monitoraggio/alerting.
3. **Prima di conservare dati reali su scala:** revisione privacy/provider, protezione e ripristino dei backup, retention, scansioni automatiche dipendenze/segreti e procedura incidenti.

Ogni intervento che cambia il perimetro MVP — per esempio MFA, recupero password o un tetto applicativo alla spesa AI — va prima concordato e registrato nel task/perimetro appropriato. Questo documento non autorizza a modificare funzionalità congelate o roadmap.
