"""014: `pubblicazione.chiamata_il` (T5-111, RL-025, ADR-121).

L'istante in cui parte la chiamata al social, confermato prima di farla. Un
tentativo `in_corso` che lo porta ancora, senza esito, è di un processo morto
a metà: il post si segnala e non si ripubblica.
"""
import sqlalchemy as sa
from alembic import op

revision = "014"
down_revision = "013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "pubblicazione",
        sa.Column("chiamata_il", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("pubblicazione", "chiamata_il")
