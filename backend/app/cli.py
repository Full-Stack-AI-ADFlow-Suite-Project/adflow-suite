"""
CLI per comandi di gestione.

Include:
- Seed dei dati iniziali (T1-06)
- Creazione utenti (T1-06)
"""

import click
from app.core.db import SessionLocal
from app.core.config import settings


@click.group()
def cli():
    """AdFlow CLI."""
    pass


@cli.command()
def seed():
    """
    Seed dei dati iniziali.

    Crea:
    - Un artigiano con profilo completo
    - Un operatore
    - Un admin

    TODO: Implementare in T1-06
    """
    click.echo("Seed non ancora implementato (T1-06)")


@cli.command()
@click.option("--email", required=True, help="Email dell'utente")
@click.option("--password", required=True, help="Password dell'utente")
@click.option("--nome", required=True, help="Nome dell'utente")
@click.option("--ruolo", required=True, type=click.Choice(["artigiano", "operatore", "admin"]), help="Ruolo dell'utente")
def crea_utente(email: str, password: str, nome: str, ruolo: str):
    """
    Crea un nuovo utente.

    TODO: Implementare in T1-06, chiamerà accesso.service.crea_utente()
    """
    click.echo(f"Creazione utente non ancora implementata (T1-06): {email}, {ruolo}")


if __name__ == "__main__":
    cli()
