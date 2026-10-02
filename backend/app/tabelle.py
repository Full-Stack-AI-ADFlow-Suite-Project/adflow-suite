"""
Composizione: importa tutti i moduli per la configurazione delle tabelle.

Questo file viene usato da Alembic per importare tutti i modelli
e assicurarsi che siano registrati in Base.metadata.
"""

from app.core.db import Base

# Importa tutti i moduli per registrare i modelli
# TODO: Uncommentare quando i moduli saranno completi
# from app.moduli.accesso.models import Utente, Sessione
# from app.moduli.artigiani.models import ProfiloBottega
# from app.moduli.campagne.models import Campagna, Foto, DecisioneCampagna
# from app.moduli.contenuti.models import Post, VersionePost, VersioneFoto
# from app.moduli.revisione.models import Approvazione
# from app.moduli.pubblicazione.models import Pubblicazione, Metrica
# from app.moduli.notifiche.models import Notifica


def get_all_models():
    """Restituisce tutti i modelli per Alembic."""
    return [model for model in Base.__subclasses__()]
