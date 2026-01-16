from decimal import Decimal

from example.domain.example import ExampleAggregate


class TestAggregateExample:
    def test_create_aggregate(self):
        aggregate = ExampleAggregate(nombre="Ejemplo Inicial", valor=Decimal("10.5"))
        assert aggregate.name == "Ejemplo Inicial"
        assert len(aggregate.pending_events) == 1

    def test_change_name_command(self):
        aggregate = ExampleAggregate(nombre="Ejemplo Inicial", valor=Decimal("10.5"))
        assert aggregate.name == "Ejemplo Inicial"
        aggregate.change_name(new_name="Nuevo Nombre")
        assert aggregate.name == "Nuevo Nombre"
        assert len(aggregate.pending_events) == 2


class TestSnapshotExample:
    def test_snapshot_state(self):
        aggregate = ExampleAggregate(nombre="Ejemplo Inicial", valor=Decimal("10.5"))
        snapshot = aggregate.Snapshot.take(aggregate)
        state = snapshot.state
        assert state.name == "Ejemplo Inicial"

        agg = snapshot.mutate(None)
        assert agg == aggregate
