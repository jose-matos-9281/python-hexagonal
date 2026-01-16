from typing import Any
from uuid import UUID

from example.domain.example import ExampleAggregate, ExampleId
from hexagonal.application import GetById


# Query to get Example by Id
class GetExampleById(GetById[ExampleAggregate, ExampleId]):
    @classmethod
    def new(cls, id: ExampleId | UUID, *_: Any, **__: Any):
        if isinstance(id, UUID):
            id = ExampleId(value=id)
        return super().new(id=id, agg_type=ExampleAggregate)
