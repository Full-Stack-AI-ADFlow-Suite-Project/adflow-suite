"""
Worker Procrastinate per l'esecuzione dei job in background.
"""

import procrastinate
from app.core.coda import app
from app.core.db import get_db_job

# Job tick_pubblicazione (plan §4)
@app.task(name="tick_pubblicazione")
async def tick_pubblicazione():
    """
    Tick eseguito ogni minuto per la pubblicazione dei post dovuti.
    Chiama pubblicazione.pubblica_dovuti().

    Questo job viene schedulato esternamente (es. cron) ogni minuto.
    """
    # TODO: Implementare quando il modulo pubblicazione sarà disponibile (T1-43)
    # from app.moduli.pubblicazione.service import pubblica_dovuti
    # db = next(get_db_job())
    # try:
    #     from app.core.orologio import adesso
    #     pubblica_dovuti(db, adesso())
    # finally:
    #     db.close()
    pass


# Job genera_campagna (plan §4)
@app.task(name="genera_campagna")
async def genera_campagna(campagna_id: int):
    """
    Genera i post di una campagna.
    """
    # TODO: Implementare nel modulo contenuti (T1-34)
    pass


# Job rigenera_post (plan §4, sprint 2b)
@app.task(name="rigenera_post")
async def rigenera_post(post_id: int):
    """
    Rigenera il testo di un post.
    """
    # TODO: Implementare nel modulo contenuti (sprint 2b)
    pass


# Job invia_notifica (plan §4, sprint 2b)
@app.task(name="invia_notifica")
async def invia_notifica(notifica_id: int):
    """
    Invia una notifica via email.
    """
    # TODO: Implementare nel modulo notifiche (sprint 2b)
    pass


# Job ritocca_foto (plan §4, sprint 3)
@app.task(name="ritocca_foto")
async def ritocca_foto(post_id: int):
    """
    Ritocca la foto di un post.
    """
    # TODO: Implementare nel modulo contenuti (sprint 3)
    pass


# Job promemoria (plan §4, sprint 3)
@app.task(name="promemoria")
async def promemoria():
    """
    Invia promemoria all'operatore per campagne in avvio.
    """
    # TODO: Implementare nel modulo revisione (sprint 3)
    pass


# Job raccogli_metriche (plan §4, sprint 4)
@app.task(name="raccogli_metriche")
async def raccogli_metriche():
    """
    Raccoglie le metriche dei post pubblicati.
    """
    # TODO: Implementare nel modulo pubblicazione (sprint 4)
    pass


# Job report_settimanale (plan §4, sprint 4)
@app.task(name="report_settimanale")
async def report_settimanale():
    """
    Invia report settimanale via email.
    """
    # TODO: Implementare nel modulo pubblicazione (sprint 4)
    pass


def main():
    """Avvia il worker Procrastinate."""
    import asyncio
    from procrastinate.cli import cli
    import sys

    asyncio.run(cli(sys.argv[1:]))


if __name__ == "__main__":
    main()
