"""SQLAlchemy implementation for Outbox and Inbox repositories."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, ClassVar, Dict, Mapping
from uuid import UUID

import orjson
from eventsourcing.domain import CanCreateTimestamp
from eventsourcing.utils import strtobool
from sqlalchemy import insert, select, update
from sqlalchemy.exc import IntegrityError

from hexagonal.adapters.drivens.mappers import MessageMapper, StoredMessage
from hexagonal.adapters.drivens.repository.base import BaseRepositoryAdapter
from hexagonal.application import InfrastructureGroup
from hexagonal.domain import CloudMessage, TMessagePayload
from hexagonal.ports.drivens import (
    IInboxRepository,
    IOutboxRepository,
    IPairInboxOutbox,
)

from .datastore import SQLAlchemyConnectionContextManager
from .models import create_inbox_table, create_outbox_table

logger = logging.getLogger(__name__)


class SQLAlchemyOutboxRepository(
    BaseRepositoryAdapter[SQLAlchemyConnectionContextManager],
    IOutboxRepository[SQLAlchemyConnectionContextManager],
):
    """SQLAlchemy implementation of the Outbox pattern repository.

    Stores outgoing messages to be published to external systems,
    ensuring at-least-once delivery semantics. Supports multiple
    database backends through SQLAlchemy.
    """

    ENV: ClassVar[Dict[str, str]] = {
        "TABLE_NAME": "outbox",
        "CREATE_TABLES": "False",
    }

    def __init__(
        self,
        mapper: MessageMapper,
        connection_manager: SQLAlchemyConnectionContextManager,
    ):
        """Initialize outbox repository.

        Args:
            mapper: Message mapper for serialization/deserialization
            connection_manager: SQLAlchemy connection context manager
        """
        super().__init__(connection_manager)
        self._mapper = mapper

    def initialize(self, env: Mapping[str, str]) -> None:
        """Initialize the repository from environment variables.

        Args:
            env: Environment variables mapping

        Environment variables:
            TABLE_NAME: Name for the outbox table (default: outbox)
            SCHEMA_NAME: Database schema name (optional)
            CREATE_TABLES: If True, create tables on initialization (default: False)
        """
        super().initialize(env)
        self._table_name: str = self.env.get("TABLE_NAME", "outbox")
        self._schema_name: str | None = self.env.get("SCHEMA_NAME")
        create_tables = strtobool(self.env.get("CREATE_TABLES", "False"))

        # Create table object
        self._outbox_table = create_outbox_table(self._table_name, self._schema_name)

        if create_tables:
            self.create_tables()

    def create_tables(self) -> None:
        """Create the outbox table if it doesn't exist."""
        engine = self.connection_manager.datastore.engine
        self._outbox_table.create(engine, checkfirst=True)
        logger.debug("Outbox table created: %s", self._table_name)

    def _get_stored_message(
        self, message: CloudMessage[Any]
    ) -> tuple[str, str, bytes, datetime]:
        """Convert CloudMessage to stored format.

        Args:
            message: The CloudMessage to convert

        Returns:
            Tuple of (message_id, topic, serialized_message, created_at)
        """
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
            CanCreateTimestamp.create_timestamp(),
        )

    def save(self, *messages: CloudMessage[Any]) -> None:
        """Save messages to the outbox table.

        Uses INSERT with ON CONFLICT DO NOTHING for idempotency.

        Args:
            messages: CloudMessage instances to save
        """
        self.verify()
        if not messages:
            return

        stored_messages = [self._get_stored_message(msg) for msg in messages]

        with self.connection_manager.cursor() as conn:
            for mid, topic, message_bytes, created_at in stored_messages:
                # Use dialect-agnostic approach for INSERT OR IGNORE
                try:
                    stmt = insert(self._outbox_table).values(
                        message_id=mid,
                        topic=topic,
                        message=message_bytes,
                        created_at=created_at,
                        retry_count=0,
                    )
                    conn.execute(stmt)
                except IntegrityError:
                    # Message already exists, ignore
                    pass

    def fetch_pending(self, limit: int | None = None) -> list[CloudMessage[Any]]:
        """Fetch pending messages that haven't been published yet.

        Retrieves messages where published_at is NULL and retry_count < 3.

        Args:
            limit: Maximum number of messages to fetch (None for all)

        Returns:
            List of CloudMessage instances ready for publishing
        """
        self.verify()
        with self.connection_manager.cursor() as conn:
            stmt = (
                select(
                    self._outbox_table.c.message_id,
                    self._outbox_table.c.topic,
                    self._outbox_table.c.message,
                )
                .where(
                    self._outbox_table.c.published_at.is_(None),
                    (
                        self._outbox_table.c.failed_at.is_(None)
                        | (self._outbox_table.c.retry_count < 3)
                    ),
                )
                .order_by(self._outbox_table.c.created_at.asc())
            )

            if limit is not None:
                stmt = stmt.limit(limit)

            result = conn.execute(stmt)
            rows = result.fetchall()

        messages: list[CloudMessage[Any]] = []
        for row in rows:
            try:
                # Reconstruct the message from stored data
                stored_payload_bytes: bytes = row.message
                data = orjson.loads(stored_payload_bytes)
                payload_state = bytes.fromhex(data.pop("payload_state"))
                payload_topic = data.pop("payload_topic")
                stored_message = StoredMessage(payload_topic, payload_state)
                payload = self._mapper.to_message(stored_message)
                assert isinstance(payload, TMessagePayload)
                data["payload"] = payload
                data["message_id"] = row.message_id
                cloud_message = CloudMessage[type(payload)](**data)  # type: ignore
                messages.append(cloud_message)
            except Exception as e:
                logger.error(
                    "Failed to deserialize message %s: %s",
                    row.message_id,
                    e,
                    exc_info=True,
                )
                continue

        return messages

    def mark_as_published(self, *message_ids: UUID) -> None:
        """Mark messages as successfully published.

        Args:
            message_ids: UUIDs of messages to mark as published
        """
        self.verify()
        if not message_ids:
            return

        now = datetime.now(timezone.utc)
        with self._cursor() as conn:
            for mid in message_ids:
                stmt = (
                    update(self._outbox_table)
                    .where(self._outbox_table.c.message_id == str(mid))
                    .values(published_at=now)
                )
                conn.execute(stmt)

    def _cursor(self):
        """Get the current connection for executing statements."""
        return self._connection_manager.cursor()

    def mark_as_failed(self, *message_ids: UUID, error: str) -> None:
        """Mark messages as failed and increment retry count.

        Args:
            message_ids: UUIDs of messages that failed
            error: Error message describing the failure
        """
        self.verify()
        if not message_ids:
            return

        now = datetime.now(timezone.utc)
        with self._cursor() as conn:
            for mid in message_ids:
                stmt = (
                    update(self._outbox_table)
                    .where(self._outbox_table.c.message_id == str(mid))
                    .values(
                        failed_at=now,
                        error=error,
                        retry_count=self._outbox_table.c.retry_count + 1,
                    )
                )
                conn.execute(stmt)


class SQLAlchemyInboxRepository(
    BaseRepositoryAdapter[SQLAlchemyConnectionContextManager],
    IInboxRepository[SQLAlchemyConnectionContextManager],
):
    """SQLAlchemy implementation of the Inbox pattern repository.

    Ensures idempotent message processing by tracking which messages
    have been processed by which handlers. Supports multiple database
    backends through SQLAlchemy.
    """

    ENV: ClassVar[Dict[str, str]] = {
        "TABLE_NAME": "inbox",
        "CREATE_TABLES": "False",
    }

    def __init__(
        self,
        mapper: MessageMapper,
        connection_manager: SQLAlchemyConnectionContextManager,
    ):
        """Initialize inbox repository.

        Args:
            mapper: Message mapper for serialization/deserialization
            connection_manager: SQLAlchemy connection context manager
        """
        super().__init__(connection_manager)
        self._mapper = mapper

    def initialize(self, env: Mapping[str, str]) -> None:
        """Initialize the repository from environment variables.

        Args:
            env: Environment variables mapping

        Environment variables:
            TABLE_NAME: Name for the inbox table (default: inbox)
            SCHEMA_NAME: Database schema name (optional)
            CREATE_TABLES: If True, create tables on initialization (default: False)
        """
        super().initialize(env)
        self._table_name: str = self.env.get("TABLE_NAME", "inbox")
        self._schema_name: str | None = self.env.get("SCHEMA_NAME")
        create_tables = strtobool(self.env.get("CREATE_TABLES", "False"))

        # Create table object
        self._inbox_table = create_inbox_table(self._table_name, self._schema_name)

        if create_tables:
            self.create_tables()

    def _cursor(self):
        """Get the current connection for executing statements."""
        return self._connection_manager.cursor()

    def create_tables(self) -> None:
        """Create the inbox table if it doesn't exist."""
        engine = self.connection_manager.datastore.engine
        self._inbox_table.create(engine, checkfirst=True)
        logger.debug("Inbox table created: %s", self._table_name)

    def register_message(
        self, message: CloudMessage[Any], handler: str, max_retries: int = 3
    ) -> bool:
        """Register a message for processing.

        Implements idempotency check by attempting to insert the message.
        If it already exists, checks if it's eligible for retry.

        Args:
            message: The CloudMessage being processed
            handler: Name of the handler processing the message
            max_retries: Maximum number of retry attempts (default: 3)

        Returns:
            True if the message was already processed or exhausted retries (skip)
            False if this is a new message or eligible for retry (process)
        """
        self.verify()
        with self._cursor() as conn:
            try:
                insert_stmt = insert(self._inbox_table).values(
                    message_id=str(message.message_id),
                    handler=handler,
                    received_at=CanCreateTimestamp.create_timestamp(),
                    retry_count=0,
                )
                conn.execute(insert_stmt)
                # Successfully inserted, so it's a new message
                return False
            except IntegrityError:
                # Primary key violation means it's a duplicate
                # Check if eligible for retry
                select_stmt = select(
                    self._inbox_table.c.message_id,
                    self._inbox_table.c.handler,
                    self._inbox_table.c.processed_at,
                    self._inbox_table.c.error,
                    self._inbox_table.c.retry_count,
                    self._inbox_table.c.failed_at,
                ).where(
                    self._inbox_table.c.message_id == str(message.message_id),
                    self._inbox_table.c.handler == handler,
                    self._inbox_table.c.processed_at.is_(None),
                    (
                        self._inbox_table.c.failed_at.is_(None)
                        | (self._inbox_table.c.retry_count < max_retries)
                    ),
                )
                result = conn.execute(select_stmt)
                row = result.fetchone()
                if row is not None:
                    return False

                return True

    def mark_as_processed(self, message_id: UUID, handler: str) -> None:
        """Mark a message as successfully processed by a handler.

        Args:
            message_id: UUID of the message
            handler: Name of the handler that processed it
        """
        self.verify()
        with self._cursor() as conn:
            stmt = (
                update(self._inbox_table)
                .where(
                    self._inbox_table.c.message_id == str(message_id),
                    self._inbox_table.c.handler == handler,
                )
                .values(processed_at=CanCreateTimestamp.create_timestamp())
            )
            conn.execute(stmt)

    def mark_as_failed(self, message_id: UUID, handler: str, error: str) -> None:
        """Mark a message as failed by a handler.

        Args:
            message_id: UUID of the message
            handler: Name of the handler that failed
            error: Error message describing the failure
        """
        self.verify()
        with self._cursor() as conn:
            stmt = (
                update(self._inbox_table)
                .where(
                    self._inbox_table.c.message_id == str(message_id),
                    self._inbox_table.c.handler == handler,
                )
                .values(
                    failed_at=CanCreateTimestamp.create_timestamp(),
                    error=error,
                    retry_count=self._inbox_table.c.retry_count + 1,
                )
            )
            conn.execute(stmt)


class SQLAlchemyPairInboxOutbox(
    InfrastructureGroup,
    IPairInboxOutbox[SQLAlchemyConnectionContextManager],
):
    """Groups SQLAlchemy inbox and outbox repositories together.

    Provides a convenient way to initialize and manage both
    inbox and outbox repositories with shared configuration.
    """

    def __init__(
        self,
        mapper: MessageMapper,
        connection_manager: SQLAlchemyConnectionContextManager,
    ):
        """Initialize inbox/outbox pair.

        Args:
            mapper: Message mapper for serialization/deserialization
            connection_manager: SQLAlchemy connection context manager
        """
        self._inbox = SQLAlchemyInboxRepository(mapper, connection_manager)
        self._outbox = SQLAlchemyOutboxRepository(mapper, connection_manager)
        super().__init__(self._inbox, self._outbox)

    @property
    def inbox(self) -> IInboxRepository[SQLAlchemyConnectionContextManager]:
        """Get the inbox repository."""
        return self._inbox

    @property
    def outbox(self) -> IOutboxRepository[SQLAlchemyConnectionContextManager]:
        """Get the outbox repository."""
        return self._outbox
