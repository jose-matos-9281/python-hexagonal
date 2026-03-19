from typing import Any, Iterable
from uuid import UUID

from example.contacto.domain.shared import EntidadValue, IdEntidad

from .shared import (
    EntidadCommand,
    EntidadCommandHandler,
    EntidadDomainEvent,
    TEntidadEvent,
)


class BorrarEntidad(EntidadCommand):
    id_entidad: IdEntidad

    @classmethod
    def new(
        cls,
        id_entidad: IdEntidad | EntidadValue | UUID,
        *_: Any,
        **__: Any,
    ):
        _id = id_entidad.to_id() if isinstance(id_entidad, EntidadValue) else id_entidad
        id_entidad = IdEntidad.from_value(_id)
        return cls(id_entidad=id_entidad)


class EntidadBorrada(EntidadDomainEvent, topic_suffix="Borrada"):
    @classmethod
    def new(cls, id_entidad: IdEntidad) -> "EntidadBorrada":
        return cls(id_entidad=id_entidad)


class BorrarEntidadHandler(EntidadCommandHandler[BorrarEntidad]):
    def execute(self, command: BorrarEntidad) -> Iterable[TEntidadEvent]:
        self.repository.delete(command.id_entidad)
        evento = EntidadBorrada.new(command.id_entidad)
        return [evento]
