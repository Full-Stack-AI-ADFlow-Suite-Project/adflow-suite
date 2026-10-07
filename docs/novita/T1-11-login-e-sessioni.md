# Novità · T1-11 Login e sessioni

7 ottobre 2026 · corsia 1 · branch `feature/T1-11-13-auth`

## Comportamento
- `POST /api/auth/login` riceve JSON con `email` e `password`, restituisce
  `id`, `email`, `nome`, `ruolo` e imposta il cookie `adflow_sessione`.
- Credenziali errate, email sconosciuta e account inattivo: stesso errore 401.
- `GET /api/auth/me` restituisce la stessa vista pubblica; senza sessione valida: 401.
- `POST /api/auth/logout` revoca il token del browser e cancella il cookie; 204
  anche se il cookie è assente o già revocato.
- Cookie httpOnly, SameSite=Lax, Path=/, Secure quando la richiesta è HTTPS.
  Le risposte riuscite hanno Cache-Control: no-store. Nel DB resta solo SHA-256.
- Verifica scrypt anche per email sconosciute; password e token non sono nei log.

## Scelte da rivedere nel gruppo
Sessione di **8 ore** (scadenza server e Max-Age del cookie). La durata non è
fissata nelle specifiche: è la scelta iniziale del brief, da approvare.
Un nuovo login ruota la sessione indicata dal cookie precedente, anche cambiando
account; le altre sessioni dell'utente restano valide. Login fallito non revoca
una sessione già valida. Un account disattivato non può usare sessioni esistenti.
In produzione il proxy deve presentare correttamente lo schema HTTPS all'app.

## Revisione
Implementazione nuova dalle specifiche, non recuperata dalla patch precedente.
Test CA-01, CA-02, scadenza, revoca, rotazione, account inattivi e flag cookie in
`tests/moduli/accesso/test_auth.py`. Nessuna dipendenza, migrazione o modifica
alla corsia 0. La chiusura formale richiede revisione del gruppo e merge admin.
