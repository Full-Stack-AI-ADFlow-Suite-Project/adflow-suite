"""015: la corsia del ritocco (RT-05).

`versione_post_foto.ritocco` (la scelta dell'operatore sulla foto di una
versione), `versione_post_foto.render` (la chiave del file derivato approvato)
e `chiamata_ai.token_in_cache` (i token d'ingresso serviti dalla cache del
provider). Tutte nullabili: le righe esistenti restano valide.
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "015"
down_revision = "014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("versione_post_foto", sa.Column("ritocco", JSONB(), nullable=True))
    op.add_column("versione_post_foto", sa.Column("render", sa.Text(), nullable=True))
    op.add_column(
        "chiamata_ai", sa.Column("token_in_cache", sa.Integer(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("chiamata_ai", "token_in_cache")
    op.drop_column("versione_post_foto", "render")
    op.drop_column("versione_post_foto", "ritocco")
