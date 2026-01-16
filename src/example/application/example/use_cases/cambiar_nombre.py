from typing import Self
from uuid import UUID

from example.domain.example import ExampleId, ExampleState

from .shared import (
    ExampleCommand,
    ExampleCommandHandler,
    ExampleDomainEvent,
    ExampleIntegrationEvent,
    ExampleSnapshot,
)


# Use Case Change Name Example
class CambiarNombreExample(ExampleCommand, topic_suffix="CambiarNombre"):
    id_example: ExampleId
    nuevo_nombre: str

    @classmethod
    def new(cls, id: UUID, nuevo_nombre: str) -> Self:
        return cls(id_example=ExampleId(value=id), nuevo_nombre=nuevo_nombre)


class NombreCambiadoExample(ExampleDomainEvent, topic_suffix="NombreCambiado"):
    nuevo_nombre: str

    @classmethod
    def from_state(cls, state: ExampleState) -> Self:
        return cls(id_example=state.id, nuevo_nombre=state.name)

    @classmethod
    def new(cls, id_example: ExampleId, nuevo_nombre: str) -> Self:
        return cls(id_example=id_example, nuevo_nombre=nuevo_nombre)


class CambiarNombreExampleHandler(ExampleCommandHandler[CambiarNombreExample]):
    def execute(self, command: CambiarNombreExample):
        example_agg = self.repository.get(command.id_example)
        example_agg.change_name(command.nuevo_nombre)
        self.repository.save(example_agg)
        events: list[ExampleDomainEvent | ExampleIntegrationEvent] = [
            NombreCambiadoExample.from_state(example_agg.state),
            ExampleSnapshot.new(example_agg.state),
        ]
        return events
