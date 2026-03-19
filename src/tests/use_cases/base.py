import os
from logging import getLogger

from alembic import command
from alembic.config import Config
from eventsourcing.utils import clear_topic_cache

from example import exampleAPI, exampleEntrypoint

logger = getLogger(__name__)


class BaseTest:
    temp_db: str
    env: dict[str, str] = {}

    @classmethod
    def setup_class(cls):
        cls.env = cls.env.copy()
        cls.env.update({
            "SQLALCHEMY_DATABASE_URL": f"sqlite:///{cls.temp_db}",
            "SCHEMA_NAME": "",
        })
        for k, v in cls.env.items():
            os.environ[k] = v
        # SQLite no usa esquema, lo eliminamos para evitar confusiones
        del os.environ["SCHEMA_NAME"]

        clear_topic_cache()
        # Run migrations using Alembic
        alembic_cfg = Config("alembic.ini")
        command.downgrade(alembic_cfg, "base")
        command.upgrade(alembic_cfg, "head")

        cls.app = exampleEntrypoint.get(env=cls.env)
        cls.api_wrapper = exampleAPI(cls.app)
        cls.api_wrapper.register_topics()
        cls.logger = getLogger(cls.__name__)
