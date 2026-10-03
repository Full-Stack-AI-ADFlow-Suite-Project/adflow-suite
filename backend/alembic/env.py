from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

from app.core.config import leggi_impostazioni
from app.tabelle import del_modello, metadata

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

# I test passano l'indirizzo di adflow_test in config.attributes["url"].
url = config.attributes.get("url") or leggi_impostazioni().database_url


def run_migrations_offline() -> None:
    context.configure(url=url, target_metadata=metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    motore = create_engine(url, poolclass=pool.NullPool)
    with motore.connect() as connessione:
        context.configure(
            connection=connessione,
            target_metadata=metadata,
            include_name=del_modello,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
