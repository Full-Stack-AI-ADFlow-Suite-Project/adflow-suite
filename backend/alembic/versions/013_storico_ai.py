"""013: lo storico dell'AI (T3-907, spec R-50, plan §2).

`chiamata_ai` registra anche la versione del prompt, la richiesta, la
risposta, l'esito, l'errore, la durata e il tentativo; `valutazione_ai` tiene
i voti da 1 a 5 che l'operatore dà alle risposte. Nessuna lettura né scrittura
nuova: le fanno T3-916, T3-917 e T3-918.
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "013"
down_revision = "012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("chiamata_ai", sa.Column("versione_prompt", sa.Text(), nullable=True))
    op.add_column(
        "chiamata_ai",
        sa.Column("richiesta", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column("chiamata_ai", sa.Column("risposta", sa.Text(), nullable=True))
    op.add_column(
        "chiamata_ai",
        sa.Column("esito", sa.Text(), nullable=False, server_default="ok"),
    )
    op.add_column("chiamata_ai", sa.Column("errore", sa.Text(), nullable=True))
    op.add_column("chiamata_ai", sa.Column("durata_ms", sa.Integer(), nullable=True))
    op.add_column("chiamata_ai", sa.Column("tentativo", sa.Integer(), nullable=True))
    op.add_column("chiamata_ai", sa.Column("foto_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_chiamata_ai_foto_id", "chiamata_ai", "foto", ["foto_id"], ["id"]
    )
    op.create_index("ix_chiamata_ai_creata_il", "chiamata_ai", ["creata_il"])

    op.create_table(
        "valutazione_ai",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "chiamata_ai_id",
            sa.Integer(),
            sa.ForeignKey("chiamata_ai.id"),
            nullable=False,
        ),
        sa.Column(
            "utente_id", sa.Integer(), sa.ForeignKey("utente.id"), nullable=False
        ),
        sa.Column("voto", sa.SmallInteger(), nullable=False),
        sa.Column("nota", sa.Text(), nullable=True),
        sa.Column(
            "creata_il",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.CheckConstraint("voto >= 1 AND voto <= 5", name="ck_valutazione_ai_voto"),
    )
    op.create_index(
        "ix_valutazione_ai_chiamata_ai_id", "valutazione_ai", ["chiamata_ai_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_valutazione_ai_chiamata_ai_id", table_name="valutazione_ai")
    op.drop_table("valutazione_ai")
    op.drop_index("ix_chiamata_ai_creata_il", table_name="chiamata_ai")
    op.drop_constraint("fk_chiamata_ai_foto_id", "chiamata_ai", type_="foreignkey")
    op.drop_column("chiamata_ai", "foto_id")
    op.drop_column("chiamata_ai", "tentativo")
    op.drop_column("chiamata_ai", "durata_ms")
    op.drop_column("chiamata_ai", "errore")
    op.drop_column("chiamata_ai", "esito")
    op.drop_column("chiamata_ai", "risposta")
    op.drop_column("chiamata_ai", "richiesta")
    op.drop_column("chiamata_ai", "versione_prompt")
