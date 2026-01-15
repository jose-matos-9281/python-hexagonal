from decimal import Decimal

from hexagonal.domain import (
    AggregateRoot,
    IdValueObject,
    SnapshotState,
    ValueObject,
    command,
)


class ValueExample(ValueObject[Decimal]):
    prefix: str

    @classmethod
    def new(cls, value: Decimal, prefix: str) -> "ValueExample":
        return cls(value=value, prefix=prefix)


class ExampleId(IdValueObject): ...


class ExampleState(SnapshotState[ExampleId]):
    name: str
    valor: ValueExample


class ExampleAggregate(AggregateRoot[ExampleId, ExampleState]):
    def __init__(self, nombre: str, valor: Decimal):
        self.name: str = nombre
        self.valor: ValueExample = ValueExample.new(valor, prefix="")

    @command("CambiarNombre")
    def change_name(self, new_name: str):
        self.name = new_name

    @command("ActualizarValor")
    def update_valor(self, new_valor: ValueExample):
        self.valor = new_valor
