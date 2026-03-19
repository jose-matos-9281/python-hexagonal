import os
from logging import getLogger
from pathlib import Path
from typing import Any, Mapping

from alembic import command
from alembic.config import Config
from eventsourcing.utils import clear_topic_cache
from sqlalchemy import func, select

from example import exampleAPI, exampleEntrypoint
from hexagonal.entrypoints.sqlalchemy import clear_infrastructure_cache

logger = getLogger(__name__)


def get_example_write_scope(app: Any) -> Any:
    return app.bus_app.infrastructure.create_write_scope()


def count_outbox_rows(app: Any, *, published: bool | None = None) -> int:
    scope = get_example_write_scope(app)
    table = scope.outbox_repository._outbox_table
    stmt = select(func.count()).select_from(table)
    if published is True:
        stmt = stmt.where(table.c.published_at.is_not(None))
    elif published is False:
        stmt = stmt.where(table.c.published_at.is_(None))

    with scope.outbox_repository.connection_manager.cursor(commit=False) as conn:
        return int(conn.execute(stmt).scalar_one())


def count_inbox_rows(app: Any, *, processed: bool | None = None) -> int:
    scope = get_example_write_scope(app)
    table = scope.inbox_repository._inbox_table
    stmt = select(func.count()).select_from(table)
    if processed is True:
        stmt = stmt.where(table.c.processed_at.is_not(None))
    elif processed is False:
        stmt = stmt.where(table.c.processed_at.is_(None))

    with scope.inbox_repository.connection_manager.cursor(commit=False) as conn:
        return int(conn.execute(stmt).scalar_one())


def reset_example_runtime_state() -> None:
    clear_topic_cache()
    clear_infrastructure_cache()


def build_example_env(
    temp_db: str | Path,
    env: Mapping[str, str] | None = None,
) -> dict[str, str]:
    bootstrap_env = dict(env or {})
    bootstrap_env.update(
        {
            "SQLALCHEMY_DATABASE_URL": f"sqlite:///{temp_db}",
            "SCHEMA_NAME": "",
        }
    )
    return bootstrap_env


def migrate_example_database(env: Mapping[str, str]) -> None:
    for key, value in env.items():
        os.environ[key] = value
    os.environ.pop("SCHEMA_NAME", None)

    alembic_cfg = Config("alembic.ini")
    command.downgrade(alembic_cfg, "base")
    command.upgrade(alembic_cfg, "head")


def bootstrap_example_stack(
    temp_db: str | Path,
    env: Mapping[str, str] | None = None,
    *,
    register_topics: bool = True,
) -> tuple[dict[str, str], Any, Any]:
    bootstrap_env = build_example_env(temp_db, env)
    reset_example_runtime_state()
    migrate_example_database(bootstrap_env)

    app = exampleEntrypoint.get(env=bootstrap_env)
    api_wrapper = exampleAPI(app)
    if register_topics:
        api_wrapper.register_topics()
    return bootstrap_env, app, api_wrapper


class BaseTest:
    temp_db: str
    env: dict[str, str] = {}

    @classmethod
    def setup_class(cls):
        cls.env, cls.app, cls.api_wrapper = bootstrap_example_stack(
            cls.temp_db,
            cls.env.copy(),
        )
        cls.logger = getLogger(cls.__name__)

    @classmethod
    def teardown_class(cls):
        reset_example_runtime_state()
