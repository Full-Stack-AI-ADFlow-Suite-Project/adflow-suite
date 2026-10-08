"""008 riallineamento: tabelle e campi di plan §2 (T1-08).

Riporta lo schema dello sprint 1 alla forma del piano:
- nuove: ``account_social``, ``gruppo_foto``, ``piano``, ``uscita``,
  ``versione_post_foto``, ``errore_generazione``;
- cambiate: ``utente`` (+deve_cambiare_password), ``profilo_bottega``
  (+logo), ``campagna`` (+canali_tolti, +chiusa_il; via crea_immagini_ai e
  rimandata), ``foto`` (gruppo_id -> gruppo_foto, campagna_id facoltativo,
  +da_usare; via descrizione), ``decisione_campagna`` (+canale, +post_id),
  ``post`` (+uscita_id, formato, riempitivo, controllato_da,
  controllato_il, intervento_in_corso, intervento_dal; unico su
  uscita_id+canale), ``versione_post`` (+autore_id; via foto_id).

La migrazione è pensata per un database vuoto: le colonne tolte tornano
al default e i dati delle tabelle cambiate non sono preservati.
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "008"
down_revision = "007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- tabelle nuove ---
    op.create_table(
        "gruppo_foto",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("profilo_id", sa.Integer(), nullable=False),
        sa.Column("campagna_id", sa.Integer(), nullable=True),
        sa.Column("origine", sa.Text(), nullable=False),
        sa.Column("descrizione", sa.Text(), nullable=True),
        sa.Column("da_usare_il", sa.Date(), nullable=True),
        sa.Column("n_immagini", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["profilo_id"],
            ["profilo_bottega.id"],
        ),
        sa.ForeignKeyConstraint(
            ["campagna_id"],
            ["campagna.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_gruppo_foto_profilo_id"), "gruppo_foto", ["profilo_id"])
    op.create_index(op.f("ix_gruppo_foto_campagna_id"), "gruppo_foto", ["campagna_id"])
    op.create_table(
        "account_social",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("profilo_id", sa.Integer(), nullable=False),
        sa.Column("piattaforma", sa.Text(), nullable=False),
        sa.Column("id_pagina", sa.Text(), nullable=True),
        sa.Column("permesso", sa.Text(), nullable=True),
        sa.Column("scadenza", sa.DateTime(timezone=True), nullable=True),
        sa.Column("stato", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["profilo_id"],
            ["profilo_bottega.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "profilo_id", "piattaforma", name="uq_account_social_piattaforma"
        ),
    )
    op.create_table(
        "piano",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("campagna_id", sa.Integer(), nullable=False),
        sa.Column("numero", sa.Integer(), nullable=False),
        sa.Column("strategia", sa.Text(), nullable=False),
        sa.Column("contenuto", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "esito_controllo", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "debole", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.Column("provider_ai", sa.Text(), nullable=True),
        sa.Column("modello_ai", sa.Text(), nullable=True),
        sa.Column("versione_prompt", sa.Text(), nullable=True),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("campagna_id", "numero", name="uq_piano_numero"),
    )
    op.create_table(
        "uscita",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("campagna_id", sa.Integer(), nullable=False),
        sa.Column("gruppo_id", sa.Integer(), nullable=True),
        sa.Column("numero", sa.Integer(), nullable=False),
        sa.Column("tema", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["campagna_id"],
            ["campagna.id"],
        ),
        sa.ForeignKeyConstraint(
            ["gruppo_id"],
            ["gruppo_foto.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("campagna_id", "numero", name="uq_uscita_numero"),
    )

    # --- tabelle cambiate ---
    op.add_column(
        "utente",
        sa.Column(
            "deve_cambiare_password",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
    )
    op.add_column(
        "profilo_bottega",
        sa.Column("logo", sa.Text(), nullable=True),
    )
    op.drop_column("campagna", "crea_immagini_ai")
    op.drop_column("campagna", "rimandata")
    op.add_column(
        "campagna",
        sa.Column("canali_tolti", postgresql.ARRAY(sa.Text()), nullable=True),
    )
    op.add_column(
        "campagna",
        sa.Column("chiusa_il", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "foto",
        sa.Column(
            "da_usare", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
    )
    op.drop_column("foto", "descrizione")
    op.drop_column("foto", "gruppo_id")
    op.add_column("foto", sa.Column("gruppo_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "foto_gruppo_id_fkey", "foto", "gruppo_foto", ["gruppo_id"], ["id"]
    )
    op.create_index(op.f("ix_foto_gruppo_id"), "foto", ["gruppo_id"])
    op.alter_column("foto", "campagna_id", nullable=True)
    op.add_column(
        "decisione_campagna",
        sa.Column("canale", sa.Text(), nullable=True),
    )
    op.add_column(
        "decisione_campagna",
        sa.Column("post_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "decisione_campagna_post_id_fkey",
        "decisione_campagna",
        "post",
        ["post_id"],
        ["id"],
    )
    op.add_column(
        "post",
        sa.Column("uscita_id", sa.Integer(), nullable=False),
    )
    op.create_foreign_key(
        "post_uscita_id_fkey", "post", "uscita", ["uscita_id"], ["id"]
    )
    op.add_column(
        "post",
        sa.Column(
            "formato",
            sa.Text(),
            server_default=sa.text("'singola'"),
            nullable=False,
        ),
    )
    op.add_column("post", sa.Column("riempitivo", sa.Text(), nullable=True))
    op.add_column("post", sa.Column("controllato_da", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "post_controllato_da_fkey", "post", "utente", ["controllato_da"], ["id"]
    )
    op.add_column(
        "post", sa.Column("controllato_il", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column("post", sa.Column("intervento_in_corso", sa.Text(), nullable=True))
    op.add_column(
        "post",
        sa.Column("intervento_dal", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_unique_constraint(
        "uq_post_uscita_canale", "post", ["uscita_id", "canale"]
    )
    op.drop_constraint(
        "versione_post_foto_id_fkey", "versione_post", type_="foreignkey"
    )
    op.drop_column("versione_post", "foto_id")
    op.add_column(
        "versione_post",
        sa.Column("autore_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "versione_post_autore_id_fkey",
        "versione_post",
        "utente",
        ["autore_id"],
        ["id"],
    )
    op.create_table(
        "versione_post_foto",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("versione_id", sa.Integer(), nullable=False),
        sa.Column("posizione", sa.Integer(), nullable=False),
        sa.Column("foto_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["versione_id"],
            ["versione_post.id"],
        ),
        sa.ForeignKeyConstraint(
            ["foto_id"],
            ["foto.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "versione_id", "posizione", name="uq_versione_post_foto_posizione"
        ),
    )
    op.create_index(
        op.f("ix_versione_post_foto_foto_id"), "versione_post_foto", ["foto_id"]
    )
    op.create_table(
        "errore_generazione",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("campagna_id", sa.Integer(), nullable=False),
        sa.Column("tipo", sa.Text(), nullable=False),
        sa.Column("messaggio", sa.Text(), nullable=False),
        sa.Column("tappa", sa.Text(), nullable=False),
        sa.Column("canale", sa.Text(), nullable=True),
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
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_errore_generazione_campagna_id"),
        "errore_generazione",
        ["campagna_id"],
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_errore_generazione_campagna_id"), table_name="errore_generazione"
    )
    op.drop_table("errore_generazione")
    op.drop_index(
        op.f("ix_versione_post_foto_foto_id"), table_name="versione_post_foto"
    )
    op.drop_table("versione_post_foto")
    op.drop_constraint(
        "versione_post_autore_id_fkey", "versione_post", type_="foreignkey"
    )
    op.drop_column("versione_post", "autore_id")
    op.add_column(
        "versione_post",
        sa.Column("foto_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "versione_post_foto_id_fkey",
        "versione_post",
        "foto",
        ["foto_id"],
        ["id"],
    )
    op.drop_constraint("uq_post_uscita_canale", "post", type_="unique")
    op.drop_column("post", "intervento_dal")
    op.drop_column("post", "intervento_in_corso")
    op.drop_column("post", "controllato_il")
    op.drop_constraint("post_controllato_da_fkey", "post", type_="foreignkey")
    op.drop_column("post", "controllato_da")
    op.drop_column("post", "riempitivo")
    op.drop_column("post", "formato")
    op.drop_constraint("post_uscita_id_fkey", "post", type_="foreignkey")
    op.drop_column("post", "uscita_id")
    op.drop_constraint(
        "decisione_campagna_post_id_fkey", "decisione_campagna", type_="foreignkey"
    )
    op.drop_column("decisione_campagna", "post_id")
    op.drop_column("decisione_campagna", "canale")
    op.alter_column("foto", "campagna_id", nullable=False)
    op.drop_index(op.f("ix_foto_gruppo_id"), table_name="foto")
    op.drop_constraint("foto_gruppo_id_fkey", "foto", type_="foreignkey")
    op.drop_column("foto", "gruppo_id")
    op.add_column(
        "foto",
        sa.Column("gruppo_id", postgresql.UUID(as_uuid=True), nullable=False),
    )
    op.add_column("foto", sa.Column("descrizione", sa.Text(), nullable=True))
    op.drop_column("foto", "da_usare")
    op.drop_column("campagna", "chiusa_il")
    op.drop_column("campagna", "canali_tolti")
    op.add_column(
        "campagna",
        sa.Column(
            "rimandata", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
    )
    op.add_column(
        "campagna",
        sa.Column(
            "crea_immagini_ai",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
    )
    op.drop_column("profilo_bottega", "logo")
    op.drop_column("utente", "deve_cambiare_password")
    op.drop_table("uscita")
    op.drop_table("piano")
    op.drop_table("account_social")
    op.drop_index(op.f("ix_gruppo_foto_campagna_id"), table_name="gruppo_foto")
    op.drop_index(op.f("ix_gruppo_foto_profilo_id"), table_name="gruppo_foto")
    op.drop_table("gruppo_foto")
