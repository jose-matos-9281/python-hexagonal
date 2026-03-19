from typing import Any

from example.contacto.domain.entidad import Entidad, EntidadValueStrategy
from example.contacto.domain.shared import EntidadValue, TipoEntidad

from .shared import (
    EntidadCommand,
    EntidadCommandHandler,
    EntidadDomainEvent,
)


class CrearEntidad(EntidadCommand):
    entidad: EntidadValue

    @classmethod
    def new(
        cls,
        tipo_entidad: TipoEntidad | str,
        *_: Any,
        **kwargs: Any,
    ):
        if isinstance(tipo_entidad, str):
            tipo_entidad = TipoEntidad[tipo_entidad]
        entidad_value = EntidadValueStrategy[tipo_entidad].new(**kwargs)
        return cls(entidad=entidad_value)


class EntidadCreada(EntidadDomainEvent, topic_suffix="Creada"):
    tipo_entidad: TipoEntidad
    entidad: str

    @classmethod
    def new(cls, entidad: Entidad) -> "EntidadCreada":
        return cls(
            id_entidad=entidad.id,
            tipo_entidad=entidad.value.tipo,
            entidad=entidad.value.value,
        )


class CrearEntidadHandler(EntidadCommandHandler[CrearEntidad]):
    def execute(self, command: CrearEntidad):
        id_entidad = command.entidad.to_id()
        entidad = Entidad(id=id_entidad, value=command.entidad)
        self.repository.save(entidad)
        evento = EntidadCreada.new(entidad)
        return [evento]
