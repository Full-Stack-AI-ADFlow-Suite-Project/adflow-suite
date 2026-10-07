"""008: contatori condivisi dei tentativi di login, senza identificatori in chiaro."""
from alembic import op
import sqlalchemy as sa

revision = "008"
down_revision = "007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "limite_login",
        sa.Column("chiave", sa.String(64), primary_key=True),
        sa.Column("tentativi", sa.Integer(), nullable=False),
        sa.Column("scade_il", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("tentativi > 0", name="limite_login_tentativi_positivi"),
    )
    op.create_index("ix_limite_login_scade_il", "limite_login", ["scade_il"])


def downgrade() -> None:
    op.drop_table("limite_login")
