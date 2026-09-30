"""crea tabelle utente e sessione

Revision ID: 001
Revises: 
Create Date: 2026-09-30 17:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Crea tabella utente
    op.create_table(
        'utente',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('nome', sa.String(length=255), nullable=False),
        sa.Column('ruolo', sa.String(length=50), nullable=False),
        sa.Column('attivo', sa.Boolean(), nullable=False),
        sa.Column('creato_il', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index(op.f('ix_utente_email'), 'utente', ['email'], unique=False)

    # Crea tabella sessione
    op.create_table(
        'sessione',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('token_hash', sa.String(length=64), nullable=False),
        sa.Column('utente_id', sa.Integer(), nullable=False),
        sa.Column('scade_il', sa.DateTime(timezone=True), nullable=False),
        sa.Column('creata_il', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['utente_id'], ['utente.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token_hash')
    )
    op.create_index(op.f('ix_sessione_token_hash'), 'sessione', ['token_hash'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_sessione_token_hash'), table_name='sessione')
    op.drop_table('sessione')
    op.drop_index(op.f('ix_utente_email'), table_name='utente')
    op.drop_table('utente')
