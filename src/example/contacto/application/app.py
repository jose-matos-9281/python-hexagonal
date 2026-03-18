from example.contacto.ports.drivens import IAppContactoInfrastructure
from example.contacto.ports.drivers import IContactoApp
from hexagonal.application import BusAppGroup
from hexagonal.ports.drivens import TManager

from .contacto import ContactoBusApp
from .entidad import EntidadBusApp
from .entidad_contacto import EntidadContactoBusApp
from .integration_handlers import IntegrationContactoBusApp


class ContactoApp(IContactoApp[TManager], BusAppGroup[TManager]):
    def __init__(self, infrastructure: IAppContactoInfrastructure[TManager]):
        infrastructure.verify()
        self._infra = infrastructure
        contacto = ContactoBusApp(
            infrastructure.uow,
            infrastructure.contacto_repository,
        )
        entidad = EntidadBusApp(
            infrastructure.uow,
            infrastructure.entidad_repository,
        )
        entidad_contacto = EntidadContactoBusApp(
            infrastructure.uow,
            infrastructure.entidad_contacto_repository,
        )
        integrations = IntegrationContactoBusApp(
            infrastructure.uow,
            infrastructure.contacto_repository,
        )
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
