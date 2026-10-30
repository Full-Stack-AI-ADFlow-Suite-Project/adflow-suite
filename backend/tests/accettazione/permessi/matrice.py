"""Matrice dei permessi di tutte le 57 operazioni dell'API (T4-102, corsia 10).

L'esito atteso di ogni cella viene da costituzione §3 («Permessi controllati
sul server a ogni richiesta: 401 senza sessione, 403 ruolo, 404 per risorse di
un altro artigiano. L'admin passa dove passa l'operatore») e da `spec.md`
(R-29, R-45…R-50, §4), **non** dal comportamento attuale del codice: dove il
codice differisce, la differenza diventa un rilievo del registro e la cella va
marcata `xfail(strict=True)` nel test.

Ruoli della matrice: `anonimo`, `artigiano_a` (proprietario delle risorse
usate nelle sonde), `artigiano_b` (l'altra bottega), `operatore`, `admin`.

Codici attesi per cella:

- `AMMESSO`: il permesso c'è. La risposta può essere 2xx, 409 (stato che non
  cambia nulla) o 422 (corpo della sonda non completo): la matrice prova i
  permessi, non la logica di stato. Un 500 è sempre un errore.
- `"401"`, `"403"`, `"404"`: rifiuto atteso, con il motivo della costituzione.

Scelte delle righe, dalla spec:

- `POST /auth/login`, `GET /health`, `GET /consorzio`, `GET /foto/{id}/pubblica`
  (firma): pubbliche (R-29: contatto e foto con firma leggibili senza sessione).
- `POST /auth/logout`: senza sessione è un no-op che non rivela nulla (204 e
  cancellazione del cookie): ammesso per tutti.
- Elenchi senza id (`GET /campagne`, `GET /archivio-foto`, `GET /calendario`):
  ogni ruolo ammesso vede il suo (artigiano) o tutto (operatore, admin).
- `GET /campagne/{id}`, `GET /campagne/{id}/calendario`, `GET /foto/{id}/file`:
  il proprietario e l'operatore (R-45: «lo leggono il proprietario e
  l'operatore»; l'operatore vede foto e calendari in Vedi campagna e archivio).
- Le rotte congelate `/api/archivio…` (D-06): l'atteso è quello del codice
  congelato, artigiano sulla propria bottega; un difetto lì è un rilievo
  «roadmap».
"""

from __future__ import annotations

AMMESSO = "ammesso"

RUOLI = ("anonimo", "artigiano_a", "artigiano_b", "operatore", "admin")


def _celle(anonimo, artigiano_a, artigiano_b, operatore, admin) -> dict[str, str]:
    return {
        "anonimo": anonimo,
        "artigiano_a": artigiano_a,
        "artigiano_b": artigiano_b,
        "operatore": operatore,
        "admin": admin,
    }


def _pubblica() -> dict[str, str]:
    return _celle(AMMESSO, AMMESSO, AMMESSO, AMMESSO, AMMESSO)


def _autenticato() -> dict[str, str]:
    """Serve una sessione, poi il ruolo non conta: ognuno vede il suo."""
    return _celle("401", AMMESSO, AMMESSO, AMMESSO, AMMESSO)


def _artigiano_elenco() -> dict[str, str]:
    """Elenco o creazione senza id: solo artigiani, ognuno per sé (R-29)."""
    return _celle("401", AMMESSO, AMMESSO, "403", "403")


def _artigiano_risorsa() -> dict[str, str]:
    """Risorsa con id di A: A sì, B 404 (costituzione §3), operatori 403."""
    return _celle("401", AMMESSO, "404", "403", "403")


def _proprietario_e_operatore() -> dict[str, str]:
    """Lettura di una risorsa di A: A e operatori sì (R-45, §4), B 404."""
    return _celle("401", AMMESSO, "404", AMMESSO, AMMESSO)


def _artigiano_e_operatore() -> dict[str, str]:
    """Elenco condiviso: artigiani per sé e operatori per tutti (R-47, R-48)."""
    return _celle("401", AMMESSO, AMMESSO, AMMESSO, AMMESSO)


def _operatore() -> dict[str, str]:
    """Solo operatori (l'admin passa dove passa l'operatore, costituzione §3)."""
    return _celle("401", "403", "403", AMMESSO, AMMESSO)


MATRICE: dict[tuple[str, str], dict[str, str]] = {
    # pubbliche
    ("post", "/api/auth/login"): _pubblica(),
    ("get", "/api/health"): _pubblica(),
    ("get", "/api/consorzio"): _pubblica(),
    ("get", "/api/foto/{id}/pubblica"): _pubblica(),  # firma valida nella sonda
    # sessione
    ("post", "/api/auth/logout"): _pubblica(),  # no-op senza sessione
    ("get", "/api/auth/me"): _autenticato(),
    # campagne ed elenchi
    ("get", "/api/campagne"): _autenticato(),
    ("post", "/api/campagne"): _artigiano_elenco(),
    ("get", "/api/campagne/{id}"): _proprietario_e_operatore(),
    ("patch", "/api/campagne/{id}"): _artigiano_risorsa(),
    ("get", "/api/campagne/{id}/calendario"): _proprietario_e_operatore(),
    ("post", "/api/campagne/{id}/gruppi"): _artigiano_risorsa(),
    ("put", "/api/campagne/{id}/gruppi/{gruppo_id}"): _artigiano_risorsa(),
    ("delete", "/api/campagne/{id}/gruppi/{gruppo_id}"): _artigiano_risorsa(),
    ("post", "/api/campagne/{id}/foto"): _artigiano_risorsa(),
    ("delete", "/api/foto/{id}"): _artigiano_risorsa(),
    ("post", "/api/campagne/{id}/invia"): _artigiano_risorsa(),
    ("get", "/api/foto/{id}/file"): _proprietario_e_operatore(),
    # richiesta all'artigiano (R-46)
    ("post", "/api/campagne/{id}/richiesta"): _operatore(),
    ("post", "/api/campagne/{id}/richiesta/foto"): _artigiano_risorsa(),
    ("post", "/api/campagne/{id}/richiesta/invia"): _artigiano_risorsa(),
    # profilo e canali
    ("get", "/api/profilo"): _artigiano_elenco(),
    ("put", "/api/profilo"): _artigiano_elenco(),
    ("get", "/api/canali"): _artigiano_elenco(),
    # rotte congelate dell'archivio (D-06: provate senza modificarle)
    ("get", "/api/archivio"): _artigiano_elenco(),
    ("post", "/api/archivio/gruppi"): _artigiano_elenco(),
    ("post", "/api/archivio/foto"): _artigiano_risorsa(),  # gruppo di A nel corpo
    ("delete", "/api/archivio/foto/{id}"): _artigiano_risorsa(),
    ("delete", "/api/archivio/gruppi/{id}"): _artigiano_risorsa(),
    # archivio foto in sola lettura e calendario settimanale (R-47, R-48)
    ("get", "/api/archivio-foto"): _artigiano_e_operatore(),
    ("get", "/api/calendario"): _artigiano_e_operatore(),
    # revisione e interventi: solo operatori
    ("get", "/api/da-approvare"): _operatore(),
    ("get", "/api/artigiani"): _operatore(),
    ("post", "/api/artigiani"): _operatore(),
    ("get", "/api/artigiani/{utente_id}"): _operatore(),
    ("get", "/api/campagne/{campagna_id}/post"): _operatore(),
    ("post", "/api/campagne/{campagna_id}/approva"): _operatore(),
    ("post", "/api/campagne/{campagna_id}/respingi"): _operatore(),
    ("post", "/api/campagne/{campagna_id}/sospendi"): _operatore(),
    ("post", "/api/campagne/{campagna_id}/riattiva"): _operatore(),
    ("post", "/api/campagne/{campagna_id}/annulla"): _operatore(),
    ("post", "/api/campagne/{campagna_id}/nota"): _operatore(),
    ("post", "/api/campagne/{campagna_id}/togli-canale"): _operatore(),
    ("post", "/api/campagne/{id}/riprova"): _operatore(),
    ("post", "/api/post/{post_id}/modifica"): _operatore(),
    ("post", "/api/post/{post_id}/controllato"): _operatore(),
    ("post", "/api/post/{post_id}/rigenera"): _operatore(),
    ("post", "/api/post/{post_id}/rigenera-immagine"): _operatore(),
    ("post", "/api/post/{post_id}/riprogramma"): _operatore(),
    ("post", "/api/post/{post_id}/sposta"): _operatore(),
    ("post", "/api/post/{post_id}/annulla"): _operatore(),
    ("post", "/api/post/{post_id}/cambia-foto"): _operatore(),
    ("get", "/api/post/{post_id}/foto-possibili"): _operatore(),
    # storico AI (R-50: l'operatore la legge)
    ("get", "/api/storico-ai"): _operatore(),
    ("get", "/api/storico-ai/numeri"): _operatore(),
    ("get", "/api/storico-ai/{id}"): _operatore(),
    ("post", "/api/storico-ai/{id}/voto"): _operatore(),
}

assert len(MATRICE) == 57, f"la matrice deve avere 57 operazioni, ne ha {len(MATRICE)}"
