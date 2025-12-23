from hexagonal.domain import AggregateRoot, AggregateState, IdValueObject, command


class ExampleId(IdValueObject): ...


class ExampleState(AggregateState[ExampleId]):
    name: str


class ExampleAggregate(AggregateRoot[ExampleId]):
    def __init__(self, nombre: str):
        self.name: str = nombre

    @command("CambiarNombre")
    def change_name(self, new_name: str):
        self.name = new_name

    @property
    def state(self) -> ExampleState:
        return ExampleState.from_aggregate(self, name=self.name)
