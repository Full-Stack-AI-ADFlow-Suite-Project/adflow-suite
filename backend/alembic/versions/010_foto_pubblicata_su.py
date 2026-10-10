"""010: dove è uscita una foto, canale per canale (T2a-01, spec R-27).

``foto.pubblicata_su`` è un JSON ``{canale: istante dell'ultima pubblicazione}``;
le foto che ci sono già partono da ``{}``: mai pubblicate.
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "010"
down_revision = "009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "foto",
        sa.Column(
            "pubblicata_su",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )


def downgrade() -> None:
    op.drop_column("foto", "pubblicata_su")
