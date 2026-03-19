# pyright: reportMissingParameterType=none, reportGeneralTypeIssues=none

from example.app.adapters.drivens.repository.sqlalchemy import (
    exampleSQLAlchemyInfrastructure,
)
from example.app.adapters.drivers import exampleAppProxyAdapter
from example.app.application import exampleApp
from example.app.ports.drivers import IexampleApp
from hexagonal.adapters.drivens.repository.sqlalchemy import (
    SQLAlchemyConnectionContextManager,
    SQLAlchemyDatastore,
)
from hexagonal.entrypoints import Entrypoint
from hexagonal.entrypoints.sqlalchemy import SQLAlchemyInfrastructureEntrypoint


class SQLAlchemyexampleEntrypoint(
    Entrypoint[IexampleApp[SQLAlchemyConnectionContextManager]]
):
    env = {
        "CREATE_TABLES": "false",
    }

    @classmethod
    def get(cls, env=None):
        env = cls.construct_env(env)
        sqlalchemy_infra = SQLAlchemyInfrastructureEntrypoint.get(env)
        datastore: SQLAlchemyDatastore = sqlalchemy_infra.datastore
        infrastructure = exampleSQLAlchemyInfrastructure(
            sqlalchemy_infra.mapper,
            datastore,
        )
        infrastructure.initialize(env)
        app = exampleApp(infrastructure)
        application = exampleAppProxyAdapter(app)
        return application
