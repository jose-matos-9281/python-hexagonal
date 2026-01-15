from typing import Mapping

from example.adapters.drivens.sqlalchemy import SQLAlchemyAppExampleInfrastructure
from example.adapters.drivers import ExampleAppProxyAdapter
from example.application import ExampleApp
from example.ports.drivers import IExampleApp
from hexagonal.adapters.drivens.repository.sqlalchemy import (
    SQLAlchemyConnectionContextManager,
)
from hexagonal.entrypoints import Entrypoint
from hexagonal.entrypoints.sqlalchemy import SQLAlchemyInfrastructureEntrypoint


class SQLAlchemyExampleEntrypoint(
    Entrypoint[IExampleApp[SQLAlchemyConnectionContextManager]]
):
    """Entrypoint for SQLAlchemy-based Example application."""

    env = {
        "CREATE_TABLES": "false",
        "TABLE_NAME": "app_example",
        # Note: SCHEMA_NAME is not set for SQLite compatibility
        # Set it explicitly when using PostgreSQL/MySQL
    }

    @classmethod
    def get(cls, env: Mapping[str, str] | None = None):
        env = cls.construct_env(env)
        sqlalchemy_infra = SQLAlchemyInfrastructureEntrypoint.get(env)
        infrastructure = SQLAlchemyAppExampleInfrastructure(
            sqlalchemy_infra.connection_manager,
            sqlalchemy_infra.mapper,
        )
        infrastructure.initialize(env)
        app = ExampleApp(infrastructure)
        application = ExampleAppProxyAdapter(app)
        return application
