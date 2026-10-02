"""003: tabelle campagne dello sprint 1."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "campagna",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("profilo_id", sa.Integer(), nullable=False),
        sa.Column("titolo", sa.Text(), nullable=False),
        sa.Column("inizio", sa.Date(), nullable=False),
        sa.Column("fine", sa.Date(), nullable=False),
        sa.Column("descrizione", sa.Text(), nullable=True),
        sa.Column(
            "crea_immagini_ai",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column("stato", sa.Text(), nullable=False),
        sa.Column("canali", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("frequenza", sa.Text(), nullable=True),
        sa.Column("obiettivo", sa.Text(), nullable=True),
        sa.Column(
            "profilo_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "rimandata", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.Column("inviata_il", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["profilo_id"],
            ["profilo_bottega.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "foto",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("profilo_id", sa.Integer(), nullable=False),
        sa.Column("campagna_id", sa.Integer(), nullable=False),
        sa.Column("gruppo_id", sa.UUID(), nullable=False),
        sa.Column(
            "origine", sa.Text(), server_default=sa.text("'caricata'"), nullable=False
        ),
        sa.Column("file", sa.Text(), nullable=False),
        sa.Column("mime", sa.Text(), nullable=False),
        sa.Column("larghezza", sa.Integer(), nullable=False),
        sa.Column("altezza", sa.Integer(), nullable=False),
        sa.Column("descrizione", sa.Text(), nullable=True),
        sa.Column("analisi_ai", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "n_utilizzi", sa.Integer(), server_default=sa.text("0"), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["campagna_id"],
            ["campagna.id"],
        ),
        sa.ForeignKeyConstraint(
            ["profilo_id"],
            ["profilo_bottega.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "decisione_campagna",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("campagna_id", sa.Integer(), nullable=False),
        sa.Column("utente_id", sa.Integer(), nullable=False),
        sa.Column("esito", sa.Text(), nullable=False),
        sa.Column("motivo", sa.Text(), nullable=True),
        sa.Column("nota", sa.Text(), nullable=True),
        sa.Column("foto_segnate", postgresql.ARRAY(sa.Integer()), nullable=True),
        sa.Column(
            "creata_il",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["campagna_id"],
            ["campagna.id"],
        ),
        sa.ForeignKeyConstraint(
            ["utente_id"],
            ["utente.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("decisione_campagna")
    op.drop_table("foto")
    op.drop_table("campagna")
