"""Worker: registra i job dei moduli importando i loro jobs.py. La coda e l'avvio arrivano con T1-05."""

from app.moduli.accesso import jobs as accesso
from app.moduli.artigiani import jobs as artigiani
from app.moduli.campagne import jobs as campagne
from app.moduli.contenuti import jobs as contenuti
from app.moduli.notifiche import jobs as notifiche
from app.moduli.pubblicazione import jobs as pubblicazione
from app.moduli.revisione import jobs as revisione

JOB_DEI_MODULI = (
    accesso,
    notifiche,
    artigiani,
    campagne,
    contenuti,
    revisione,
    pubblicazione,
)
