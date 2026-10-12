"""011: la tabella delle notifiche (T2b-01, spec R-32, plan §2).

Una riga per destinatario e per evento: la crea ``notifiche.crea()`` e il job
``invia_notifica`` ne aggiorna ``stato_invio`` e ``inviata_il``.
"""
import sqlalchemy as sa
from alembic import op

revision = "011"
down_revision = "010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "notifica",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "utente_id", sa.Integer(), sa.ForeignKey("utente.id"), nullable=False
        ),
        sa.Column(
            "campagna_id", sa.Integer(), sa.ForeignKey("campagna.id"), nullable=False
        ),
        sa.Column("post_id", sa.Integer(), sa.ForeignKey("post.id"), nullable=True),
        sa.Column("tipo", sa.Text(), nullable=False),
        sa.Column("canale", sa.Text(), nullable=False, server_default="email"),
        sa.Column(
            "stato_invio", sa.Text(), nullable=False, server_default="da_inviare"
        ),
        sa.Column(
            "creata_il",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("inviata_il", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_notifica_utente_id", "notifica", ["utente_id"])
    op.create_index("ix_notifica_campagna_id", "notifica", ["campagna_id"])


def downgrade() -> None:
    op.drop_table("notifica")
