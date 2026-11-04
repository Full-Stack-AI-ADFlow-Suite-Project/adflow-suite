"""Tipi condivisi dei parametri di percorso (RL-026).

Un id oltre il range di PostgreSQL ``int4`` fa fallire la query con
``InternalError`` (500): il limite superiore si ferma prima, nello schema del
percorso, e l'API risponde 422. Gli id minori di 1 restano ammessi: li
rifiutano i service con il 404 già documentato.
"""

from typing import Annotated

from fastapi import Path

# Massimo intero rappresentabile in una colonna PostgreSQL `integer`.
LIMITE_INTERO_PG = 2_147_483_647

IdPercorso = Annotated[int, Path(le=LIMITE_INTERO_PG)]
