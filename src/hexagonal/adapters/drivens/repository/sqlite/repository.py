"""SQLite repository adapter for event-sourced aggregates."""
# pyright: reportMissingTypeStubs=false, reportUnknownArgumentType=false, reportMissingParameterType=none, reportGeneralTypeIssues=none

from __future__ import annotations

import logging
import sqlite3
from typing import Any, ClassVar, Dict, Mapping, Sequence, Tuple, TypeVar, Union, cast
from uuid import UUID

from eventsourcing.domain import CanMutateAggregate
from eventsourcing.persistence import StoredEvent
from eventsourcing.utils import strtobool

from hexagonal.adapters.drivens.repository.base import BaseAggregateRepositoryAdapter
from hexagonal.domain import (
    AggregateNotFound,
    AggregateRoot,
    AggregateSnapshot,
    AggregateVersionMismatch,
    SnapshotState,
    TIdEntity,
)

from .datastore import SQLiteConnectionContextManager

# Type aliases
SQLiteRow = Dict[str, Any]
SQLiteParams = Union[Tuple[Any, ...], Dict[str, Any]]
TAggregate = TypeVar("TAggregate", bound=AggregateRoot[Any, Any])

logger = logging.getLogger(__name__)


class SQLiteRepositoryAdapter(
    BaseAggregateRepositoryAdapter[
        SQLiteConnectionContextManager, TAggregate, TIdEntity
    ]
):
    """SQLite repository adapter for event-sourced aggregates.

    This adapter implements the IRepository interface using SQLite as the backing store.
    It handles the persistence and retrieval of event-sourced aggregates, including
    snapshotting and event history.

    Args:
        datastore: The SQLite datastore to use for database connections
        mapper: Mapper for converting between domain and persistence models
        create_tables: If True, create the required database tables on initialization
        table_name: Base name for the database tables
        (will append _snapshots and _events)
    """

    ENV: ClassVar[Dict[str, str]] = {
        "TABLE_NAME": "aggregates",
        "CREATE_TABLES": "False",
    }

    def initialize(self, env: Mapping[str, str]) -> None:
        super().initialize(env)
        self._current_connection: sqlite3.Connection | None = None
        self._table_name: str = self.env.get("TABLE_NAME", "aggregates")
        self._schema_name: str = self.env.get("SCHEMA_NAME", "anomatrace")
        create_tables = strtobool(self.env.get("CREATE_TABLES", "False"))
        self.create_table_statements: list[str] = self._create_table_statements()

        if create_tables:
            self.create_tables()

    def _create_table_statements(self) -> list[str]:
        complete_table_name = self._get_table_name()
        complete_event_history = self._get_event_history_table_name()

        return [
            f"""
            CREATE TABLE IF NOT EXISTS {complete_table_name} (
                originator_id UUID NOT NULL,
                aggregate_name TEXT NOT NULL,
                originator_version INTEGER NOT NULL,
                topic TEXT NOT NULL,
                state BLOB NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                PRIMARY KEY (originator_id, aggregate_name)
            );
            """,
            f"""
            CREATE TABLE IF NOT EXISTS {complete_event_history} (
                originator_id UUID NOT NULL,
                aggregate_name TEXT NOT NULL,
                originator_version INTEGER NOT NULL,
                topic TEXT NOT NULL,
                state BLOB NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                PRIMARY KEY (originator_id, aggregate_name, originator_version)
            );
            """,
        ]

    def create_tables(self) -> None:
        with self.connection_manager.datastore.transaction(commit=True) as cursor:
            for statement in self.create_table_statements:
                logger.debug("Table created: %s", self._get_table_name())
                cursor.execute(statement)

    def _get_table_name(self) -> str:
        return f"aggregates_{self._table_name}"

    def _get_event_history_table_name(self) -> str:
        return f"aggregates_{self._table_name}_events"

    def _verify_new_aggregate(
        self, cursor: sqlite3.Cursor, aggregate: TAggregate
    ) -> Tuple[Sequence[CanMutateAggregate[UUID]], bool]:
        actual_agg = self._get_aggregate(cursor, aggregate.value_id)
        eventos = aggregate.collect_events()
        if actual_agg is None:
            return eventos, True
        if actual_agg.originator_version != aggregate.version - len(eventos):
            raise AggregateVersionMismatch(
                f"Aggregate {self.aggregate_name} with id {aggregate.value_id}"
                " has a different version"
            )
        return eventos, False

    def _insert_snapshot(
        self, cursor: sqlite3.Cursor, snap: AggregateSnapshot[SnapshotState[TIdEntity]]
    ) -> None:
        stored_event = self._mapper.to_stored_event(snap)
        complete_table_name = self._get_table_name()
        cursor.execute(
            f"""
            INSERT INTO {complete_table_name} (
                originator_id, 
                aggregate_name, 
                originator_version, 
                topic, 
                state,
                timestamp) 
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                str(stored_event.originator_id),
                self.aggregate_name,
                stored_event.originator_version,
                stored_event.topic,
                stored_event.state,
                snap.timestamp.isoformat(" ", "milliseconds"),
            ),
        )

    def _update_snapshot(
        self, cursor: sqlite3.Cursor, snap: AggregateSnapshot[SnapshotState[TIdEntity]]
    ) -> None:
        stored_event = self._mapper.to_stored_event(snap)
        complete_table_name = self._get_table_name()
        cursor.execute(
            f"""
            UPDATE {complete_table_name} 
            SET 
                originator_version = ?, 
                topic = ?, 
                state = ?,
                timestamp = ? 
            WHERE originator_id = ? 
            AND aggregate_name = ?
            """,
            (
                stored_event.originator_version,
                stored_event.topic,
                stored_event.state,
                snap.timestamp.isoformat(" ", "milliseconds"),
                str(stored_event.originator_id),
                self.aggregate_name,
            ),
        )

    def _save_event_history(
        self, cursor: sqlite3.Cursor, events: Sequence[CanMutateAggregate[UUID]]
    ) -> None:
        complete_event_history = self._get_event_history_table_name()
        stored_events = list(
            zip(
                map(self._mapper.to_stored_event, events),
                (e.timestamp for e in events),
                strict=True,
            )
        )
        cursor.executemany(
            f"""
                INSERT INTO {complete_event_history} (
                    originator_id, 
                    aggregate_name, 
                    originator_version, 
                    topic, 
                    state,
                    timestamp) 
                VALUES (?, ?, ?, ?, ?, ?)
                """,
            [
                (
                    str(stored_event.originator_id),
                    self.aggregate_name,
                    stored_event.originator_version,
                    stored_event.topic,
                    stored_event.state,
                    timestamp.isoformat(" ", "milliseconds"),
                )
                for stored_event, timestamp in stored_events
            ],  # type: ignore
        )

    def save(self, aggregate: TAggregate) -> None:
        self.verify()
        with self.connection_manager.cursor() as cursor:
            eventos, new = self._verify_new_aggregate(cursor, aggregate)
            snapshot = aggregate.take_snapshot()
            if new:
                self._insert_snapshot(cursor, snapshot)
            else:
                self._update_snapshot(cursor, snapshot)
            self._save_event_history(cursor, eventos)
            agg = self._get_aggregate(cursor, aggregate.value_id)
            assert agg is not None

    def _get_aggregate(
        self, cursor: sqlite3.Cursor, id: TIdEntity
    ) -> StoredEvent | None:
        complete_table_name = self._get_table_name()
        cursor.execute(
            f"""
            SELECT 
                originator_id, 
                originator_version, 
                topic, 
                state 
            FROM {complete_table_name} 
            WHERE originator_id = ? 
            AND aggregate_name = ?
            LIMIT 1
            """,
            (str(id.value), self.aggregate_name),
        )
        data: tuple[str, int, str, bytes] | None = cursor.fetchone()
        if data is None:
            return None
        stored_event: StoredEvent = StoredEvent(
            originator_id=data[0],
            originator_version=data[1],
            topic=data[2],
            state=data[3],
        )
        return stored_event

    def get(self, id: TIdEntity) -> TAggregate:
        self.verify()
        with self.connection_manager.cursor() as cursor:
            stored_event = self._get_aggregate(cursor, id)
        if stored_event is None:
            raise AggregateNotFound(
                f"Aggregate {self.aggregate_name} with id {id} not found"
            )
        snap_event = self._mapper.to_domain_event(stored_event)
        assert isinstance(snap_event, self._type_of_aggregate.Snapshot)
        return cast(TAggregate, snap_event.mutate(None))

    def _delete(self, cursor: sqlite3.Cursor, id: TIdEntity) -> None:
        complete_table_name = self._get_table_name()
        cursor.execute(
            f"""
            DELETE FROM {complete_table_name} 
            WHERE originator_id = ? 
            AND aggregate_name = ?
            """,
            (str(id.value), self.aggregate_name),
        )

    def delete(self, id: TIdEntity) -> TAggregate:
        self.verify()
        agg = self.get(id)

        agg.trigger_event(event_class=agg.Deleted)
        events = agg.collect_events()
        with self.connection_manager.cursor() as cursor:
            self._save_event_history(cursor, events)
            self._delete(cursor, id)
        return agg
