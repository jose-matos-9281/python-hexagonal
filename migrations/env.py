import os
from logging.config import fileConfig
from typing import Any

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool

from example.app.entrypoints import exampleEntrypoint
from example.database.base import Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
load_dotenv()
config = context.config

database_url = os.getenv("SQLALCHEMY_DATABASE_URL")
if not database_url:
    raise RuntimeError("SQLALCHEMY_DATABASE_URL no está definida")
schema_name = os.getenv("SCHEMA_NAME", "example")
config.set_main_option("sqlalchemy.url", database_url)
# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
exampleEntrypoint.get()
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context_kwargs: dict[str, Any] = {
        "url": url,
        "target_metadata": target_metadata,
        "literal_binds": True,
        "dialect_opts": {"paramstyle": "named"},
    }
    if "sqlite" not in (url or "").lower():
        context_kwargs["version_table_schema"] = schema_name

    context.configure(**context_kwargs)

    with context.begin_transaction():
        context.run_migrations()


def include_object(object, name, type_, reflected, compare_to):  # type: ignore  # ty:ignore[unused-type-ignore-comment]
    # En SQLite no usamos esquemas
    url = config.get_main_option("sqlalchemy.url")
    if "sqlite" in (url or "").lower():
        return True

    # Solo permite objetos que pertenezcan al esquema configurado
    if type_ == "table":
        return object.schema == schema_name  # type: ignore  # ty:ignore[unused-type-ignore-comment]
    return True


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context_kwargs: dict[str, Any] = {
            "connection": connection,
            "target_metadata": target_metadata,
            "include_object": include_object,
            "include_schemas": True,
        }

        if connection.dialect.name != "sqlite":
            context_kwargs["version_table_schema"] = schema_name

        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
