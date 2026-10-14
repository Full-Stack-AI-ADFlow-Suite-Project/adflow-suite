"""012: il costo di ogni chiamata all'AI (T3-31, spec R-44, plan §2).

Una riga per chiamata di analisi, piano, testo o immagine, scritta da chi
chiama l'adattatore AI: la generazione e la rigenerazione di un testo.
"""
import sqlalchemy as sa
from alembic import op

revision = "012"
down_revision = "011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "chiamata_ai",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "campagna_id", sa.Integer(), sa.ForeignKey("campagna.id"), nullable=False
        ),
        sa.Column("post_id", sa.Integer(), sa.ForeignKey("post.id"), nullable=True),
        sa.Column("tipo", sa.Text(), nullable=False),
        sa.Column("provider_ai", sa.Text(), nullable=False),
        sa.Column("modello_ai", sa.Text(), nullable=False),
        sa.Column("token_ingresso", sa.Integer(), nullable=True),
        sa.Column("token_uscita", sa.Integer(), nullable=True),
        sa.Column("n_immagini", sa.Integer(), nullable=True),
        sa.Column("costo_usd", sa.Numeric(12, 6), nullable=False),
        sa.Column(
            "creata_il",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index("ix_chiamata_ai_campagna_id", "chiamata_ai", ["campagna_id"])


def downgrade() -> None:
    op.drop_table("chiamata_ai")
