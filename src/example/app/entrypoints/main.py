from logging import getLogger
from typing import Any, Mapping

from hexagonal.entrypoints import Entrypoint, EntrypointGroup
from hexagonal.ports.drivers import IBaseApplication

from .bus import BusEntrypointGroupApp

logger = getLogger(__name__)


class Sqlalchemy(Entrypoint[IBaseApplication[Any]]):
    name = "sqlalchemy"

    @classmethod
    def get(cls, env: Mapping[str, str] | None = None):
        from hexagonal.entrypoints.sqlalchemy import SQLAlchemyAppEntrypoint

        from .db.sqlalchemy import (
            SQLAlchemyConnectionContextManager,
            SQLAlchemyexampleEntrypoint,
        )

        class SqlalchemyexampleAppEntrypoint(SQLAlchemyAppEntrypoint):
            BUS_APP = SQLAlchemyexampleEntrypoint
            BUS_GROUP = BusEntrypointGroupApp[SQLAlchemyConnectionContextManager]

        return SqlalchemyexampleAppEntrypoint.get(env)


class exampleEntrypoint(EntrypointGroup[IBaseApplication[Any]]):
    env_key = "ENV_REPOSITORY"
    entrypoints = [Sqlalchemy]
    env = {"ENV_REPOSITORY": "sqlalchemy"}
