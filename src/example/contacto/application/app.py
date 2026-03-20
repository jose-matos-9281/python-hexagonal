from example.app.ports.drivens import IexampleInfrastructure
from example.contacto.ports.drivens import IAppContactoInfrastructure
from example.contacto.ports.drivers import IContactoApp
from hexagonal.application import BusAppGroup
from hexagonal.ports.drivens import TManager

from .contacto import ContactoBusApp
from .entidad import EntidadBusApp
from .entidad_contacto import EntidadContactoBusApp
from .integration_handlers import IntegrationContactoBusApp


class ContactoApp(IContactoApp[TManager], BusAppGroup[TManager]):
    def __init__(
        self,
        infrastructure: IAppContactoInfrastructure[TManager],
        scope_provider: IexampleInfrastructure[TManager],
    ):
        infrastructure.verify()
        self._infra = infrastructure
        contacto = ContactoBusApp(infrastructure.uow, scope_provider)
        entidad = EntidadBusApp(infrastructure.uow, scope_provider)
        entidad_contacto = EntidadContactoBusApp(infrastructure.uow, scope_provider)
        integrations = IntegrationContactoBusApp(infrastructure.uow, scope_provider)
        super().__init__(
            infrastructure.uow,
            contacto,
            entidad,
            entidad_contacto,
            integrations,
        )

    @property
    def infrastructure(self) -> IAppContactoInfrastructure[TManager]:
        return self._infra
