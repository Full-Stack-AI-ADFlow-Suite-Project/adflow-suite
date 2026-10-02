"""Riga di comando: seed dei dati di partenza e creazione di un utente.

Da ``backend/``::

    python -m app.cli seed
    python -m app.cli crea-utente --email E --nome N --ruolo artigiano|operatore|admin

La password si chiede a terminale: non passa dagli argomenti né finisce in git.
"""

import argparse
import sys
from collections.abc import Sequence
from getpass import getpass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import transazione
from app.core.errori import ErroreDominio
from app.core.security import hash_password
from app.moduli.accesso.models import Utente
from app.moduli.accesso.service import crea_utente
from app.moduli.artigiani.models import ProfiloBottega

UTENTI_SEED = (
    ("artigiano@example.com", "Marta Bianchi", "artigiano"),
    ("operatore@example.com", "Operatore del consorzio", "operatore"),
    ("admin@example.com", "Amministratore", "admin"),
)

# Profilo completo dell'artigiano del seed, con i valori ammessi di plan §2.
PROFILO_SEED = dict(
    nome="Ceramiche Bianchi",
    referente="Marta Bianchi",
    citta="Deruta",
    anni_attivita=28,
    sito="https://ceramichebianchi.example.com",
    storia="Bottega di famiglia: tre generazioni al tornio, ogni pezzo dipinto a mano.",
    origine="Fondata dal nonno nel dopoguerra, nel centro storico di Deruta.",
    valori=["artigianalita", "tradizione", "territorio"],
    tipo_prodotto="ceramica_vetro",
    gamma="Piatti, vasi e servizi da tavola in maiolica decorata.",
    fascia_prezzo="media",
    stagionalita="Più richieste a Natale e nella stagione dei matrimoni.",
    clienti_ideali="Coppie e famiglie che cercano oggetti per la casa fatti a mano.",
    obiettivo="notorieta",
    zona="Umbria e Italia centrale",
    tono=["caldo", "professionale"],
    cortesia="tu",
    vincoli="Non parlare di sconti; non citare altri marchi.",
    canali=["facebook", "instagram"],
    frequenza="f3_4",
    social_esistenti={
        "canali": ["facebook"],
        "profili": "facebook.com/ceramichebianchi.example",
        "cosa_funziona": "Le foto dei pezzi appena usciti dal forno.",
    },
    foto_policy={
        "quantita_mese": "da5_a12",
        "chi_scatta": "artigiano",
        "persone": "con_consenso",
    },
    eventi_ricorrenti=[
        {
            "nome": "Mercatino di Natale",
            "quando": "dicembre",
            "tipo": "fiera_mercatino",
        }
    ],
    chiusure="Due settimane ad agosto.",
)


def esegui_seed(db: Session, password: str) -> list[str]:
    """Crea artigiano (con profilo), operatore e admin; restituisce le email create.

    Si può rilanciare: ciò che esiste già resta com'è, password compresa.
    """
    password_hash = hash_password(password)
    creati = []
    for email, nome, ruolo in UTENTI_SEED:
        utente = db.scalar(select(Utente).where(Utente.email == email))
        if utente is None:
            utente = Utente(
                email=email, password_hash=password_hash, nome=nome, ruolo=ruolo
            )
            db.add(utente)
            db.flush()
            creati.append(email)
        if ruolo == "artigiano":
            profilo = db.scalar(
                select(ProfiloBottega).where(ProfiloBottega.utente_id == utente.id)
            )
            if profilo is None:
                db.add(ProfiloBottega(utente_id=utente.id, **PROFILO_SEED))
                db.flush()
    return creati


def _chiedi_password(etichetta: str) -> str:
    password = getpass(f"{etichetta}: ")
    if not password:
        raise SystemExit("La password non può essere vuota.")
    if getpass("Ripeti la password: ") != password:
        raise SystemExit("Le due password non coincidono.")
    return password


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m app.cli", description=__doc__)
    comandi = parser.add_subparsers(dest="comando", required=True)
    comandi.add_parser("seed", help="artigiano con profilo, operatore e admin")
    nuovo = comandi.add_parser("crea-utente", help="crea un utente")
    nuovo.add_argument("--email", required=True)
    nuovo.add_argument("--nome", required=True)
    nuovo.add_argument(
        "--ruolo", required=True, choices=("artigiano", "operatore", "admin")
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    argomenti = _parser().parse_args(argv)
    try:
        if argomenti.comando == "seed":
            password = _chiedi_password("Password per gli utenti del seed")
            with transazione() as db:
                creati = esegui_seed(db, password)
            for email, _, ruolo in UTENTI_SEED:
                esito = "creato" if email in creati else "già presente"
                print(f"{ruolo}: {email} ({esito})")
        else:
            password = _chiedi_password("Password del nuovo utente")
            with transazione() as db:
                utente = crea_utente(
                    db, argomenti.email, password, argomenti.nome, argomenti.ruolo
                )
                print(f"{utente.ruolo}: {utente.email} (creato)")
    except ErroreDominio as errore:
        print(errore.messaggio, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
