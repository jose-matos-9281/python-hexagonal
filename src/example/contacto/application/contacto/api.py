from typing import Any, List, Optional, Type
from uuid import UUID

from example.contacto.domain.contacto import (
    Contacto,
    EstadoContacto,
    Exampletate,
    GetContactoById,
)
from example.contacto.domain.shared import TipoContacto
from hexagonal.application import BaseAPI, TBaseApp
from hexagonal.application.api import ApiCommandResponse
from hexagonal.domain import AggregateSnapshot, TEvento

from .use_cases import (
    ContactoContactado,
    ContactoCreado,
    ContactoNoContactable,
    ContactoNoContactado,
    CrearContacto,
    Examplenapshot,
    ValidarContacto,
)


class ContactoAPI(BaseAPI[TBaseApp]):
    class Events(BaseAPI.Events):
        SNAPSHOT = Examplenapshot
        CREADO = ContactoCreado
        CONTACTADO = ContactoContactado
        NO_CONTACTADO = ContactoNoContactado
        NO_CONTACTABLE = ContactoNoContactable
        AGGREGATE = AggregateSnapshot[Exampletate]

    class Commands(BaseAPI.Commands):
        CREAR = CrearContacto
        VALIDAR = ValidarContacto

    class Queries(BaseAPI.Queries):
        GET_BY_ID = GetContactoById

    def crear(
        self,
        tipo_contacto: str | TipoContacto,
        contacto: str,
        usuario: UUID | None = None,
        *,
        events: Optional[List[Type[TEvento]]] = None,
        async_dispatch: bool = False,
        **kwargs: Any,
    ) -> ApiCommandResponse[CrearContacto]:
        command = CrearContacto.new(tipo_contacto, contacto, usuario)
        return self._dispatch_command(
            command,
            events=events,
            default_events=[Examplenapshot, ContactoCreado],
            to_outbox=async_dispatch,
            **kwargs,
        )

    def get(self, id_contacto: UUID) -> Contacto:
        return self._get_aggregate(id_contacto, GetContactoById)

    def validar(
        self,
        id_contacto: UUID,
        validacion: EstadoContacto,
        usuario: UUID,
        *,
        events: Optional[List[Type[TEvento]]] = None,
        async_dispatch: bool = False,
        **kwargs: Any,
    ) -> ApiCommandResponse[ValidarContacto]:
        command = ValidarContacto.new(id_contacto, validacion, usuario)
        return self._dispatch_command(
            command,
            events=events,
            default_events=[
                Examplenapshot,
                ContactoContactado,
                ContactoNoContactado,
                ContactoNoContactable,
            ],
            to_outbox=async_dispatch,
            **kwargs,
        )
