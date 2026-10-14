"""Riga di comando: seed dei dati di partenza e creazione di un utente.

Da ``backend/``::

    python -m app.cli seed
    python -m app.cli crea-utente --email E --nome N --ruolo artigiano|operatore|admin
    python -m app.cli cambia-password --email E
    python -m app.cli prova-ai --campagna ID

La password si chiede a terminale: non passa dagli argomenti né finisce in git.

``prova-ai`` genera una campagna `inviata` con il provider scelto in
``backend/.env`` (``AI_PROVIDER=litellm`` per quello vero) e stampa cosa ha
fatto e speso l'AI: è la prova su 10 post di T3-32, da ripetere per ogni modello.
"""

import argparse
import sys
import time
import traceback
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from getpass import getpass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import leggi_impostazioni
from app.core.db import transazione
from app.core.errori import ErroreDominio
from app.core.orologio import adesso
from app.core.security import hash_password
from app.moduli.accesso.models import Utente
from app.moduli.accesso.service import crea_utente, cambia_password
from app.moduli.artigiani.models import ProfiloBottega, AccountSocial
from app.moduli.campagne import service as campagne
from app.moduli.campagne.domain import INVIATA, IN_GENERAZIONE
from app.moduli.contenuti import generazione
from app.moduli.contenuti.schemas import RiepilogoAI
from app.moduli.contenuti.service import riepilogo_ai_della_campagna

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
                profilo = ProfiloBottega(utente_id=utente.id, **PROFILO_SEED)
                db.add(profilo)
                db.flush()
            for piattaforma in ("facebook", "instagram"):
                account = db.scalar(
                    select(AccountSocial).where(
                        AccountSocial.profilo_id == profilo.id,
                        AccountSocial.piattaforma == piattaforma,
                    )
                )
                if account is None:
                    db.add(
                        AccountSocial(
                            profilo_id=profilo.id,
                            piattaforma=piattaforma,
                            id_pagina=f"{piattaforma}-pagina-seed-finta",
                            stato="collegato",
                        )
                    )
            db.flush()
    return creati


@dataclass
class EsitoProva:
    """Com'è andata una prova: tempo, stato finale, errore se c'è, riepilogo dell'AI."""

    campagna_id: int
    titolo: str
    secondi: float
    stato: str
    errore: str | None
    riepilogo: RiepilogoAI


def esegui_prova_ai(
    campagna_id: int,
    *,
    ora: Callable[[], datetime] = adesso,
    cronometro: Callable[[], float] = time.monotonic,
) -> EsitoProva:
    """Genera la campagna passo per passo, come il job ma senza ripetizioni.

    Al primo errore si ferma e lo riporta: la campagna resta com'è, con ciò
    che è già salvato e già costato, e un nuovo lancio riparte da lì (R-24).
    Il job riprova da sé fino a 3 volte e potrebbe nascondere un modello
    debole: qui si vede.

    Raises:
        ErroreDominio: la campagna non esiste o non è da generare.
    """
    with transazione() as db:
        campagna = campagne.campagna(db, campagna_id)
        if campagna.stato not in (INVIATA, IN_GENERAZIONE):
            raise ErroreDominio(
                f"La campagna {campagna_id} è {campagna.stato}: la prova parte da "
                f"una campagna {INVIATA}."
            )
        titolo = campagna.titolo

    errore = None
    inizio = cronometro()
    try:
        for _ in range(generazione.MAX_PASSI):
            with transazione() as db:
                if not generazione.passo(db, campagna_id, ora()):
                    break
        else:
            errore = "La generazione non arriva alla fine."
    except generazione.GenerazioneInterrotta as interrotta:
        errore = (
            f"{interrotta.tipo} nella tappa {interrotta.tappa}: {interrotta.messaggio}"
        )
    except Exception as imprevisto:  # noqa: BLE001 - si riporta, non si nasconde
        # Solo il tipo e i punti del codice: il messaggio può contenere dati.
        punti = "".join(traceback.format_tb(imprevisto.__traceback__)).rstrip()
        errore = f"errore imprevisto ({type(imprevisto).__name__})\n{punti}"
    secondi = cronometro() - inizio

    with transazione() as db:
        return EsitoProva(
            campagna_id=campagna_id,
            titolo=titolo,
            secondi=secondi,
            stato=campagne.campagna(db, campagna_id).stato,
            errore=errore,
            riepilogo=riepilogo_ai_della_campagna(db, campagna_id),
        )


def _dollari(valore: Decimal) -> str:
    return f"{valore:.4f} $"


def rapporto_prova_ai(esito: EsitoProva) -> str:
    """Il rapporto della prova, in testo, da riportare nella tabella della PR."""
    impostazioni = leggi_impostazioni()
    riepilogo = esito.riepilogo
    righe = [
        f"Prova AI · campagna {esito.campagna_id} · {esito.titolo}",
        f"  provider          {impostazioni.ai_provider}",
        f"  modello visione   {impostazioni.ai_modello_visione or '-'}",
        f"  modello testo     {impostazioni.ai_modello_testo or '-'}",
        f"  esito             {'completata' if esito.errore is None else 'interrotta'}"
        f" (campagna {esito.stato})",
    ]
    if esito.errore is not None:
        righe.append(f"  errore            {esito.errore}")
    righe += [
        f"  tempo             {esito.secondi:.1f} s (questo lancio)",
        f"  post              {riepilogo.n_post}",
        "",
        "Chiamate per tipo (tutta la campagna)",
        f"  {'tipo':<9}{'n':>4} {'token in':>10} {'token out':>10} {'costo':>12}  modelli",
    ]
    for riga in riepilogo.per_tipo:
        righe.append(
            f"  {riga.tipo:<9}{riga.chiamate:>4} {riga.token_ingresso:>10} "
            f"{riga.token_uscita:>10} {_dollari(riga.costo_usd):>12}  "
            f"{', '.join(riga.modelli)}"
        )
    righe.append(
        f"  {'totale':<9}{'':>4} {'':>10} {'':>10} "
        f"{_dollari(riepilogo.costo_totale_usd):>12}"
    )
    if riepilogo.n_post:
        medio = riepilogo.costo_totale_usd / riepilogo.n_post
        righe.append(f"  costo medio per post: {_dollari(medio)}")
    righe += [
        "",
        f"Riscritture del piano:  {riepilogo.riscritture_piano}",
        f"Riscritture dei testi:  {riepilogo.riscritture_testi}",
        "",
    ]
    if not riepilogo.post_segnalati:
        righe.append("Post con blocchi o avvisi: nessuno")
    else:
        righe.append(f"Post con blocchi o avvisi: {len(riepilogo.post_segnalati)}")
        for post in riepilogo.post_segnalati:
            sigla = "BLOCCO" if post.con_blocco else "avviso"
            righe.append(
                f"  post {post.post_id} · {post.canale} · "
                f"{post.data_ora:%d/%m %H:%M} · {sigla}"
            )
            righe.extend(f"    {voce}" for voce in post.segnalazioni)
    return "\n".join(righe)


def _chiedi_password(etichetta: str) -> str:
    password = getpass(f"{etichetta}: ")
    if not password:
        raise SystemExit("La password non può essere vuota.")
    if getpass("Ripeti la password: ") != password:
        raise SystemExit("Le due password non coincidono.")
    return password


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m app.cli",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    comandi = parser.add_subparsers(dest="comando", required=True)
    comandi.add_parser("seed", help="artigiano con profilo, operatore e admin")
    nuovo = comandi.add_parser("crea-utente", help="crea un utente")
    nuovo.add_argument("--email", required=True)
    nuovo.add_argument("--nome", required=True)
    # I ruoli ammessi li controlla accesso.service.crea_utente(): qui nessuna copia.
    nuovo.add_argument("--ruolo", required=True)
    cambio = comandi.add_parser(
        "cambia-password", help="cambia la password di un utente"
    )
    cambio.add_argument("--email", required=True)
    prova = comandi.add_parser(
        "prova-ai", help="genera una campagna inviata e stampa cosa ha speso l'AI"
    )
    prova.add_argument("--campagna", required=True, type=int, help="id della campagna")
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
        elif argomenti.comando == "prova-ai":
            esito = esegui_prova_ai(argomenti.campagna)
            print(rapporto_prova_ai(esito))
            return 0 if esito.errore is None else 1
        elif argomenti.comando == "cambia-password":
            password = _chiedi_password("Nuova password")
            with transazione() as db:
                cambia_password(db, argomenti.email, password)
            print("Password cambiata.")
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
