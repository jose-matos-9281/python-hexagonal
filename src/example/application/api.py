from example.application.example.api import ExampleAPI
from hexagonal.application.api import BaseAPI, TBaseApp


class API(BaseAPI[TBaseApp]):
    def __init__(self, app: TBaseApp):
        super().__init__(app)
        self._example = ExampleAPI(app)

    @property
    def example(self) -> ExampleAPI[TBaseApp]:
        return self._example
