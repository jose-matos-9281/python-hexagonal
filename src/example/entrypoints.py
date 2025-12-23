from typing import Mapping

from example.adapters import ExampleAppProxyAdapter, SQLiteAppExampleInfrastructure
from example.application import ExampleApp
from example.ports import IExampleApp
from hexagonal.adapters.drivens.repository.sqlite import SQLiteConnectionContextManager
from hexagonal.entrypoints import Entrypoint
from hexagonal.entrypoints.sqlite import SQLiteInfrastructureEntrypoint


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
