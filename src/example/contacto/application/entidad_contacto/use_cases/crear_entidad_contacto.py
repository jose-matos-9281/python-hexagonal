from typing import Any, Iterable
from uuid import UUID

from example.contacto.domain.entidad_contacto import (
    EntidadContacto,
    EntidadExampletate,
)
from example.contacto.domain.shared import IdContacto, IdEntidad, IdUsuario

from .shared import (
    TOPICS,
    EntidadContactoCommand,
    EntidadContactoCommandHandler,
    EntidadContactoDomainEvent,
    EntidadExamplenapshot,
    TEntidadContactoEvent,
)


class CrearEntidadContacto(EntidadContactoCommand):
    entidad: IdEntidad
    contacto: IdContacto
    usuario: IdUsuario | None = None

    @classmethod
    def new(
        cls,
        entidad: IdEntidad | UUID,
        contacto: IdContacto | UUID,
        usuario: IdUsuario | UUID | None = None,
        *_: Any,
        **__: Any,
    ) -> "CrearEntidadContacto":
        entidad_id = IdEntidad.from_value(entidad)
        contacto_id = IdContacto.from_value(contacto)
        usuario_id = IdUsuario.from_value(usuario) if usuario else None
        return cls(entidad=entidad_id, contacto=contacto_id, usuario=usuario_id)


class EntidadContactoCreado(EntidadContactoDomainEvent, topic_suffix="Creado"):
    entidad: IdEntidad
    contacto: IdContacto
    usuario: IdUsuario | None

    @classmethod
    def new(cls, state: EntidadExampletate) -> "EntidadContactoCreado":
        return cls(
            id_entidad_contacto=state.id,
            entidad=state.entidad,
            contacto=state.contacto,
            usuario=state.usuario_creacion,
        )


class CrearEntidadContactoHandler(EntidadContactoCommandHandler[CrearEntidadContacto]):
    def execute(self, command: CrearEntidadContacto) -> Iterable[TEntidadContactoEvent]:
        entidad_contacto = EntidadContacto(
            entidad=command.entidad,
            contacto=command.contacto,
            usuario=command.usuario,
        )
        self.repository.save(entidad_contacto)
        evento = EntidadContactoCreado.new(entidad_contacto.state)
        snap = EntidadExamplenapshot.new(entidad_contacto.state)
        return [snap, evento]


TOPICS.register(EntidadContactoCreado, CrearEntidadContacto)
