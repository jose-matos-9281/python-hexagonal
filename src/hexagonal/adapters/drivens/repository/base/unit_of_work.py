from typing import Mapping

from eventsourcing.utils import get_topic

from hexagonal.application import InfrastructureGroup
from hexagonal.ports.drivens import IBaseRepository, IUnitOfWork, TManager


class BaseUnitOfWork(IUnitOfWork[TManager], InfrastructureGroup):
    def __init__(
        self,
        *repositories: IBaseRepository[TManager],
        connection_manager: TManager,
    ):
        self._repositories = {get_topic(repo.__class__): repo for repo in repositories}
        self._initialized = False
        self._manager = connection_manager
        super().__init__(self._manager, *repositories)

    def initialize(self, env: Mapping[str, str]) -> None:
        self._initialized = True
        self._active = False
        return super().initialize(env)

    @property
    def initialized(self) -> bool:
        return self._initialized and super().initialized

    def attach_repo(self, repo: IBaseRepository[TManager]):
        topic = get_topic(repo.__class__)
        if topic in self._repositories:
            return

        self._repositories[topic] = repo
        if self.initialized and self._active:
            repo.attach_to_unit_of_work(self)

    def detach_repo(self, repo: IBaseRepository[TManager]) -> None:
        topic = get_topic(repo.__class__)
        if topic not in self._repositories:
            return

        if self.initialized and self._active:
            repo.detach_from_unit_of_work()
        del self._repositories[topic]

    @property
    def connection_manager(self):
        return self._manager

    def __enter__(self):
        self.verify()
        if self._active:
            return self
        # get connection from manager, the connection is entered yet
        self._ctx = self._manager.start_connection()
        for repo in self._repositories.values():
            repo.attach_to_unit_of_work(self)
        self._active = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):  # type: ignore
        self._active = False
        try:
            if exc_type is None:
                self.commit()
            else:
                self.rollback()
        except Exception as e:
            # Log or handle commit/rollback errors
            raise RuntimeError(f"Failed to finalize transaction: {e}") from e
        finally:
            for repo in self._repositories.values():
                repo.detach_from_unit_of_work()
            self._ctx.__exit__(exc_type, exc_val, exc_tb)  # type: ignore
