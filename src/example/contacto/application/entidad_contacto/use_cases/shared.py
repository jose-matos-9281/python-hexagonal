from datetime import datetime
from typing import Any, Self
from uuid import UUID

from example.contacto.domain.entidad_contacto import (
    EntidadExampletate,
    GetEntidadContactoById,
    IdEntidadContacto,
    ValidacionEntidadContacto,
)
from example.contacto.ports.drivens import IEntidadContactoRepository
from hexagonal.application import CommandHandlerBase, RegisterTopics
from hexagonal.domain import Command, DomainEvent, IntegrationEvent, TCommand


class EntidadContactoDomainEvent(DomainEvent, topic_suffix="EntidadContacto"):
    id_entidad_contacto: IdEntidadContacto


class EntidadContactoIntegrationEvent(IntegrationEvent, topic_suffix="EntidadContacto"):
    id_entidad_contacto: IdEntidadContacto


class EntidadExamplenapshot(EntidadContactoIntegrationEvent, topic_suffix="Snapshot"):
    entidad: UUID
    contacto: UUID
    validacion: ValidacionEntidadContacto
    usuario_creacion: UUID | None
    usuario_validacion: UUID | None
    fecha_validacion: datetime | None
    created_on: datetime
    modified_on: datetime

    @classmethod
    def new(cls, state: EntidadExampletate) -> Self:
        user_creacion = state.usuario_creacion.value if state.usuario_creacion else None
        user_val = state.usuario_validacion.value if state.usuario_validacion else None
        return cls(
            id_entidad_contacto=state.id,
            entidad=state.entidad.value,
            contacto=state.contacto.value,
            validacion=state.validacion,
            usuario_creacion=user_creacion,
            usuario_validacion=user_val,
            fecha_validacion=state.fecha_validacion,
            created_on=state.created_on,
            modified_on=state.modified_on,
        )


TEntidadContactoEvent = EntidadContactoDomainEvent | EntidadContactoIntegrationEvent


class EntidadContactoCommand(Command, topic_suffix="EntidadContacto"): ...


EntidadContactoCommandHandler = CommandHandlerBase[
    TCommand, IEntidadContactoRepository[Any]
]


TOPICS = RegisterTopics(EntidadExamplenapshot, GetEntidadContactoById)

__all__ = [
    "EntidadContactoCommand",
    "EntidadContactoDomainEvent",
    "EntidadContactoIntegrationEvent",
    "EntidadExamplenapshot",
    "GetEntidadContactoById",
    "TEntidadContactoEvent",
    "TOPICS",
]
