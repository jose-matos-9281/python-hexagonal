from typing import Self
from uuid import UUID

from example.domain.example import ExampleId, ExampleState

from .shared import ExampleCommand, ExampleCommandHandler, ExampleDomainEvent


# Use Case Delete Example
class DeleteExample(ExampleCommand, topic_suffix="Eliminar"):
    id_example: ExampleId

    @classmethod
    def new(cls, id: UUID) -> Self:
        return cls(id_example=ExampleId(value=id))


class ExampleDeleted(ExampleDomainEvent, topic_suffix="Deleted"):
    @classmethod
    def from_state(cls, state: ExampleState) -> Self:
        return cls(id_example=state.id)

    @classmethod
    def new(cls, id_example: ExampleId) -> Self:
        return cls(id_example=id_example)


class DeleteExampleHandler(ExampleCommandHandler[DeleteExample]):
    def execute(self, command: DeleteExample):
        example_agg = self.repository.delete(command.id_example)
        events: list[ExampleDomainEvent] = [
            ExampleDeleted.from_state(example_agg.state),
        ]
        return events
