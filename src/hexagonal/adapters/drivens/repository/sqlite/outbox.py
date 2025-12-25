"""SQLite implementation for Outbox and Inbox repositories."""

from __future__ import annotations

import logging
import sqlite3
from datetime import datetime, timezone
from typing import Any, ClassVar, Dict, Mapping
from uuid import UUID

import orjson
from eventsourcing.domain import CanCreateTimestamp
from eventsourcing.utils import strtobool

from hexagonal.adapters.drivens.mappers import MessageMapper, StoredMessage
from hexagonal.adapters.drivens.repository.base import BaseRepositoryAdapter
from hexagonal.application import InfrastructureGroup
from hexagonal.domain import CloudMessage, TMessagePayload
from hexagonal.ports.drivens import (
    IInboxRepository,
    IOutboxRepository,
    IPairInboxOutbox,
)

from .datastore import SQLiteConnectionContextManager

logger = logging.getLogger(__name__)


class SQLiteOutboxRepository(
    BaseRepositoryAdapter[SQLiteConnectionContextManager],
    IOutboxRepository[SQLiteConnectionContextManager],
):
    """SQLite implementation of the Outbox pattern repository.

    Stores outgoing messages to be published to external systems,
    ensuring at-least-once delivery semantics.
    """

    ENV: ClassVar[Dict[str, str]] = {
        "TABLE_NAME": "outbox",
        "CREATE_TABLES": "False",
    }

    def __init__(
        self,
        mapper: MessageMapper,
        connection_manager: SQLiteConnectionContextManager,
    ):
        super().__init__(connection_manager)
        self._mapper = mapper

    def initialize(self, env: Mapping[str, str]) -> None:
        super().initialize(env)
        self._table_name: str = self.env.get("TABLE_NAME", "outbox")
        create_tables = strtobool(self.env.get("CREATE_TABLES", "False"))
        self.create_table_statements: list[str] = self._create_table_statements()

        if create_tables:
            self.create_tables()

    def _create_table_statements(self) -> list[str]:
        return [
            f"""
            CREATE TABLE IF NOT EXISTS {self._table_name} (
                message_id TEXT PRIMARY KEY,
                topic TEXT NOT NULL,
                message BLOB NOT NULL,
                published_at TIMESTAMP,
                failed_at TIMESTAMP,
                error TEXT,
                retry_count INTEGER DEFAULT 0,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """,
            f"""
            CREATE INDEX IF NOT EXISTS idx_{self._table_name}_published 
            ON {self._table_name}(published_at) 
            WHERE published_at IS NULL;
            """,
            f"""
            CREATE INDEX IF NOT EXISTS idx_{self._table_name}_topic 
            ON {self._table_name}(topic);
            """,
        ]

    def create_tables(self) -> None:
        """Create the outbox table if it doesn't exist."""
        with self.connection_manager.datastore.transaction(commit=True) as cursor:
            for statement in self.create_table_statements:
                cursor.execute(statement)
                logger.debug("Outbox table created: %s", self._table_name)

    def _get_stored_message(self, message: CloudMessage[Any]) -> tuple[str, str, bytes]:
        stored = self._mapper.to_stored_message(message.payload)
        serialized_message: dict[str, Any] = {
            "type": message.type,
            "metadata": message.metadata,
            "correlation_id": str(message.correlation_id)
            if message.correlation_id
            else None,
            "causation_id": str(message.causation_id) if message.causation_id else None,
            "occurred_at": message.occurred_at.isoformat(),
            "payload_topic": stored.topic,
            "payload_state": stored.state.hex(),
        }

        return (
            str(message.message_id),
            stored.topic,
            orjson.dumps(serialized_message),
        )

    def save(self, *messages: CloudMessage[Any]) -> None:
        """Save messages to the outbox table."""
        self.verify()
        if not messages:
            return

        to_stored_message = map(self._get_stored_message, messages)

        with self.connection_manager.cursor() as cursor:
            cursor.executemany(
                f"""
                    INSERT OR IGNORE INTO {self._table_name} (
                        message_id,
                        topic,
                        message,
                        created_at
                    ) VALUES (?, ?, ?, ?)
                    """,
                [
                    (
                        mid,
                        topic,
                        message,
                        CanCreateTimestamp.create_timestamp().isoformat(
                            " ", "milliseconds"
                        ),
                    )
                    for mid, topic, message in to_stored_message
                ],
            )

    def fetch_pending(self, limit: int | None = None) -> list[CloudMessage[Any]]:
        """Fetch pending messages that haven't been published yet."""
        self.verify()
        with self.connection_manager.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT 
                    message_id,
                    topic,
                    message
                FROM {self._table_name}
                WHERE published_at IS NULL
                  AND (failed_at IS NULL OR retry_count < 3)
                ORDER BY created_at ASC
                {"LIMIT ?" if limit is not None else ""}
                """,
                (limit,) if limit is not None else (),
            )
            rows = cursor.fetchall()

        messages: list[CloudMessage[Any]] = []
        for row in rows:
            try:
                # Reconstruct the message from stored data
                stored_payload_bytes: bytes = row[2]
                data = orjson.loads(stored_payload_bytes)
                payload_state = bytes.fromhex(data.pop("payload_state"))
                payload_topic = data.pop("payload_topic")
                stored_message = StoredMessage(payload_topic, payload_state)
                payload = self._mapper.to_message(stored_message)
                assert isinstance(payload, TMessagePayload)
                data["payload"] = payload
                data["message_id"] = row[0]
                cloud_message = CloudMessage[type(payload)](**data)  # type: ignore
                messages.append(cloud_message)
            except Exception as e:
                logger.error(
                    "Failed to deserialize message %s: %s", row[0], e, exc_info=True
                )
                continue

        return messages

    def mark_as_published(self, *message_ids: UUID) -> None:
        """Mark messages as successfully published."""
        self.verify()
        if not message_ids:
            return

        with self.cursor() as cursor:
            now = datetime.now(timezone.utc).isoformat(" ", "seconds")
            cursor.executemany(
                f"""
                UPDATE {self._table_name}
                SET published_at = ?
                WHERE message_id = ?
                """,
                [(now, str(mid)) for mid in message_ids],
            )

    def cursor(self):
        return self._connection_manager.datastore.transaction(commit=True)

    def mark_as_failed(self, *message_ids: UUID, error: str) -> None:
        """Mark messages as failed and increment retry count."""
        self.verify()
        if not message_ids:
            return

        with self.cursor() as cursor:
            cursor.executemany(
                f"""
                UPDATE {self._table_name}
                SET 
                    failed_at = ?,
                    error = ?,
                    retry_count = retry_count + 1
                WHERE message_id = ?
                """,
                [
                    (datetime.now(timezone.utc).isoformat(), error, str(mid))
                    for mid in message_ids
                ],
            )


class SQLiteInboxRepository(
    BaseRepositoryAdapter[SQLiteConnectionContextManager],
    IInboxRepository[SQLiteConnectionContextManager],
):
    """SQLite implementation of the Inbox pattern repository.

    Ensures idempotent message processing by tracking which messages
    have been processed by which handlers.
    """

    ENV: ClassVar[Dict[str, str]] = {
        "TABLE_NAME": "inbox",
        "CREATE_TABLES": "False",
    }

    def cursor(self):
        return self._connection_manager.datastore.transaction(commit=True)

    def __init__(
        self,
        mapper: MessageMapper,
        connection_manager: SQLiteConnectionContextManager,
    ):
        super().__init__(connection_manager)
        self._mapper = mapper

    def initialize(self, env: Mapping[str, str]) -> None:
        super().initialize(env)
        self._table_name: str = self.env.get("TABLE_NAME", "inbox")
        create_tables = strtobool(self.env.get("CREATE_TABLES", "False"))
        self.create_table_statements: list[str] = self._create_table_statements()

        if create_tables:
            self.create_tables()

    def _create_table_statements(self) -> list[str]:
        return [
            f"""
            CREATE TABLE IF NOT EXISTS {self._table_name} (
                message_id TEXT NOT NULL,
                handler TEXT NOT NULL,
                received_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                processed_at TIMESTAMP,
                error TEXT,
                retry_count INTEGER NOT NULL DEFAULT 0,
                failed_at TIMESTAMP,
                PRIMARY KEY (message_id, handler)
            );
            """,
            f"""
            CREATE INDEX IF NOT EXISTS idx_{self._table_name}_processed 
            ON {self._table_name}(processed_at) 
            WHERE processed_at IS NULL;
            """,
        ]

    def create_tables(self) -> None:
        """Create the inbox table if it doesn't exist."""
        with self.cursor() as cursor:
            for statement in self.create_table_statements:
                cursor.execute(statement)
                logger.debug("Inbox table created: %s", self._table_name)

    def register_message(
        self, message: CloudMessage[Any], handler: str, max_retries: int = 3
    ) -> bool:
        """Register a message for processing.

        Returns:
            True if the message was already registered (duplicate)
            False if this is a new message
        """
        self.verify()
        with self.cursor() as cursor:
            try:
                cursor.execute(
                    f"""
                    INSERT INTO {self._table_name} (message_id, handler, received_at)
                    VALUES (?, ?, ?)
                    """,
                    (
                        str(message.message_id),
                        handler,
                        CanCreateTimestamp.create_timestamp().isoformat(
                            " ", "milliseconds"
                        ),
                    ),
                )
                # Successfully inserted, so it's a new message
                return False
            except sqlite3.IntegrityError:
                # Primary key violation means it's a duplicate
                cursor.execute(
                    f"""
                    select 
                        message_id,
                        handler,
                        processed_at,
                        error,
                        retry_count,
                        failed_at
                    from {self._table_name}
                    where message_id = ? 
                        and handler = ?
                        and processed_at is null 
                        and (failed_at is null or retry_count < ?)
                    """,
                    (str(message.message_id), handler, max_retries),
                )
                row = cursor.fetchone()
                if row is not None:
                    return False

                return True

    def mark_as_processed(self, message_id: UUID, handler: str) -> None:
        """Mark a message as successfully processed by a handler."""
        self.verify()
        with self.cursor() as cursor:
            cursor.execute(
                f"""
                UPDATE {self._table_name}
                SET processed_at = ?
                WHERE message_id = ? AND handler = ?
                """,
                (
                    CanCreateTimestamp.create_timestamp().isoformat(
                        " ", "milliseconds"
                    ),
                    str(message_id),
                    handler,
                ),
            )

    def mark_as_failed(self, message_id: UUID, handler: str, error: str) -> None:
        """Mark a message as failed by a handler."""
        self.verify()
        with self.cursor() as cursor:
            cursor.execute(
                f"""
                UPDATE {self._table_name}
                SET failed_at = ?, error = ?, retry_count = retry_count + 1
                WHERE message_id = ? AND handler = ?
                """,
                (
                    CanCreateTimestamp.create_timestamp().isoformat(
                        " ", "milliseconds"
                    ),
                    error,
                    str(message_id),
                    handler,
                ),
            )


class SQLitePairInboxOutbox(
    InfrastructureGroup,
    IPairInboxOutbox[SQLiteConnectionContextManager],
):
    def __init__(
        self,
        mapper: MessageMapper,
        connection_manager: SQLiteConnectionContextManager,
    ):
        self._inbox = SQLiteInboxRepository(mapper, connection_manager)
        self._outbox = SQLiteOutboxRepository(mapper, connection_manager)
        super().__init__(self._inbox, self._outbox)

    @property
    def inbox(self) -> IInboxRepository[SQLiteConnectionContextManager]:
        return self._inbox

    @property
    def outbox(self) -> IOutboxRepository[SQLiteConnectionContextManager]:
        return self._outbox
