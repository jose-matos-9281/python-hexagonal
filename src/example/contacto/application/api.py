from hexagonal.application.api import BaseAPI, TBaseApp

from .contacto import ContactoAPI
from .entidad import EntidadAPI
from .entidad_contacto import EntidadContactoAPI


class ContactoAppAPI(BaseAPI[TBaseApp]):
    class Events(BaseAPI.Events):
        contacto = ContactoAPI.Events
        entidad = EntidadAPI.Events
        entidad_contacto = EntidadContactoAPI.Events

    class Commands(BaseAPI.Commands):
        contacto = ContactoAPI.Commands
        entidad = EntidadAPI.Commands
        entidad_contacto = EntidadContactoAPI.Commands

    class Queries(BaseAPI.Queries):
        contacto = ContactoAPI.Queries
        entidad = EntidadAPI.Queries
        entidad_contacto = EntidadContactoAPI.Queries

    def __init__(self, app: TBaseApp):
        super().__init__(app)
        self._contacto = ContactoAPI(app)
        self._entidad = EntidadAPI(app)
        self._entidad_contacto = EntidadContactoAPI(app)

    @property
    def contacto(self) -> ContactoAPI[TBaseApp]:
        return self._contacto

    @property
    def entidad(self) -> EntidadAPI[TBaseApp]:
        return self._entidad

    @property
    def entidad_contacto(self) -> EntidadContactoAPI[TBaseApp]:
        return self._entidad_contacto
