"""004: tabelle contenuti dello sprint 1."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "post",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("campagna_id", sa.Integer(), nullable=False),
        sa.Column("canale", sa.Text(), nullable=False),
        sa.Column("data_ora", sa.DateTime(timezone=True), nullable=False),
        sa.Column("stato", sa.Text(), nullable=False),
        sa.Column(
            "da_rivedere", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.Column(
            "n_rigenerazioni_testo",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["campagna_id"],
            ["campagna.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_post_campagna_id"), "post", ["campagna_id"])
    op.create_index("ix_post_stato_data_ora", "post", ["stato", "data_ora"])
    op.create_table(
        "versione_post",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("post_id", sa.Integer(), nullable=False),
        sa.Column("numero", sa.Integer(), nullable=False),
        sa.Column("testo", sa.Text(), nullable=False),
        sa.Column("hashtag", postgresql.ARRAY(sa.Text()), nullable=False),
        sa.Column("foto_id", sa.Integer(), nullable=True),
        sa.Column("tipo_intervento", sa.Text(), nullable=False),
        sa.Column("testo_proposto", sa.Text(), nullable=True),
        sa.Column("nota", sa.Text(), nullable=True),
        sa.Column("provider_ai", sa.Text(), nullable=True),
        sa.Column("modello_ai", sa.Text(), nullable=True),
        sa.Column("versione_prompt", sa.Text(), nullable=True),
        sa.Column(
            "errori_validazione", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "creata_il",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["foto_id"],
            ["foto.id"],
        ),
        sa.ForeignKeyConstraint(
            ["post_id"],
            ["post.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("post_id", "numero", name="uq_versione_post_numero"),
    )


def downgrade() -> None:
    op.drop_table("versione_post")
    op.drop_table("post")
