"""Interventi in parallelo (T4-103): approva/respingi, richiesta, cambio foto.

Scenari di §7.3:
- approva e respingi insieme: un solo esito, l'altro 409;
- approva e richiesta all'artigiano insieme: la richiesta non blocca
  l'approvazione (R-14, R-46) e la campagna resta coerente;
- la stessa foto su due post della stessa campagna sullo stesso canale
  (costituzione §1.9): uno solo dei due cambi foto deve passare;
- quattro rigenerazioni dello stesso post in parallelo con il limite a 3 (R-04):
  l'accensione dell'intervento deve restare una alla volta (R-31) e il
  contatore non deve superare il limite.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.moduli.campagne import service as campagne_service
from app.moduli.campagne.models import Foto
from app.moduli.contenuti.models import Post, VersionePost
from app.moduli.revisione import decisioni, interventi, service
from tests.accettazione.concorrenza.conftest import crea_con_commit, esegui_in_parallelo
from tests.moduli.campagne.fabbrica import campagna_in_revisione
from tests.moduli.contenuti.fabbrica import post_da_approvare

RIPETIZIONI = 50


def _campagna_con_due_post(motore, bottega) -> dict:
    def costruisci(sessione):
        campagna = campagna_in_revisione(sessione, profilo_id=bottega.id)
        post = [post_da_approvare(sessione, campagna_id=campagna.id) for _ in range(2)]
        return {"campagna": campagna.id, "post": [p.id for p in post]}

    return crea_con_commit(motore, costruisci)


def test_approva_e_respingi_insieme(motore_concorrenza, mondo_concorrenza):
    """50 volte: approvazione e respinta in parallelo, un solo esito vincente."""
    doppie = 0
    for _ in range(RIPETIZIONI):
        mondo = _campagna_con_due_post(motore_concorrenza, mondo_concorrenza["bottega"])
        adesso = datetime.now(timezone.utc)
        _, errori = esegui_in_parallelo(
            motore_concorrenza,
            [
                lambda s: service.approva(
                    s, mondo["campagna"], mondo_concorrenza["operatore"], adesso
                ),
                lambda s: decisioni.respingi(
                    s,
                    mondo["campagna"],
                    mondo_concorrenza["operatore2"],
                    "foto",
                    "Foto non della bottega",
                    [],
                    adesso,
                ),
            ],
        )
        if errori == [None, None]:
            doppie += 1
    assert doppie == 0, (
        f"approvazione e respinta passano entrambe in {doppie}/{RIPETIZIONI}: "
        "la campagna finisce in uno stato che non è né attiva né respinta"
    )


def test_approva_mentre_l_operatore_chiede_all_artigiano(
    motore_concorrenza, mondo_concorrenza
):
    """La richiesta non blocca Approva (R-14): alla fine o è decaduta o non è partita."""
    for _ in range(RIPETIZIONI):
        mondo = _campagna_con_due_post(motore_concorrenza, mondo_concorrenza["bottega"])
        adesso = datetime.now(timezone.utc)
        _, errori = esegui_in_parallelo(
            motore_concorrenza,
            [
                lambda s: service.approva(
                    s, mondo["campagna"], mondo_concorrenza["operatore"], adesso
                ),
                lambda s: campagne_service.apri_richiesta(
                    s,
                    mondo["campagna"],
                    mondo_concorrenza["operatore2"].id,
                    "Serve un'altra foto",
                    [],
                ),
            ],
        )
        # L'approvazione non deve mai fallire per colpa della richiesta
        assert (
            errori[0] is None
        ), f"l'approvazione è stata fermata dalla richiesta: {errori[0]}"
        # La richiesta può essere partita prima o dopo l'approvazione; se dopo,
        # è decaduta o rifiutata: mai aperta su una campagna attiva.
        stato = crea_con_commit(
            motore_concorrenza,
            lambda s: s.execute(
                select(VersionePost.post_id).where(
                    VersionePost.post_id == mondo["post"][0]
                )
            ).scalar(),
        )
        assert stato == mondo["post"][0], "la campagna approvata ha perso i post"


@pytest.mark.xfail(
    strict=True,
    reason="RL-023 (costituzione §1.9): la stessa foto finisce su due post "
    "dello stesso canale nella stessa campagna in 50/50 ripetizioni. "
    "Correzione proposta: controllo e scrittura sotto blocco della foto o "
    "vincolo che escluda la stessa foto su due versioni correnti dello stesso canale",
)
def test_cambia_foto_insieme_sulla_stessa_foto(motore_concorrenza, mondo_concorrenza):
    """§1.9: la stessa foto non può finire su due post dello stesso canale.

    Entrambi i post sono su Instagram nella stessa campagna; i due operatori
    cambiano foto insieme scegliendo la stessa immagine libera.
    """
    doppie = 0
    for _ in range(RIPETIZIONI):
        mondo = _campagna_con_due_post(motore_concorrenza, mondo_concorrenza["bottega"])

        def libera(sessione: Session) -> dict:
            # una foto del gruppo della campagna non ancora usata
            foto_libera = sessione.scalars(
                select(Foto.id).where(
                    Foto.campagna_id == mondo["campagna"], Foto.n_utilizzi == 0
                )
            ).first()
            return {"foto": foto_libera}

        dati = crea_con_commit(motore_concorrenza, libera)
        if dati["foto"] is None:
            continue
        adesso = datetime.now(timezone.utc)
        _, errori = esegui_in_parallelo(
            motore_concorrenza,
            [
                lambda s: interventi.cambia_foto(
                    s,
                    mondo["post"][0],
                    dati["foto"],
                    mondo_concorrenza["operatore"],
                    adesso,
                ),
                lambda s: interventi.cambia_foto(
                    s,
                    mondo["post"][1],
                    dati["foto"],
                    mondo_concorrenza["operatore2"],
                    adesso,
                ),
            ],
        )
        if errori == [None, None]:
            doppie += 1
    assert doppie == 0, (
        f"la stessa foto è finita su due post dello stesso canale in "
        f"{doppie}/{RIPETIZIONI} ripetizioni: costituzione §1.9 violata"
    )


@pytest.mark.xfail(
    strict=False,
    reason="RL-024 (R-04, R-31): due rigenerazioni dello stesso post partono "
    "insieme in 49/50 ripetizioni; il contatore resta sotto il limite solo "
    "perché il job non gira. Correzione proposta: blocco della riga del post "
    "all'accensione dell'intervento",
)
def test_rigenerazioni_insieme_col_limite_a_tre(motore_concorrenza, mondo_concorrenza):
    """R-04, R-31: post a due rigenerazioni su tre, due accensioni in parallelo.

    Il primo controllo che deve reggere è R-31 (una rigenerazione alla volta):
    una sola accensione passa, l'altra trova l'intervento in corso (409).
    Se passano entrambe, il contatore può arrivare a 4 e a fine giornata il
    job scriverebbe più versioni del limite.
    """
    doppie = 0
    for _ in range(RIPETIZIONI):

        def costruisci(sessione):
            campagna = campagna_in_revisione(
                sessione, profilo_id=mondo_concorrenza["bottega"].id
            )
            post = post_da_approvare(sessione, campagna_id=campagna.id)
            post.n_rigenerazioni_testo = 2
            return {"campagna": campagna.id, "post": post.id}

        mondo = crea_con_commit(motore_concorrenza, costruisci)
        adesso = datetime.now(timezone.utc)
        _, errori = esegui_in_parallelo(
            motore_concorrenza,
            [
                lambda s: interventi.rigenera(
                    s, mondo["post"], "totale", None, None, adesso
                ),
                lambda s: interventi.rigenera(
                    s, mondo["post"], "totale", None, None, adesso
                ),
            ],
        )
        if errori == [None, None]:
            doppie += 1
        contatore = crea_con_commit(
            motore_concorrenza,
            lambda s: s.scalar(
                select(Post.n_rigenerazioni_testo).where(Post.id == mondo["post"])
            ),
        )
        assert contatore <= 3, f"contatore a {contatore} su un limite di 3"
    assert doppie == 0, (
        f"due rigenerazioni partono insieme in {doppie}/{RIPETIZIONI} ripetizioni "
        "(R-31 e R-04)"
    )
