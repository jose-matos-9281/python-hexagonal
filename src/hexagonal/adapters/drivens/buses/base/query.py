from typing import Any, Literal, Mapping, Type, overload

from eventsourcing.utils import get_topic

from hexagonal.application import Infrastructure
from hexagonal.domain import (
    HandlerAlreadyRegistered,
    HandlerNotRegistered,
    Query,
    QueryResult,
    QueryResults,
    TQuery,
    TView,
)
from hexagonal.ports.drivens import IQueryBus, IQueryHandler, TManager


class QueryBus(IQueryBus[TManager], Infrastructure):
    handlers: dict[str, IQueryHandler[TManager, Any, Any]]

    def initialize(self, env: Mapping[str, str]) -> None:
        self.handlers = {}
        super().initialize(env)

    def _get_name(self, query_type: Type[Query[TView]]) -> str:
        return get_topic(query_type)

    def _get_handler(
        self, query: Query[TView]
    ) -> IQueryHandler[TManager, Query[TView], TView] | None:
        name = self._get_name(query.__class__)
        return self.handlers.get(name)

    def register_handler(
        self,
        query_type: Type[TQuery],
        handler: IQueryHandler[TManager, TQuery, TView],
    ):
        self.verify()
        name = self._get_name(query_type)
        if name in self.handlers:
            raise HandlerAlreadyRegistered(f"Query: {name}")
        self.handlers[name] = handler

    def unregister_handler(self, query_type: Type[TQuery]):
        self.verify()
        name = self._get_name(query_type)
        if name in self.handlers:
            del self.handlers[name]
        else:
            raise HandlerNotRegistered(f"Query: {name}")

    @overload
    def get(self, query: Query[TView], *, one: Literal[True]) -> QueryResult[TView]: ...

    @overload
    def get(
        self,
        query: Query[TView],
        *,
        one: Literal[False] = False,
    ) -> QueryResults[TView]: ...

    def get(
        self,
        query: Query[TView],
        *,
        one: bool = False,
    ) -> QueryResult[TView] | QueryResults[TView]:
        self.verify()
        name = self._get_name(query.__class__)
        handler = self._get_handler(query)
        if not handler:
            raise HandlerNotRegistered(f"Query: {name}")
        results = handler.get(query)
        if not one:
            return results
        if len(results) == 0:
            raise ValueError("No results found")
        if len(results) > 1:
            raise ValueError("More than one result found")
        return QueryResult[TView](item=results.items[0])
