"""Tests for SQLAlchemy repository adapter."""

import os
from decimal import Decimal

from eventsourcing.utils import clear_topic_cache

from example import register_topics
from example.application import (
    ExampleAPI,
    ExampleCreated,
    NombreCambiadoExample,
)
from example.domain.example import ExampleId
from example.entrypoints import ExampleAppEntrypoint
from hexagonal.entrypoints.sqlalchemy import clear_infrastructure_cache


class TestApplicationSQLAlchemy:
    """Test SQLAlchemy application bootstrap and bus verification."""

    env = {
        "ENV_REPOSITORY": "sqlalchemy",
        "SQLALCHEMY_DATABASE_URL": "sqlite:///test_sqlalchemy.db",
        "RESET_TABLES": "true",
        "CREATE_TABLES": "true",
    }

    def setup_class(self):
        # Clean up test database and caches
        clear_infrastructure_cache()
        try:
            if os.path.exists("test_sqlalchemy.db"):
                os.remove("test_sqlalchemy.db")
        except Exception:
            pass
        clear_topic_cache()
        register_topics()
        self.app = ExampleAppEntrypoint.get(self.env)

    def test_verify_buses(self):
        """Verify command, query and event buses are initialized."""
        command_bus = self.app.command_bus
        query_bus = self.app.query_bus
        event_bus = self.app.event_bus
        assert command_bus is not None
        assert query_bus is not None
        assert event_bus is not None


class TestCrudExampleSQLAlchemy:
    """Test CRUD operations using SQLAlchemy repository adapter."""

    env = {
        "ENV_REPOSITORY": "sqlalchemy",
        "SQLALCHEMY_DATABASE_URL": "sqlite:///test_sqlalchemy_crud.db",
        "RESET_TABLES": "true",
        "CREATE_TABLES": "true",
    }

    def setup_class(self):
        # Clean up test database and caches
        clear_infrastructure_cache()
        try:
            if os.path.exists("test_sqlalchemy_crud.db"):
                os.remove("test_sqlalchemy_crud.db")
        except Exception:
            pass
        clear_topic_cache()
        register_topics()
        self.app = ExampleAppEntrypoint.get(self.env)
        self.api = ExampleAPI(self.app)

    def test_create_read_update_delete(self):
        """Test full CRUD cycle for aggregates."""
        # Create
        cmd, evts = self.api.crear(
            nombre="Ejemplo SQLAlchemy 1",
            valor_example=Decimal("10.5"),
            events=[ExampleCreated],
        )
        assert cmd is not None
        assert len(evts) == 2

        created = evts[ExampleCreated]
        assert created is not None and isinstance(created, ExampleCreated)
        example_id = created.id_example

        # Read
        agg = self.api.get(example_id.value)
        assert agg is not None
        assert agg.name == "Ejemplo SQLAlchemy 1"

        # Update
        cmd, evts = self.api.cambiar_nombre(
            example_id.value,
            nuevo_nombre="Ejemplo SQLAlchemy 1 Actualizado",
            events=[NombreCambiadoExample],
        )
        changed = evts.get(NombreCambiadoExample)
        assert changed is not None and isinstance(changed, NombreCambiadoExample)
        assert changed.nuevo_nombre == "Ejemplo SQLAlchemy 1 Actualizado"

        # Read after update
        agg = self.api.get(example_id.value)
        assert agg is not None
        assert agg.name == "Ejemplo SQLAlchemy 1 Actualizado"


class TestSQLAlchemyMultipleAggregates:
    """Test multiple aggregate operations with SQLAlchemy."""

    env = {
        "ENV_REPOSITORY": "sqlalchemy",
        "SQLALCHEMY_DATABASE_URL": "sqlite:///test_sqlalchemy_multi.db",
        "CREATE_TABLES": "true",
    }

    def setup_class(self):
        # Clean up test database and caches
        clear_infrastructure_cache()
        try:
            if os.path.exists("test_sqlalchemy_multi.db"):
                os.remove("test_sqlalchemy_multi.db")
        except Exception:
            pass
        clear_topic_cache()
        register_topics()
        self.app = ExampleAppEntrypoint.get(self.env)
        self.api = ExampleAPI(self.app)

    def test_multiple_aggregates(self):
        """Test creating and reading multiple aggregates."""
        ids: list[ExampleId] = []

        # Create multiple aggregates
        for i in range(5):
            _, evts = self.api.crear(
                nombre=f"Aggregate {i}",
                valor_example=Decimal("10.5"),
                events=[ExampleCreated],
            )
            created = evts[ExampleCreated]
            assert isinstance(created, ExampleCreated)
            print(f"Created aggregate {i}: id={created.id_example.value}")
            ids.append(created.id_example)

        # Read all aggregates
        for i, agg_id in enumerate(ids):
            print(f"Getting aggregate {i}: looking for id={agg_id.value}")
            agg = self.api.get(agg_id.value)
            print(f"  Got: id={agg.id}, name={agg.name}")
            assert agg is not None
            assert (
                agg.name == f"Aggregate {i}"
            ), f"Expected 'Aggregate {i}', got '{agg.name}' for id {agg_id.value}"

    def test_update_multiple_aggregates(self):
        """Test updating multiple aggregates."""
        # Create
        _, evts1 = self.api.crear(
            nombre="First",
            valor_example=Decimal("10.5"),
            events=[ExampleCreated],
        )
        _, evts2 = self.api.crear(
            nombre="Second",
            valor_example=Decimal("10.5"),
            events=[ExampleCreated],
        )
        evt1 = evts1[ExampleCreated]
        evt2 = evts2[ExampleCreated]
        assert isinstance(evt1, ExampleCreated)
        assert isinstance(evt2, ExampleCreated)
        id1 = evt1.id_example
        id2 = evt2.id_example

        # Update both
        self.api.cambiar_nombre(
            id1.value, nuevo_nombre="First Updated", events=[NombreCambiadoExample]
        )
        self.api.cambiar_nombre(
            id2.value, nuevo_nombre="Second Updated", events=[NombreCambiadoExample]
        )

        # Verify updates
        agg1 = self.api.get(id1.value)
        agg2 = self.api.get(id2.value)

        assert agg1.name == "First Updated"
        assert agg2.name == "Second Updated"
