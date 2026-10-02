"""002: tabelle artigiani dello sprint 1."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "profilo_bottega",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("utente_id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.Text(), nullable=False),
        sa.Column("referente", sa.Text(), nullable=False),
        sa.Column("citta", sa.Text(), nullable=False),
        sa.Column("anni_attivita", sa.Integer(), nullable=True),
        sa.Column("sito", sa.Text(), nullable=True),
        sa.Column("storia", sa.Text(), nullable=True),
        sa.Column("origine", sa.Text(), nullable=True),
        sa.Column("valori", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("tipo_prodotto", sa.Text(), nullable=False),
        sa.Column("gamma", sa.Text(), nullable=True),
        sa.Column("fascia_prezzo", sa.Text(), nullable=True),
        sa.Column("stagionalita", sa.Text(), nullable=True),
        sa.Column("clienti_ideali", sa.Text(), nullable=False),
        sa.Column("obiettivo", sa.Text(), nullable=False),
        sa.Column("zona", sa.Text(), nullable=True),
        sa.Column("tono", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("cortesia", sa.Text(), nullable=True),
        sa.Column("vincoli", sa.Text(), nullable=True),
        sa.Column("canali", postgresql.ARRAY(sa.Text()), nullable=False),
        sa.Column("frequenza", sa.Text(), nullable=True),
        sa.Column("orari", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "social_esistenti", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "foto_policy", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "eventi_ricorrenti", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("chiusure", sa.Text(), nullable=True),
        sa.Column(
            "aggiornato_il",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["utente_id"],
            ["utente.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("utente_id"),
    )


def downgrade() -> None:
    op.drop_table("profilo_bottega")
