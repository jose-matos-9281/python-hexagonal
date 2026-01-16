from eventsourcing.utils import register_topic

from .api import API
from .app import ExampleApp
from .example.api import ExampleAPI
from .example.use_cases import (
    CambiarNombreExample,
    CreateExample,
    DeleteExample,
    ExampleCreated,
    ExampleDeleted,
    ExampleSnapshot,
    GetExampleById,
    NombreCambiadoExample,
)


def register_topics():
    register_topic(ExampleCreated.TOPIC, ExampleCreated)
    register_topic(NombreCambiadoExample.TOPIC, NombreCambiadoExample)
    register_topic(ExampleDeleted.TOPIC, ExampleDeleted)
    register_topic(ExampleSnapshot.TOPIC, ExampleSnapshot)


__all__ = [
    "ExampleAPI",
    "ExampleApp",
    "API",
    "CreateExample",
    "CambiarNombreExample",
    "CreateExample",
    "ExampleCreated",
    "CambiarNombreExample",
    "NombreCambiadoExample",
    "DeleteExample",
    "ExampleDeleted",
    "GetExampleById",
    "ExampleSnapshot",
]
