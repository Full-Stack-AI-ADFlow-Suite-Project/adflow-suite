"""§1.4 — Generazione e rigenerazioni usano `campagna.profilo_snapshot`.

Attacco di §4.3: cambiare il profilo dopo l'invio, poi Rigenera testo e
Rigenera immagine: deve uscire ancora la fotografia vecchia.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.adapters.ai import usa_ai
from app.adapters.ai.finto import AIFinto
from app.moduli.contenuti import interventi as interventi_contenuti
from app.moduli.revisione import interventi as interventi_revisione
from tests.moduli.artigiani.fabbrica import profilo
from tests.moduli.campagne.fabbrica import campagna_in_revisione
from tests.moduli.contenuti.fabbrica import post_da_approvare


def test_rigenera_usa_lo_snapshot_e_non_il_profilo_corrente(db, utente_di_prova):
    """La rigenerazione passa all'AI il nome della bottega al momento dell'invio."""
    artigiano = utente_di_prova("artigiano")
    bottega = profilo(db, utente_id=artigiano.id, nome="Bottega Vecchia")
    campagna = campagna_in_revisione(db, profilo_id=bottega.id)
    post = post_da_approvare(db, campagna_id=campagna.id)
    db.flush()
    assert campagna.profilo_snapshot["nome"] == "Bottega Vecchia"

    # il profilo cambia dopo l'invio (la fabbrica ha già fotografato il vecchio)
    bottega.nome = "Bottega Nuova"
    db.flush()
    assert bottega.nome == "Bottega Nuova"

    adesso = datetime.now(timezone.utc)
    finto = AIFinto()
    with usa_ai(finto):
        interventi_revisione.rigenera(db, post.id, "totale", None, None, adesso)
        interventi_contenuti.rigenera(db, post.id, None, None, adesso)  # il job, a mano

    testi = [
        chiamata
        for chiamata in finto.chiamate
        if chiamata["operazione"] == "genera_post"
    ]
    assert testi, "la rigenerazione non ha chiamato l'AI"
    testo = post.versione_corrente.testo
    assert "Bottega Vecchia" in testo, "la rigenerazione non ha usato lo snapshot"
    assert "Bottega Nuova" not in testo
    assert campagna.profilo_snapshot["nome"] == "Bottega Vecchia"
