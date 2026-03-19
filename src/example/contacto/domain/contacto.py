from datetime import datetime
from enum import Enum
from typing import Any, Dict, Type
from uuid import UUID

from example.contacto.domain.shared import (
    ContactoValue,
    IdContacto,
    IdUsuario,
    TipoContacto,
)
from hexagonal.application import AggregateView
from hexagonal.domain import AggregateRoot, GetById, SnapshotState, command


class Telefono(ContactoValue):
    tipo: TipoContacto = TipoContacto.TELEFONO


class Email(ContactoValue):
    tipo: TipoContacto = TipoContacto.EMAIL


ContactoValueStrategy: Dict[TipoContacto, Type[ContactoValue]] = {
    TipoContacto.TELEFONO: Telefono,
    TipoContacto.EMAIL: Email,
}


class EstadoContacto(Enum):
    SIN_VALIDAR = "sin_validar"
    CONTACTADO = "contactado"
    NO_CONTACTADO = "no_contactado"
    NO_CONTACTABLE = "no_contactable"


class Exampletate(SnapshotState[IdContacto]):
    contacto: ContactoValue
    estado: EstadoContacto
    usuario_creacion: IdUsuario | None
    usuario_validacion: IdUsuario | None
    fecha_validacion: datetime | None


class Contacto(AggregateRoot[IdContacto, Exampletate]):
    def __init__(
        self, *, contacto: ContactoValue, usuario: IdUsuario | None = None
    ) -> None:
        self.contacto: ContactoValue = contacto
        self.estado: EstadoContacto = EstadoContacto.SIN_VALIDAR
        self.usuario_creacion: IdUsuario | None = usuario
        self.usuario_validacion: IdUsuario | None = None
        self.fecha_validacion: datetime | None = None

    @classmethod
    def create_id(cls, contacto: ContactoValue, *_: Any, **__: Any) -> UUID:
        return contacto.to_id().value

    def _marcar_validacion(self, estado: EstadoContacto, usuario: IdUsuario) -> None:
        self.estado = estado
        self.usuario_validacion = usuario
        self.fecha_validacion = self.Event.create_timestamp()

    @command("marcarContactado")
    def marcar_contactado(self, usuario: IdUsuario) -> None:
        self._marcar_validacion(EstadoContacto.CONTACTADO, usuario)

    @command("marcarNoContactado")
    def marcar_no_contactado(self, usuario: IdUsuario) -> None:
        self._marcar_validacion(EstadoContacto.NO_CONTACTADO, usuario)

    @command("marcarNoContactable")
    def marcar_no_contactable(self, usuario: IdUsuario) -> None:
        self._marcar_validacion(EstadoContacto.NO_CONTACTABLE, usuario)


class ContactoView(AggregateView[Contacto]):
    pass


class GetContactoById(GetById[Contacto, IdContacto]):
    @classmethod
    def new(cls, id: IdContacto | UUID, *_: Any, **__: Any) -> "GetContactoById":
        id = IdContacto.from_value(id)
        return cls(id=id, view=ContactoView)


__all__ = [
    "Contacto",
    "ContactoValueStrategy",
    "ContactoView",
    "Email",
    "EstadoContacto",
    "Exampletate",
    "GetContactoById",
    "Telefono",
]


# class GetContactoById(GetById[Contacto, IdContacto]):
#     @classmethod
#     def new(cls, id: IdContacto | UUID, *_: Any, **__: Any):
#         id = IdContacto.from_value(id)
#         return super().new(id=id, agg_type=Contacto)
