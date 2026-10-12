from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errori import DatiNonValidi, NonTrovato
from app.core.coda import INVIA_NOTIFICA
from app.moduli.notifiche import domain, service
from app.moduli.notifiche.models import Notifica
from tests.moduli.accesso.fabbrica import utente
from tests.moduli.artigiani.fabbrica import profilo
from tests.moduli.campagne.fabbrica import campagna_in_bozza
from tests.moduli.contenuti.fabbrica import post_da_approvare
from tests.moduli.notifiche.fabbrica import notifica

ORA = datetime(2030, 1, 5, 12, tzinfo=timezone.utc)


def jobs(coda):
    return [(j["task_name"], j["args"]) for j in coda.jobs.values()]


def conta(db):
    return db.scalar(select(func.count()).select_from(Notifica))


@pytest.mark.parametrize("tipo", domain.TIPI)
def test_destinatari_e_job_per_ogni_tipo_di_notifica(db, coda, tipo):
    artigiano = utente(db)
    bottega = profilo(db, utente_id=artigiano.id)
    campagna = campagna_in_bozza(db, profilo_id=bottega.id)
    operatore = utente(db, "operatore")
    admin = utente(db, "admin")
    utente(db, "operatore", attivo=False)
    utente(db, "admin", attivo=False)
    utente(db, "artigiano")
    post = post_da_approvare(db, campagna_id=campagna.id)
    nuove = service.crea(
        db, tipo, campagna.id, ORA, artigiano_id=artigiano.id, post_id=post.id
    )
    attesi = (
        [artigiano.id]
        if domain.DESTINATARI[tipo] == domain.ARTIGIANO
        else [operatore.id, admin.id]
    )
    assert [n.utente_id for n in nuove] == attesi
    for n in nuove:
        assert n.campagna_id == campagna.id and n.tipo == tipo
        assert n.canale == "email" and n.stato_invio == "da_inviare"
        assert n.creata_il == ORA and n.inviata_il is None
        assert n.post_id == (post.id if tipo in domain.TIPI_DI_UN_POST else None)
    assert jobs(coda) == [(INVIA_NOTIFICA, {"notifica_id": n.id}) for n in nuove]
    assert (
        service.crea(
            db,
            tipo,
            campagna.id,
            ORA + timedelta(hours=1),
            artigiano_id=artigiano.id,
            post_id=post.id,
        )
        == []
    )
    assert conta(db) == len(attesi) and len(jobs(coda)) == len(attesi)


@pytest.mark.parametrize(
    "tipo,kwargs",
    [
        ("sconosciuta", {}),
        ("campagna_respinta", {}),
        ("campagna_scaduta", {}),
        ("post_fallito", {}),
    ],
)
def test_dati_mancanti_o_tipo_errato_non_scrive_e_non_accoda(db, coda, tipo, kwargs):
    c = campagna_in_bozza(db)
    with pytest.raises(DatiNonValidi):
        service.crea(db, tipo, c.id, ORA, **kwargs)
    assert conta(db) == 0 and jobs(coda) == []


def test_istante_senza_fuso_non_scrive(db, coda):
    c = campagna_in_bozza(db)
    with pytest.raises(DatiNonValidi, match="fuso orario"):
        service.crea(db, "campagna_pronta", c.id, ORA.replace(tzinfo=None))
    assert conta(db) == 0 and jobs(coda) == []


def test_artigiano_inesistente_o_ruolo_errato(db, coda):
    c = campagna_in_bozza(db)
    with pytest.raises(NonTrovato):
        service.crea(db, "campagna_respinta", c.id, ORA, artigiano_id=-1)
    operatore = utente(db, "operatore")
    with pytest.raises(DatiNonValidi, match="artigiano"):
        service.crea(db, "campagna_respinta", c.id, ORA, artigiano_id=operatore.id)
    assert conta(db) == 0 and jobs(coda) == []


def test_evento_senza_operatori_e_parametri_non_pertinenti_ignorati(db, coda):
    c = campagna_in_bozza(db)
    assert (
        service.crea(db, "campagna_pronta", c.id, ORA, artigiano_id=-1, post_id=-1)
        == []
    )
    op = utente(db, "operatore")
    nuove = service.crea(db, "campagna_pronta", c.id, ORA, artigiano_id=-1, post_id=-1)
    assert [n.utente_id for n in nuove] == [op.id] and nuove[0].post_id is None


@pytest.mark.parametrize("stato", domain.STATI_INVIO)
def test_notifica_precedente_anche_fallita_non_viene_riaccodata(db, coda, stato):
    c = campagna_in_bozza(db)
    op = utente(db, "operatore")
    vecchia = notifica(db, campagna=c, utente=op, stato_invio=stato, creata_il=ORA)
    assert service.crea(db, "campagna_pronta", c.id, ORA + timedelta(days=1)) == []
    db.refresh(vecchia)
    assert vecchia.stato_invio == stato and vecchia.creata_il == ORA
    assert jobs(coda) == []


def test_nuovo_operatore_riceve_evento_non_duplicato_per_gli_altri(db, coda):
    c = campagna_in_bozza(db)
    op = utente(db, "operatore")
    prime = service.crea(db, "campagna_pronta", c.id, ORA)
    admin = utente(db, "admin")
    seconde = service.crea(db, "campagna_pronta", c.id, ORA)
    assert [n.utente_id for n in prime] == [op.id]
    assert [n.utente_id for n in seconde] == [admin.id]
    assert conta(db) == 2 and len(jobs(coda)) == 2


def test_post_campagne_e_tipi_diversi_sono_eventi_distinti(db, coda):
    utente(db, "operatore")
    c1, c2 = campagna_in_bozza(db), campagna_in_bozza(db)
    p1 = post_da_approvare(db, campagna_id=c1.id)
    p2 = post_da_approvare(db, campagna_id=c1.id)
    righe = []
    for c, tipo, post in [
        (c1, "campagna_pronta", None),
        (c1, "piano_da_rivedere", None),
        (c2, "campagna_pronta", None),
        (c1, "post_fallito", p1.id),
        (c1, "post_fallito", p2.id),
    ]:
        righe.extend(service.crea(db, tipo, c.id, ORA, post_id=post))
    assert len(righe) == conta(db) == len(jobs(coda)) == 5


def test_flush_di_tutte_le_righe_prima_del_primo_job(db, monkeypatch):
    c = campagna_in_bozza(db)
    utente(db, "operatore")
    utente(db, "admin")
    visti = []

    def accoda(nome, **argomenti):
        with db.no_autoflush:
            assert conta(db) == 2
            assert db.get(Notifica, argomenti["notifica_id"]) is not None
        assert nome == INVIA_NOTIFICA
        visti.append(argomenti["notifica_id"])

    monkeypatch.setattr(service, "accoda", accoda)
    righe = service.crea(db, "campagna_pronta", c.id, ORA)
    assert visti == [n.id for n in righe]


def test_errore_del_flush_non_accoda(db, coda):
    utente(db, "operatore")
    with pytest.raises(IntegrityError), db.begin_nested():
        service.crea(db, "campagna_pronta", -1, ORA)
    assert jobs(coda) == [] and conta(db) == 0


def test_errore_della_coda_consente_rollback_al_chiamante(db, monkeypatch):
    c = campagna_in_bozza(db)
    utente(db, "operatore")

    def fallisce(*args, **kwargs):
        raise RuntimeError("Coda non disponibile")

    monkeypatch.setattr(service, "accoda", fallisce)
    with pytest.raises(RuntimeError), db.begin_nested():
        service.crea(db, "campagna_pronta", c.id, ORA)
    assert conta(db) == 0


def test_notifiche_concorrenti_non_creano_doppioni(motore_test, monkeypatch):
    # Connessioni vere e transazioni indipendenti, tutte su adflow_test.
    with Session(motore_test) as preparazione, preparazione.begin():
        artigiano = utente(preparazione)
        bottega = profilo(preparazione, utente_id=artigiano.id, canali=[])
        c = campagna_in_bozza(preparazione, profilo_id=bottega.id)
        op = utente(preparazione, "operatore")
        campagna_id, operatore_id = c.id, op.id
    accodati = []
    monkeypatch.setattr(
        service, "accoda", lambda nome, **kw: accodati.append((nome, kw))
    )

    def crea(numero):
        with Session(motore_test) as sessione, sessione.begin():
            return [
                n.id
                for n in service.crea(sessione, "campagna_pronta", campagna_id, ORA)
            ]

    try:
        with ThreadPoolExecutor(max_workers=4) as pool:
            risultati = list(pool.map(crea, range(4)))
        assert sum(map(len, risultati)) == 1 and len(accodati) == 1
        with Session(motore_test) as controllo:
            righe = list(
                controllo.scalars(
                    select(Notifica).where(Notifica.campagna_id == campagna_id)
                )
            )
            assert len(righe) == 1 and righe[0].utente_id == operatore_id
    finally:
        # I commit delle connessioni concorrenti non sono nella transazione
        # della fixture db: eliminiamo esclusivamente i dati creati qui.
        with Session(motore_test) as pulisci, pulisci.begin():
            pulisci.execute(delete(Notifica).where(Notifica.campagna_id == campagna_id))
            pulisci.delete(pulisci.merge(c))
            pulisci.flush()
            pulisci.delete(pulisci.merge(bottega))
            pulisci.flush()
            pulisci.delete(pulisci.merge(artigiano))
            pulisci.delete(pulisci.merge(op))
