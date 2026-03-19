from datetime import datetime
from typing import Any, Self
from uuid import UUID

from example.contacto.domain.contacto import EstadoContacto, Exampletate
from example.contacto.domain.shared import IdContacto, TipoContacto
from example.contacto.ports.drivens import IContactoRepository
from hexagonal.application import CommandHandlerBase, EventHandlerBase
from hexagonal.domain import Command, DomainEvent, IntegrationEvent, TCommand, TEvent


class ContactoDomainEvent(DomainEvent, topic_suffix="Contacto"):
    id_contacto: IdContacto


class ContactoIntegrationEvent(IntegrationEvent, topic_suffix="Contacto"):
    id_contacto: IdContacto


class Examplenapshot(ContactoIntegrationEvent, topic_suffix="Snapshot"):
    tipo_contacto: TipoContacto
    contacto: str
    estado: EstadoContacto
    usuario_creacion: UUID | None
    usuario_validacion: UUID | None
    fecha_validacion: datetime | None
    created_on: datetime
    modified_on: datetime

    @classmethod
    def new(cls, state: Exampletate) -> Self:
        user_creacion = state.usuario_creacion.value if state.usuario_creacion else None
        user_val = state.usuario_validacion.value if state.usuario_validacion else None
        return cls(
            id_contacto=state.id,
            tipo_contacto=state.contacto.tipo,
            contacto=state.contacto.value,
            estado=state.estado,
            usuario_creacion=user_creacion,
            usuario_validacion=user_val,
            fecha_validacion=state.fecha_validacion,
            created_on=state.created_on,
            modified_on=state.modified_on,
        )


TContactoEvent = ContactoDomainEvent | ContactoIntegrationEvent


class ContactoCommand(Command, topic_suffix="Contacto"): ...


ContactoCommandHandler = CommandHandlerBase[TCommand, IContactoRepository[Any]]

ContactoEventHandler = EventHandlerBase[TEvent, IContactoRepository[Any]]
