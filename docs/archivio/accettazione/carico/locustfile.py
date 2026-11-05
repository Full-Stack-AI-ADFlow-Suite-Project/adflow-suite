"""Carico di accettazione su AdFlow (T4-105, §7.2).

Si lancia **solo** su un'API in locale collegata al database dedicato
`adflow_accettazione` (mai `adflow` o `adflow_test`), con `SOCIAL_PROVIDER` e
`AI_PROVIDER` finti. I dati si preparano con le `fabbrica.py` dei moduli
(vedi README.md in questa cartella).

    AZURE... niente: tutto in locale.
    BASE_URL=http://127.0.0.1:8905 \
    EMAIL_ARTIGIANO=demo@example.com PASSWORD=... \
    uvx locust -f docs/accettazione/carico/locustfile.py --headless \
        -u 10 -r 2 -t 60s --host $BASE_URL

Numeri ipotizzati (D-01 della proposta, dichiarati come ipotesi, non misure):
200 consorzi, 2 000 artigiani, 8 operatori, 400 campagne al mese, 60 post al
giorno, 12 foto per campagna. Obiettivi di servizio di partenza: p95 < 300 ms
per le letture, < 1 s per le scritture, errori < 0,1 %, ritardo di
pubblicazione < 2 minuti.
"""

from __future__ import annotations

import os
import random

from locust import HttpUser, between, task

EMAIL_ARTIGIANO = os.environ.get("EMAIL_ARTIGIANO", "artigiano@example.com")
EMAIL_OPERATORE = os.environ.get("EMAIL_OPERATORE", "operatore@example.com")
PASSWORD = os.environ.get("PASSWORD", "")


class _ConAccesso(HttpUser):
    abstract = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.campagne: list[int] = []

    def accedi(self, email: str) -> None:
        risposta = self.client.post(
            "/api/auth/login", json={"email": email, "password": PASSWORD}, name="login"
        )
        if risposta.status_code != 200:
            raise RuntimeError(f"accesso fallito per {email}: {risposta.status_code}")


class Artigiano(HttpUser):
    """Il lavoro dell'artigiano: ingresso, campagne, calendario, archivio."""

    wait_time = between(1, 4)

    def on_start(self) -> None:
        self.accedi(EMAIL_ARTIGIANO)
        risposta = self.client.get("/api/campagne", name="GET /campagne")
        if risposta.status_code == 200:
            self.campagne = [c["id"] for c in risposta.json()]

    def accedi(self, email: str) -> None:
        risposta = self.client.post(
            "/api/auth/login", json={"email": email, "password": PASSWORD}, name="login"
        )
        if risposta.status_code != 200:
            raise RuntimeError(f"accesso fallito per {email}: {risposta.status_code}")

    @task(4)
    def campagne(self) -> None:
        self.client.get("/api/campagne", name="GET /campagne")

    @task(2)
    def profilo_e_canali(self) -> None:
        self.client.get("/api/profilo", name="GET /profilo")
        self.client.get("/api/canali", name="GET /canali")

    @task(2)
    def calendario(self) -> None:
        self.client.get("/api/calendario", name="GET /calendario")

    @task(2)
    def archivio(self) -> None:
        self.client.get("/api/archivio-foto", name="GET /archivio-foto")

    @task(1)
    def dettaglio(self) -> None:
        if not self.campagne:
            return
        campagna = random.choice(self.campagne)
        self.client.get(f"/api/campagne/{campagna}", name="GET /campagne/{id}")


class Operatore(HttpUser):
    """Il lavoro dell'operatore: campagne da approvare, artigiani, storico AI."""

    wait_time = between(1, 3)

    def on_start(self) -> None:
        self.accedi(EMAIL_OPERATORE)
        risposta = self.client.get("/api/da-approvare", name="GET /da-approvare")
        if risposta.status_code == 200:
            self.da_approvare = [c["id"] for c in risposta.json()]
        else:
            self.da_approvare = []

    def accedi(self, email: str) -> None:
        risposta = self.client.post(
            "/api/auth/login", json={"email": email, "password": PASSWORD}, name="login"
        )
        if risposta.status_code != 200:
            raise RuntimeError(f"accesso fallito per {email}: {risposta.status_code}")

    @task(4)
    def da_approvare(self) -> None:
        self.client.get("/api/da-approvare", name="GET /da-approvare")

    @task(3)
    def artigiani(self) -> None:
        risposta = self.client.get("/api/artigiani", name="GET /artigiani")
        if risposta.status_code == 200 and risposta.json():
            scelto = random.choice(risposta.json())
            self.client.get(
                f"/api/artigiani/{scelto['utente_id']}", name="GET /artigiani/{id}"
            )

    @task(3)
    def vedi_campagna(self) -> None:
        if not self.da_approvare:
            return
        campagna = random.choice(self.da_approvare)
        self.client.get(
            f"/api/campagne/{campagna}/post", name="GET /campagne/{id}/post"
        )

    @task(2)
    def storico_ai(self) -> None:
        self.client.get("/api/storico-ai", name="GET /storico-ai")
        self.client.get("/api/storico-ai/numeri", name="GET /storico-ai/numeri")

    @task(1)
    def calendario(self) -> None:
        self.client.get("/api/calendario", name="GET /calendario")
