from typing import Any

from example.contacto.domain.shared import IdEntidad
from example.contacto.ports.drivens import IEntidadRepository
from hexagonal.application import CommandHandlerBase
from hexagonal.domain import Command, DomainEvent, IntegrationEvent, TCommand


class EntidadDomainEvent(DomainEvent, topic_suffix="Entidad"):
    id_entidad: IdEntidad


class EntidadIntegrationEvent(IntegrationEvent, topic_suffix="Entidad"):
    id_entidad: IdEntidad


TEntidadEvent = EntidadDomainEvent | EntidadIntegrationEvent


class EntidadCommand(Command, topic_suffix="Entidad"): ...


class EntidadCommandHandler(CommandHandlerBase[TCommand, IEntidadRepository[Any]]): ...
