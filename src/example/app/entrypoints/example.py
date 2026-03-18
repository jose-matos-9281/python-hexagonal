from logging import getLogger
from typing import Any, Mapping, Optional

from example.app.ports.drivers import IexampleApp
from hexagonal.entrypoints import Entrypoint, EntrypointGroup

logger = getLogger(__name__)


class Sqlalchemy(Entrypoint[IexampleApp[Any]]):
    name = "sqlalchemy"

    @classmethod
    def get(cls, env: Optional[Mapping[str, str]] = None):
        from .db.sqlalchemy import SQLAlchemyexampleEntrypoint

        return SQLAlchemyexampleEntrypoint.get(env)


class exampleBusAppEntrypoint(EntrypointGroup[IexampleApp[Any]]):
    env_key = "ENV_REPOSITORY"
    entrypoints = [Sqlalchemy]
    env = {"ENV_REPOSITORY": "sqlalchemy"}
