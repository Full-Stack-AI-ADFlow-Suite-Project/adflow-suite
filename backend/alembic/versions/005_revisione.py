"""005: tabelle revisione dello sprint 1."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "approvazione",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("versione_id", sa.Integer(), nullable=False),
        sa.Column("utente_id", sa.Integer(), nullable=False),
        sa.Column("ruolo", sa.Text(), nullable=False),
        sa.Column("esito", sa.Text(), nullable=False),
        sa.Column(
            "creata_il",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["utente_id"],
            ["utente.id"],
        ),
        sa.ForeignKeyConstraint(
            ["versione_id"],
            ["versione_post.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("approvazione")
