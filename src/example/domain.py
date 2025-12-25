from hexagonal.domain import AggregateRoot, IdValueObject, SnapshotState, command


class ExampleId(IdValueObject): ...


class ExampleState(SnapshotState[ExampleId]):
    name: str


class ExampleAggregate(AggregateRoot[ExampleId, ExampleState]):
    def __init__(self, nombre: str):
        self.name: str = nombre

    @command("CambiarNombre")
    def change_name(self, new_name: str):
        self.name = new_name
