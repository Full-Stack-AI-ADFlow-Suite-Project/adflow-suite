"""012: versioni delle foto e anagrafica artigiano (T3-01, plan §2)."""
import sqlalchemy as sa
from alembic import op

revision = "012"
down_revision = "011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "versione_foto",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("foto_id", sa.Integer(), sa.ForeignKey("foto.id"), nullable=False),
        sa.Column("numero", sa.Integer(), nullable=False),
        sa.Column("file", sa.Text(), nullable=False),
        sa.Column("origine", sa.Text(), nullable=False),
        sa.Column("nota", sa.Text(), nullable=True),
        sa.Column("provider_ai", sa.Text(), nullable=True),
        sa.Column("modello_ai", sa.Text(), nullable=True),
        sa.Column("versione_prompt", sa.Text(), nullable=True),
        sa.Column(
            "creata_il",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.UniqueConstraint("foto_id", "numero", name="uq_versione_foto_numero"),
    )
    op.create_index("ix_versione_foto_foto_id", "versione_foto", ["foto_id"])
    op.execute(
        sa.text(
            """
            INSERT INTO versione_foto (foto_id, numero, file, origine)
            SELECT id, 0, file, 'originale' FROM foto
            """
        )
    )
    op.add_column(
        "versione_post_foto",
        sa.Column("versione_foto_id", sa.Integer(), nullable=True),
    )
    op.execute(
        sa.text(
            """
            UPDATE versione_post_foto AS legame
            SET versione_foto_id = versione_foto.id
            FROM versione_foto
            WHERE versione_foto.foto_id = legame.foto_id
              AND versione_foto.numero = 0
            """
        )
    )
    op.create_foreign_key(
        "fk_versione_post_foto_versione_foto_id_versione_foto",
        "versione_post_foto",
        "versione_foto",
        ["versione_foto_id"],
        ["id"],
    )
    op.create_index(
        "ix_versione_post_foto_versione_foto_id",
        "versione_post_foto",
        ["versione_foto_id"],
    )
    op.add_column(
        "post",
        sa.Column(
            "n_ritocchi_foto",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )
    op.create_table(
        "anagrafica_artigiano",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "utente_id", sa.Integer(), sa.ForeignKey("utente.id"), nullable=False
        ),
        sa.Column("codice", sa.Text(), nullable=False),
        sa.Column("codice_consorzio", sa.Text(), nullable=False),
        sa.Column("nome_bottega", sa.Text(), nullable=False),
        sa.Column("referente", sa.Text(), nullable=False),
        sa.Column("citta", sa.Text(), nullable=False),
        sa.Column("telefono", sa.Text(), nullable=True),
        sa.Column(
            "stato_iscrizione", sa.Text(), nullable=False, server_default="attiva"
        ),
        sa.Column(
            "iscritto_il",
            sa.Date(),
            nullable=False,
            server_default=sa.text("CURRENT_DATE"),
        ),
        sa.UniqueConstraint("utente_id", name="uq_anagrafica_artigiano_utente"),
        sa.UniqueConstraint("codice", name="uq_anagrafica_artigiano_codice"),
    )


def downgrade() -> None:
    op.drop_table("anagrafica_artigiano")
    op.drop_column("post", "n_ritocchi_foto")
    op.drop_index(
        "ix_versione_post_foto_versione_foto_id", table_name="versione_post_foto"
    )
    op.drop_constraint(
        "fk_versione_post_foto_versione_foto_id_versione_foto",
        "versione_post_foto",
        type_="foreignkey",
    )
    op.drop_column("versione_post_foto", "versione_foto_id")
    op.drop_index("ix_versione_foto_foto_id", table_name="versione_foto")
    op.drop_table("versione_foto")
