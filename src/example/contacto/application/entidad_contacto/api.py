from typing import Any, List, Optional, Type
from uuid import UUID

from example.contacto.domain.entidad_contacto import ValidacionEntidadContacto
from hexagonal.application.api import BaseAPI, TBaseApp
from hexagonal.domain import TEvento

from .use_cases import (
    CrearEntidadContacto,
    EntidadContactoCorresponde,
    EntidadContactoCreado,
    EntidadContactoNoCorresponde,
    EntidadExamplenapshot,
    GetEntidadContactoById,
    ValidarEntidadContacto,
)


class EntidadContactoAPI(BaseAPI[TBaseApp]):
    class Events(BaseAPI.Events):
        SNAPSHOT = EntidadExamplenapshot
        CREADO = EntidadContactoCreado
        CORRESPONDE = EntidadContactoCorresponde
        NO_CORRESPONDE = EntidadContactoNoCorresponde

    class Commands(BaseAPI.Commands):
        CREAR = CrearEntidadContacto
        VALIDAR = ValidarEntidadContacto

    class Queries(BaseAPI.Queries):
        GET_BY_ID = GetEntidadContactoById

    def crear(
        self,
        entidad: UUID,
        contacto: UUID,
        usuario: UUID | None = None,
        *,
        events: Optional[List[Type[TEvento]]] = None,
        async_dispatch: bool = False,
        **kwargs: Any,
    ):
        command = CrearEntidadContacto.new(entidad, contacto, usuario)
        return self._dispatch_command(
            command,
            events=events,
            default_events=[EntidadExamplenapshot, EntidadContactoCreado],
            to_outbox=async_dispatch,
            **kwargs,
        )

    def get(self, id_entidad_contacto: UUID):
        return self._get_aggregate(id_entidad_contacto, GetEntidadContactoById)

    def validar(
        self,
        id_entidad: UUID,
        id_contacto: UUID,
        validacion: ValidacionEntidadContacto,
        usuario: UUID,
        *,
        events: Optional[List[Type[TEvento]]] = None,
        async_dispatch: bool = False,
        **kwargs: Any,
    ):
        command = ValidarEntidadContacto.new(
            id_entidad,
            id_contacto,
            validacion,
            usuario,
        )
        return self._dispatch_command(
            command,
            events=events,
            default_events=[
                EntidadExamplenapshot,
                EntidadContactoCorresponde,
                EntidadContactoNoCorresponde,
            ],
            to_outbox=async_dispatch,
            **kwargs,
        )
