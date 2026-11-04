"""Tipi condivisi degli id in ingresso (RL-026).

Un id oltre il range di PostgreSQL ``int4`` fa fallire la query con
``InternalError`` (500): il limite superiore si ferma prima, nello schema
dell'ingresso, e l'API risponde 422. Gli id negativi restano ammessi: li
rifiutano i service con il 404 già documentato.
"""

from typing import Annotated

from fastapi import Form, Path, Query
from pydantic import Field

# Massimo intero rappresentabile in una colonna PostgreSQL `integer`.
LIMITE_INTERO_PG = 2_147_483_647

IdPercorso = Annotated[int, Path(le=LIMITE_INTERO_PG)]
IdQuery = Annotated[int, Query(le=LIMITE_INTERO_PG)]
IdQueryOpzionale = Annotated[int | None, Query(le=LIMITE_INTERO_PG)]
IdForm = Annotated[int, Form(le=LIMITE_INTERO_PG)]
IdCampo = Annotated[int, Field(le=LIMITE_INTERO_PG)]
