import logging
from typing import Any, Iterable
from uuid import UUID

from example.contacto.domain.contacto import EstadoContacto, Exampletate
from example.contacto.domain.shared import IdContacto, IdUsuario
from hexagonal.domain import DomainValueError

from .shared import (
    ContactoCommand,
    ContactoCommandHandler,
    ContactoDomainEvent,
    Examplenapshot,
    TContactoEvent,
)

logger = logging.getLogger(__name__)


class ValidarContacto(ContactoCommand, topic_suffix="Validar"):
    id_contacto: IdContacto
    estado: EstadoContacto
    usuario: IdUsuario

    @classmethod
    def new(
        cls,
        id_contacto: IdContacto | UUID,
        estado: EstadoContacto | str,
        usuario: IdUsuario | UUID,
        *_: Any,
        **__: Any,
    ) -> "ValidarContacto":
        if isinstance(estado, str):
            estado = EstadoContacto[estado]
        id_contacto = IdContacto.from_value(id_contacto)
        usuario = IdUsuario.from_value(usuario)
        return cls(id_contacto=id_contacto, estado=estado, usuario=usuario)


class ContactoContactado(ContactoDomainEvent, topic_suffix="Contactado"):
    estado: EstadoContacto
    usuario: IdUsuario

    @classmethod
    def new(cls, state: Exampletate) -> "ContactoContactado":
        assert (
            state.usuario_validacion is not None
        ), "El usuario de validación no puede ser None"
        return cls(
            id_contacto=state.id,
            estado=state.estado,
            usuario=state.usuario_validacion,
        )


class ContactoNoContactado(ContactoDomainEvent, topic_suffix="NoContactado"):
    estado: EstadoContacto
    usuario: IdUsuario

    @classmethod
    def new(cls, state: Exampletate) -> "ContactoNoContactado":
        assert (
            state.usuario_validacion is not None
        ), "El usuario de validación no puede ser None"
        return cls(
            id_contacto=state.id,
            estado=state.estado,
            usuario=state.usuario_validacion,
        )


class ContactoNoContactable(ContactoDomainEvent, topic_suffix="NoContactable"):
    estado: EstadoContacto
    usuario: IdUsuario

    @classmethod
    def new(cls, state: Exampletate) -> "ContactoNoContactable":
        assert (
            state.usuario_validacion is not None
        ), "El usuario de validación no puede ser None"
        return cls(
            id_contacto=state.id,
            estado=state.estado,
            usuario=state.usuario_validacion,
        )


class ValidarContactoHandler(ContactoCommandHandler[ValidarContacto]):
    def execute(self, command: ValidarContacto) -> Iterable[TContactoEvent]:
        contacto = self.repository.get(command.id_contacto)
        evento: TContactoEvent

        if command.estado == EstadoContacto.CONTACTADO:
            contacto.marcar_contactado(command.usuario)
            evento = ContactoContactado.new(contacto.state)
        elif command.estado == EstadoContacto.NO_CONTACTADO:
            contacto.marcar_no_contactado(command.usuario)
            evento = ContactoNoContactado.new(contacto.state)
        elif command.estado == EstadoContacto.NO_CONTACTABLE:
            contacto.marcar_no_contactable(command.usuario)
            evento = ContactoNoContactable.new(contacto.state)
        else:
            raise DomainValueError(
                "El estado debe ser CONTACTADO, NO_CONTACTADO o NO_CONTACTABLE"
            )

        logger.info("Contacto validado: %s", contacto.estado)
        self.repository.save(contacto)
        snap = Examplenapshot.new(contacto.state)
        return [snap, evento]
