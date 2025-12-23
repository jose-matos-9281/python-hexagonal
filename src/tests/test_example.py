from eventsourcing.utils import clear_topic_cache

from example import register_topics
from example.application import ExampleAPI
from example.entrypoints import ExampleAppEntrypoint


class TestApplicationSqlite:
    env = {
        "ENV_REPOSITORY": "sqlite",
        "SQLITE_DB_PATH": "test.db",
        "RESET_TABLES": "true",
        "CREATE_TABLES": "true",
    }

    def setup_class(self):
        clear_topic_cache()
        register_topics()
        self.app = ExampleAppEntrypoint.get(self.env)

    def test_verify_buses(self):
        command_bus = self.app.command_bus
        query_bus = self.app.query_bus
        event_bus = self.app.event_bus
        assert command_bus is not None
        assert query_bus is not None
        assert event_bus is not None


class TestCrudExampleSqlite:
    env = {
        "ENV_REPOSITORY": "sqlite",
        "SQLITE_DB_PATH": "test.db",
        "RESET_TABLES": "true",
        "CREATE_TABLES": "true",
    }

    def setup_class(self):
        clear_topic_cache()
        register_topics()
        self.app = ExampleAppEntrypoint.get(self.env)
        self.api = ExampleAPI(self.app)

    def test_create_read_update_delete(self):
        # Create
        cmd, evts = self.api.crear(nombre="Ejemplo 1")
        assert cmd is not None
        assert len(evts) == 2
