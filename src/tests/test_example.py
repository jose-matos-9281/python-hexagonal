import os

from eventsourcing.utils import clear_topic_cache

from example import register_topics
from example.application import ExampleAPI, ExampleCreated, NombreCambiadoExample
from example.entrypoints.app import ExampleAppEntrypoint


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
        try:
            if os.path.exists(self.env["SQLITE_DB_PATH"]):
                os.remove(self.env["SQLITE_DB_PATH"])
        except Exception:
            pass
        clear_topic_cache()
        register_topics()
        self.app = ExampleAppEntrypoint.get(self.env)
        self.api = ExampleAPI(self.app)

    def test_create_read_update_delete(self):
        # Create
        cmd, evts = self.api.crear(nombre="Ejemplo 1", events=[ExampleCreated])
        assert cmd is not None
        assert len(evts) == 2

        created = evts[ExampleCreated]
        assert created is not None and isinstance(created, ExampleCreated)
        example_id = created.id_example

        agg = self.api.get(example_id.value)
        assert agg is not None
        assert agg.name == "Ejemplo 1"

        cmd, evts = self.api.cambiar_nombre(
            example_id.value,
            nuevo_nombre="Ejemplo 1 Actualizado",
            events=[NombreCambiadoExample],
        )
        changed = evts.get(NombreCambiadoExample)
        assert changed is not None and isinstance(changed, NombreCambiadoExample)
        assert changed.nuevo_nombre == "Ejemplo 1 Actualizado"

        agg = self.api.get(example_id.value)
        assert agg is not None
        assert agg.name == "Ejemplo 1 Actualizado"
