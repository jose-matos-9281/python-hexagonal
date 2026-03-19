from datetime import datetime
from enum import Enum
from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid5

from example.contacto.domain.shared import IdContacto, IdEntidad, IdUsuario
from hexagonal.domain import (
    AggregateRoot,
    GetById,
    IdValueObject,
    SnapshotState,
    command,
)


class IdEntidadContacto(IdValueObject):
    @classmethod
    def new(
        cls,
        *_: Any,
        entidad: IdEntidad | UUID,
        contacto: IdContacto | UUID,
        **__: Any,
    ):
        entidad = IdEntidad.from_value(entidad)
        contacto = IdContacto.from_value(contacto)
        return cls(
            value=uuid5(
                NAMESPACE_URL,
                f"entidades/{entidad.value}/example/{contacto.value}",
            )
        )


class ValidacionEntidadContacto(Enum):
    NO_VALIDADO = "no_validado"
    CORRESPONDE = "corresponde"
    NO_CORRESPONDE = "no_corresponde"


class EntidadExampletate(SnapshotState[IdEntidadContacto]):
    id_entidad_contacto: IdEntidadContacto
    entidad: IdEntidad
    contacto: IdContacto
    validacion: ValidacionEntidadContacto
    usuario_creacion: IdUsuario | None
    usuario_validacion: IdUsuario | None
    fecha_validacion: datetime | None


class EntidadContacto(AggregateRoot[IdEntidadContacto, EntidadExampletate]):
    def __init__(
        self,
        *,
        entidad: IdEntidad,
        contacto: IdContacto,
        usuario: IdUsuario | None = None,
    ) -> None:
        self.entidad: IdEntidad = entidad
        self.contacto: IdContacto = contacto
        self.validacion: ValidacionEntidadContacto = (
            ValidacionEntidadContacto.NO_VALIDADO
        )
        self.usuario_creacion: IdUsuario | None = usuario
        self.fecha_validacion: datetime | None = None
        self.usuario_validacion: IdUsuario | None = None

    @classmethod
    def create_id(cls, entidad: IdEntidad, contacto: IdContacto, *_, **__: Any):
        return super().create_id(entidad=entidad, contacto=contacto)

    def _marcar_validacion(
        self, validacion: ValidacionEntidadContacto, usuario: IdUsuario
    ):
        self.validacion = validacion
        self.usuario_validacion = usuario
        self.fecha_validacion = self.Event.create_timestamp()

    @command("marcarEntidadContactoCorrecta")
    def marcar_entidad_contacto_correcta(self, usuario: IdUsuario):
        self._marcar_validacion(ValidacionEntidadContacto.CORRESPONDE, usuario)

    @command("marcarEntidadContactoIncorrecta")
    def marcar_entidad_contacto_incorrecta(self, usuario: IdUsuario):
        self._marcar_validacion(ValidacionEntidadContacto.NO_CORRESPONDE, usuario)


class GetEntidadContactoById(GetById[EntidadContacto, IdEntidadContacto]):
    @classmethod
    def new(cls, id: IdEntidadContacto | UUID, *_: Any, **__: Any):
        id = IdEntidadContacto.from_value(id)
        return super().new(id=id, agg_type=EntidadContacto)
