from typing import Any, Dict, Type
from uuid import UUID

from example.contacto.domain.shared import EntidadValue, IdEntidad, TipoEntidad
from hexagonal.domain import Entity, GetById


class NucleoAfiliado(EntidadValue):
    cd_asegurado: str
    tipo: TipoEntidad = TipoEntidad.NUCLEO

    @classmethod
    def new(cls, *_: Any, cd_asegurado: str, **__: Any):
        return cls(value=cd_asegurado, cd_asegurado=cd_asegurado)


class Afiliado(EntidadValue):
    tipo: TipoEntidad = TipoEntidad.AFILIADO
    cd_asegurado: str
    cd_dependiente: str

    @property
    def cd_afiliado(self) -> str:
        return self.value

    @classmethod
    def new(cls, *_: Any, cd_asegurado: str, cd_dependiente: str, **__: Any):
        return cls(
            value=f"{cd_asegurado}-{cd_dependiente}",
            cd_asegurado=cd_asegurado,
            cd_dependiente=cd_dependiente,
        )


EntidadValueStrategy: Dict[TipoEntidad, Type[EntidadValue]] = {
    TipoEntidad.NUCLEO: NucleoAfiliado,
    TipoEntidad.AFILIADO: Afiliado,
}


class Entidad(Entity[IdEntidad]):
    value: EntidadValue


class GetEntidadById(GetById[Entidad, IdEntidad]):
    @classmethod
    def new(cls, id: IdEntidad | UUID, *_: Any, **__: Any):
        id = IdEntidad.from_value(id)
        return super().new(id=id, agg_type=Entidad)
