"""006: tabelle pubblicazione dello sprint 1."""
from alembic import op
import sqlalchemy as sa

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "pubblicazione",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("post_id", sa.Integer(), nullable=False),
        sa.Column("versione_id", sa.Integer(), nullable=False),
        sa.Column("n_tentativo", sa.Integer(), nullable=False),
        sa.Column("stato", sa.Text(), nullable=False),
        sa.Column("id_esterno", sa.Text(), nullable=True),
        sa.Column("errore", sa.Text(), nullable=True),
        sa.Column(
            "creata_il",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["post_id"],
            ["post.id"],
        ),
        sa.ForeignKeyConstraint(
            ["versione_id"],
            ["versione_post.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "post_id", "n_tentativo", name="uq_pubblicazione_tentativo"
        ),
    )
    op.create_index(
        "uq_pubblicazione_ok_post",
        "pubblicazione",
        ["post_id"],
        unique=True,
        postgresql_where=sa.text("stato = 'ok'"),
    )


def downgrade() -> None:
    op.drop_table("pubblicazione")
