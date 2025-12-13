from hexagonal.ports.drivens import TManager
from hexagonal.ports.drivers import IBaseApplication


class ApplicationProxyAdapter(IBaseApplication[TManager]):
    def __init__(self, application: IBaseApplication[TManager]):
        self._application = application

    @property
    def bus_app(self):
        return self._application.bus_app

    @property
    def bus_infrastructure(self):
        return self._application.bus_infrastructure
