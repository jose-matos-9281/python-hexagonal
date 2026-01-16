import logging
from decimal import Decimal
from typing import Self

from example.domain.example import (
    ExampleAggregate,
    ExampleId,
    ExampleState,
    ValueExample,
)

from .shared import (
    ExampleCommand,
    ExampleCommandHandler,
    ExampleDomainEvent,
    ExampleIntegrationEvent,
    ExampleSnapshot,
)

logger = logging.getLogger(__name__)


# Use Case Create Example
class CreateExample(ExampleCommand, topic_suffix="Create"):
    nombre: str
    valor: Decimal

    @classmethod
    def new(cls, nombre: str, valor: Decimal) -> Self:
        return cls(nombre=nombre, valor=valor)


class ExampleCreated(ExampleDomainEvent, topic_suffix="Created"):
    nombre: str
    valor: ValueExample

    @classmethod
    def from_state(cls, state: ExampleState) -> Self:
        return cls(id_example=state.id, nombre=state.name, valor=state.valor)

    @classmethod
    def new(cls, id_example: ExampleId, nombre: str, valor: ValueExample) -> Self:
        return cls(id_example=id_example, nombre=nombre, valor=valor)


class CrearExampleHandler(ExampleCommandHandler[CreateExample]):
    def execute(self, command: CreateExample):
        logger.debug(
            "    [DEBUG CrearExampleHandler]"
            " Creating aggregate with nombre=%s and valor=%s",
            command.nombre,
            command.valor,
        )
        example_agg = ExampleAggregate(nombre=command.nombre, valor=command.valor)
        logger.debug(f"    [DEBUG CrearExampleHandler] Aggregate id={example_agg.id}")
        self.repository.save(example_agg)
        events: list[ExampleDomainEvent | ExampleIntegrationEvent] = [
            ExampleCreated.from_state(example_agg.state),
            ExampleSnapshot.new(example_agg.state),
        ]
        logger.debug(
            "    [DEBUG CrearExampleHandler] Events created, id_example=%s",
            events[0].id_example,
        )
        return events
