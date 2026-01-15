from typing import Any, List, Optional, Type
from uuid import UUID

from hexagonal.application.api import BaseAPI, TBaseApp
from hexagonal.domain.base import TEvento

from .commands import CambiarNombreExample, CreateExample, DeleteExample
from .events import ExampleDeleted, ExampleSnapshot
from .queries import GetExampleById


class ExampleAPI(BaseAPI[TBaseApp]):
    def crear(
        self,
        nombre: str,
        *,
        events: Optional[List[Type[TEvento]]] = None,
        async_dispatch: bool = False,
        **kwargs: Any,
    ):
        command = CreateExample.new(nombre=nombre)
        return self._dispatch_command(
            command,
            events=events,
            default_events=[ExampleSnapshot],
            async_dispatch=async_dispatch,
            **kwargs,
        )

    def cambiar_nombre(
        self,
        id: UUID,
        nuevo_nombre: str,
        *,
        events: Optional[List[Type[TEvento]]] = None,
        async_dispatch: bool = False,
        **kwargs: Any,
    ):
        command = CambiarNombreExample.new(id=id, nuevo_nombre=nuevo_nombre)
        return self._dispatch_command(
            command,
            events=events,
            default_events=[ExampleSnapshot],
            async_dispatch=async_dispatch,
            **kwargs,
        )

    def eliminar(
        self,
        id: UUID,
        *,
        events: Optional[List[Type[TEvento]]] = None,
        async_dispatch: bool = False,
        **kwargs: Any,
    ):
        command = DeleteExample.new(id=id)
        return self._dispatch_command(
            command,
            events=events,
            default_events=[ExampleDeleted],
            async_dispatch=async_dispatch,
            **kwargs,
        )

    def get(
        self,
        id: UUID,
        **kwargs: Any,
    ):
        return self._get_aggregate(id, GetExampleById)
