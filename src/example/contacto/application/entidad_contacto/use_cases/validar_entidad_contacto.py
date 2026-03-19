import logging
from typing import Any, Iterable
from uuid import UUID

from pydantic import computed_field

from example.contacto.domain.entidad_contacto import (
    EntidadExampletate,
    IdEntidadContacto,
    ValidacionEntidadContacto,
)
from example.contacto.domain.shared import (
    ContactoValue,
    EntidadValue,
    IdContacto,
    IdEntidad,
    IdUsuario,
)
from hexagonal.domain import DomainValueError

from .shared import (
    TOPICS,
    EntidadContactoCommand,
    EntidadContactoCommandHandler,
    EntidadContactoDomainEvent,
    EntidadExamplenapshot,
    TEntidadContactoEvent,
)

logger = logging.getLogger(__name__)


class ValidarEntidadContacto(EntidadContactoCommand, topic_suffix="Validar"):
    id_entidad: IdEntidad
    id_contacto: IdContacto
    validacion: ValidacionEntidadContacto
    usuario: IdUsuario

    @classmethod
    def new(
        cls,
        entidad: IdEntidad | UUID | EntidadValue,
        contacto: IdContacto | UUID | ContactoValue,
        validacion: ValidacionEntidadContacto | str,
        usuario: IdUsuario | UUID,
        *_: Any,
        **__: Any,
    ) -> "ValidarEntidadContacto":
        if isinstance(validacion, str):
            validacion = ValidacionEntidadContacto[validacion]
        if isinstance(entidad, EntidadValue):
            id_entidad = entidad.to_id()
        else:
            id_entidad = IdEntidad.from_value(entidad)
        if isinstance(contacto, ContactoValue):
            id_contacto = contacto.to_id()
        else:
            id_contacto = IdContacto.from_value(contacto)
        usuario = IdUsuario.from_value(usuario)
        return cls(
            id_entidad=id_entidad,
            id_contacto=id_contacto,
            validacion=validacion,
            usuario=usuario,
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def id_entidad_contacto(self) -> IdEntidadContacto:
        return IdEntidadContacto.new(entidad=self.id_entidad, contacto=self.id_contacto)


class EntidadContactoCorresponde(
    EntidadContactoDomainEvent, topic_suffix="Corresponde"
):
    entidad: IdEntidad
    contacto: IdContacto
    usuario: IdUsuario

    @classmethod
    def new(cls, state: EntidadExampletate) -> "EntidadContactoCorresponde":
        assert (
            state.usuario_validacion is not None
        ), "El usuario de validación no puede ser None"
        assert (
            state.validacion == ValidacionEntidadContacto.CORRESPONDE
        ), "El estado de validación debe ser CORRESPONDE para crear este evento"
        return cls(
            id_entidad_contacto=state.id,
            entidad=state.entidad,
            contacto=state.contacto,
            usuario=state.usuario_validacion,
        )


class EntidadContactoNoCorresponde(
    EntidadContactoDomainEvent, topic_suffix="NoCorresponde"
):
    entidad: IdEntidad
    contacto: IdContacto
    usuario: IdUsuario

    @classmethod
    def new(cls, state: EntidadExampletate) -> "EntidadContactoNoCorresponde":
        assert (
            state.usuario_validacion is not None
        ), "El usuario de validación no puede ser None"
        assert (
            state.validacion == ValidacionEntidadContacto.NO_CORRESPONDE
        ), "El estado de validación debe ser NO_CORRESPONDE para crear este evento"
        return cls(
            id_entidad_contacto=state.id,
            entidad=state.entidad,
            contacto=state.contacto,
            usuario=state.usuario_validacion,
        )


class ValidarEntidadContactoHandler(
    EntidadContactoCommandHandler[ValidarEntidadContacto]
):
    def execute(
        self, command: ValidarEntidadContacto
    ) -> Iterable[TEntidadContactoEvent]:
        entidad_contacto = self.repository.get(command.id_entidad_contacto)
        evento: TEntidadContactoEvent

        if command.validacion == ValidacionEntidadContacto.CORRESPONDE:
            entidad_contacto.marcar_entidad_contacto_correcta(command.usuario)
            evento = EntidadContactoCorresponde.new(entidad_contacto.state)
        elif command.validacion == ValidacionEntidadContacto.NO_CORRESPONDE:
            entidad_contacto.marcar_entidad_contacto_incorrecta(command.usuario)
            evento = EntidadContactoNoCorresponde.new(entidad_contacto.state)
        else:
            raise DomainValueError(
                "La validación debe ser CORRESPONDE o NO_CORRESPONDE"
            )

        logger.info("EntidadContacto validado: %s", entidad_contacto.validacion)
        self.repository.save(entidad_contacto)
        snap = EntidadExamplenapshot.new(entidad_contacto.state)
        return [snap, evento]


TOPICS.register(
    EntidadContactoCorresponde,
    ValidarEntidadContacto,
    EntidadContactoNoCorresponde,
)
