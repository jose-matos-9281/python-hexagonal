from enum import Enum
from typing import Any, Self
from uuid import NAMESPACE_URL, uuid5

from hexagonal.domain import ExternalId, IdValueObject, ValueObject


class TipoContacto(Enum):
    TELEFONO = "telefono"
    EMAIL = "email"


class TipoEntidad(Enum):
    AFILIADO = "afiliado"
    NUCLEO = "nucleo"


class ContactoValue(ValueObject[str]):
    tipo: TipoContacto

    def to_id(self) -> "IdContacto":
        return IdContacto.new(contacto=self)


class EntidadValue(ValueObject[str]):
    tipo: TipoEntidad

    def to_id(self) -> "IdEntidad":
        return IdEntidad.new(entidad=self)


class IdContacto(IdValueObject):
    @classmethod
    def new(cls, *_: Any, contacto: ContactoValue, **__: Any) -> Self:
        return cls(
            value=uuid5(
                NAMESPACE_URL, f"example/{contacto.tipo.value}/{contacto.value}"
            )
        )


class IdEntidad(IdValueObject):
    @classmethod
    def new(cls, *_: Any, entidad: EntidadValue, **__: Any) -> Self:
        return cls(
            value=uuid5(
                NAMESPACE_URL, f"entidades/{entidad.tipo.value}/{entidad.value}"
            )
        )


class IdUsuario(ExternalId): ...


__all__ = [
    "ContactoValue",
    "EntidadValue",
    "IdContacto",
    "IdEntidad",
    "IdUsuario",
    "TipoContacto",
    "TipoEntidad",
]
