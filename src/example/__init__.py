from eventsourcing.utils import register_topic

from .application import (
    CambiarNombreExample,
    CreateExample,
    DeleteExample,
    ExampleCommand,
    ExampleCreated,
    ExampleDeleted,
    ExampleDomainEvent,
    ExampleIntegrationEvent,
    ExampleSnapshot,
    NombreCambiadoExample,
)


def register_topics():
    register_topic(ExampleCommand.TOPIC, ExampleCommand)
    register_topic(ExampleDomainEvent.TOPIC, ExampleDomainEvent)
    register_topic(ExampleIntegrationEvent.TOPIC, ExampleIntegrationEvent)
    register_topic(ExampleSnapshot.TOPIC, ExampleSnapshot)
    register_topic(CreateExample.TOPIC, CreateExample)
    register_topic(ExampleCreated.TOPIC, ExampleCreated)
    register_topic(CambiarNombreExample.TOPIC, CambiarNombreExample)
    register_topic(NombreCambiadoExample.TOPIC, NombreCambiadoExample)
    register_topic(DeleteExample.TOPIC, DeleteExample)
    register_topic(ExampleDeleted.TOPIC, ExampleDeleted)


register_topics()
__all__ = [
    "CreateExample",
    "ExampleCommand",
    "ExampleCreated",
    "ExampleDomainEvent",
    "ExampleIntegrationEvent",
    "ExampleSnapshot",
    "NombreCambiadoExample",
    "CambiarNombreExample",
    "DeleteExample",
    "ExampleDeleted",
    "register_topics",
]
