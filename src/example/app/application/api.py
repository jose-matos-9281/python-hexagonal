from example.contacto.application import ContactoAppAPI
from hexagonal.application.api import BaseAPI, TBaseApp


class exampleAPI(BaseAPI[TBaseApp]):
    class Events(BaseAPI.Events):
        contacto = ContactoAppAPI.Events

    class Commands(BaseAPI.Commands):
        contacto = ContactoAppAPI.Commands

    class Queries(BaseAPI.Queries):
        contacto = ContactoAppAPI.Queries

    def __init__(self, app: TBaseApp):
        super().__init__(app)
        self._contacto = ContactoAppAPI(app)

    @property
    def contacto(self) -> ContactoAppAPI[TBaseApp]:
        return self._contacto
