from typing import Any, Mapping, Optional

from example.adapters import ExampleAppProxyAdapter, SQLiteAppExampleInfrastructure
from example.application import ExampleApp
from example.ports import IExampleApp
from hexagonal.adapters.drivens.repository.sqlite import SQLiteConnectionContextManager
from hexagonal.entrypoints import Entrypoint, EntrypointGroup
from hexagonal.entrypoints.sqlite import SQLiteInfrastructureEntrypoint
from hexagonal.ports.drivers import IBaseApplication


class SQLiteExampleEntrypoint(Entrypoint[IExampleApp[SQLiteConnectionContextManager]]):
    env = {
        "CREATE_TABLES": "false",
        "TABLE_NAME": "app_example",
        "SCHEMA_NAME": "example",
    }

    @classmethod
    def get(cls, env: Mapping[str, str] | None = None):
        env = cls.construct_env(env)
        sqlite_infra = SQLiteInfrastructureEntrypoint.get(env)
        infrastructure = SQLiteAppExampleInfrastructure(
            sqlite_infra.connection_manager,
            sqlite_infra.mapper,
        )
        infrastructure.initialize(env)
        app = ExampleApp(infrastructure)
        application = ExampleAppProxyAdapter(app)
        return application


class SqliteBusApp(Entrypoint[IExampleApp[Any]]):
    name = "sqlite"

    @classmethod
    def get(cls, env: Mapping[str, str] | None = None):
        return SQLiteExampleEntrypoint.get(env)


class ExampleEntrypoint(EntrypointGroup[IExampleApp[Any]]):
    env_key = "ENV_REPOSITORY"
    entrypoints = [SqliteBusApp]
    env = {"ENV_REPOSITORY": "sqlite"}


class SqliteApp(Entrypoint[IBaseApplication[Any]]):
    name = "sqlite"

    @classmethod
    def get(cls, env: Optional[Mapping[str, str]] = None):
        from hexagonal.entrypoints.sqlite import SQLiteAppEntrypoint

        class SQLiteExampleAppEntrypoint(SQLiteAppEntrypoint):
            BUS_APP = ExampleEntrypoint

        return SQLiteExampleAppEntrypoint.get(env)


class ExampleAppEntrypoint(EntrypointGroup[IBaseApplication[Any]]):
    env_key = "ENV_REPOSITORY"
    entrypoints = [SqliteApp]
    env = {"ENV_REPOSITORY": "sqlite"}
