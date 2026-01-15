from typing import Any, Mapping, Optional

from example.ports.drivers import IExampleApp
from hexagonal.entrypoints import Entrypoint, EntrypointGroup
from hexagonal.ports.drivers import IBaseApplication


class SqliteBusApp(Entrypoint[IExampleApp[Any]]):
    name = "sqlite"

    @classmethod
    def get(cls, env: Mapping[str, str] | None = None):
        from .sqlite import SQLiteExampleEntrypoint

        return SQLiteExampleEntrypoint.get(env)


class SqlAlchemyBusApp(Entrypoint[IExampleApp[Any]]):
    """SQLAlchemy bus application entrypoint."""

    name = "sqlalchemy"

    @classmethod
    def get(cls, env: Mapping[str, str] | None = None):
        from .sqlalchemy import SQLAlchemyExampleEntrypoint

        return SQLAlchemyExampleEntrypoint.get(env)


class ExampleEntrypoint(EntrypointGroup[IExampleApp[Any]]):
    env_key = "ENV_REPOSITORY"
    entrypoints = [SqliteBusApp, SqlAlchemyBusApp]
    env = {"ENV_REPOSITORY": "sqlite"}


class SqliteApp(Entrypoint[IBaseApplication[Any]]):
    name = "sqlite"

    @classmethod
    def get(cls, env: Optional[Mapping[str, str]] = None):
        from hexagonal.entrypoints.sqlite import SQLiteAppEntrypoint

        class SQLiteExampleAppEntrypoint(SQLiteAppEntrypoint):
            BUS_APP = ExampleEntrypoint

        return SQLiteExampleAppEntrypoint.get(env)


class SqlAlchemyApp(Entrypoint[IBaseApplication[Any]]):
    """SQLAlchemy application entrypoint."""

    name = "sqlalchemy"

    @classmethod
    def get(cls, env: Optional[Mapping[str, str]] = None):
        from hexagonal.entrypoints.sqlalchemy import SQLAlchemyAppEntrypoint

        class SQLAlchemyExampleAppEntrypoint(SQLAlchemyAppEntrypoint):
            BUS_APP = ExampleEntrypoint

        return SQLAlchemyExampleAppEntrypoint.get(env)


class ExampleAppEntrypoint(EntrypointGroup[IBaseApplication[Any]]):
    env_key = "ENV_REPOSITORY"
    entrypoints = [SqliteApp, SqlAlchemyApp]
    env = {"ENV_REPOSITORY": "sqlite"}
