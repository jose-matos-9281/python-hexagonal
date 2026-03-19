from typing import Any, List, Optional, Type
from uuid import UUID

from example.contacto.domain.entidad import Entidad, GetEntidadById
from example.contacto.domain.shared import IdEntidad, TipoEntidad
from hexagonal.application.api import ApiCommandResponse, BaseAPI, TBaseApp
from hexagonal.domain import TEvento

from .use_cases import (
    BorrarEntidad,
    CrearEntidad,
    EntidadBorrada,
    EntidadCreada,
)


class EntidadAPI(BaseAPI[TBaseApp]):
    class Events(BaseAPI.Events):
        CREADA = EntidadCreada
        BORRADA = EntidadBorrada

    class Commands(BaseAPI.Commands):
        CREAR = CrearEntidad
        BORRAR = BorrarEntidad

    class Queries(BaseAPI.Queries):
        GET_BY_ID = GetEntidadById

    def crear(
        self,
        tipo_entidad: str | TipoEntidad,
        datos_entidad: dict[str, Any],
        *,
        events: Optional[List[Type[TEvento]]] = None,
        async_dispatch: bool = False,
        **kwargs: Any,
    ) -> ApiCommandResponse[CrearEntidad]:
        command = CrearEntidad.new(tipo_entidad, **datos_entidad)
        return self._dispatch_command(
            command,
            events=events,
            default_events=[EntidadCreada],
            to_outbox=async_dispatch,
            **kwargs,
        )

    def get(self, id_entidad: UUID | IdEntidad) -> Entidad:
        query = GetEntidadById.new(id_entidad)
        r = self.app.query_bus.get(query, one=True)
        return r.item.value

    # def get(self, id_entidad: UUID | IdEntidad) -> Entidad:
    #     bus_app = cast(Any, self.app.bus_app)
    #     return bus_app.infrastructure.contacto.entidad_repository.get(
    #         IdEntidad.from_value(id_entidad)
    #     )
    def borrar(
        self,
        id_entidad: UUID | IdEntidad,
        *,
        events: Optional[List[Type[TEvento]]] = None,
        async_dispatch: bool = False,
        **kwargs: Any,
    ) -> ApiCommandResponse[BorrarEntidad]:
        command = BorrarEntidad.new(id_entidad)
        return self._dispatch_command(
            command,
            events=events,
            default_events=[EntidadBorrada],
            to_outbox=async_dispatch,
            **kwargs,
        )
