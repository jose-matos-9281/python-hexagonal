from typing import Any, Iterable
from uuid import UUID

from example.contacto.domain.contacto import (
    Contacto,
    ContactoValueStrategy,
    Exampletate,
)
from example.contacto.domain.shared import ContactoValue, IdUsuario, TipoContacto

from .shared import (
    ContactoCommand,
    ContactoCommandHandler,
    ContactoDomainEvent,
    Examplenapshot,
    TContactoEvent,
)


class CrearContacto(ContactoCommand):
    contacto: ContactoValue
    usuario: IdUsuario | None = None

    @classmethod
    def new(
        cls,
        tipo_contacto: TipoContacto | str,
        contacto: str,
        usuario: IdUsuario | UUID | None = None,
        *_: Any,
        **__: Any,
    ):
        if isinstance(tipo_contacto, str):
            tipo_contacto = TipoContacto(tipo_contacto)
        contacto_value = ContactoValueStrategy[tipo_contacto].new(contacto)
        usuario_id = IdUsuario.from_value(usuario) if usuario else None
        return cls(contacto=contacto_value, usuario=usuario_id)


class ContactoCreado(ContactoDomainEvent, topic_suffix="Creado"):
    tipo_contacto: TipoContacto
    contacto: str
    usuario: IdUsuario | None

    @classmethod
    def new(cls, state: Exampletate) -> "ContactoCreado":
        return cls(
            id_contacto=state.id,
            tipo_contacto=state.contacto.tipo,
            contacto=state.contacto.value,
            usuario=state.usuario_creacion,
        )


class CrearContactoHandler(ContactoCommandHandler[CrearContacto]):
    def execute(self, command: CrearContacto) -> Iterable[TContactoEvent]:
        contacto = Contacto(contacto=command.contacto, usuario=command.usuario)
        self.repository.save(contacto)
        evento = ContactoCreado.new(contacto.state)
        snap = Examplenapshot.new(contacto.state)
        return [snap, evento]
