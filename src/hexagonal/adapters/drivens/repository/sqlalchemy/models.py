"""SQLAlchemy table definitions for aggregates, events, outbox and inbox."""

from sqlalchemy import (
    Column,
    DateTime,
    Index,
    Integer,
    LargeBinary,
    MetaData,
    PrimaryKeyConstraint,
    String,
    Table,
    Text,
)

# Global metadata for table definitions
metadata = MetaData()


def _get_table_key(table_name: str, schema: str | None = None) -> str:
    """Get the key used by SQLAlchemy metadata to store the table."""
    if schema:
        return f"{schema}.{table_name}"
    return table_name


def create_aggregates_table(table_name: str, schema: str | None = None) -> Table:
    """Create the aggregates snapshots table definition.

    Args:
        table_name: Base name for the table (will be prefixed with 'aggregates_')
        schema: Optional database schema name

    Returns:
        SQLAlchemy Table object for aggregate snapshots
    """
    full_table_name = f"aggregates_{table_name}"
    table_key = _get_table_key(full_table_name, schema)

    # Return existing table if already defined
    if table_key in metadata.tables:
        return metadata.tables[table_key]

    return Table(
        full_table_name,
        metadata,
        Column("originator_id", String(36), nullable=False),
        Column("aggregate_name", Text, nullable=False),
        Column("originator_version", Integer, nullable=False),
        Column("topic", Text, nullable=False),
        Column("state", LargeBinary, nullable=False),
        Column("timestamp", DateTime(timezone=True), nullable=False),
        PrimaryKeyConstraint("originator_id", "aggregate_name"),
        schema=schema,
    )


def create_events_table(table_name: str, schema: str | None = None) -> Table:
    """Create the aggregates events history table definition.

    Args:
        table_name: Base name for the table (prefixed with 'aggregates_',
            suffixed with '_events')
        schema: Optional database schema name

    Returns:
        SQLAlchemy Table object for aggregate events history
    """
    full_table_name = f"aggregates_{table_name}_events"
    table_key = _get_table_key(full_table_name, schema)

    # Return existing table if already defined
    if table_key in metadata.tables:
        return metadata.tables[table_key]

    return Table(
        full_table_name,
        metadata,
        Column("originator_id", String(36), nullable=False),
        Column("aggregate_name", Text, nullable=False),
        Column("originator_version", Integer, nullable=False),
        Column("topic", Text, nullable=False),
        Column("state", LargeBinary, nullable=False),
        Column("timestamp", DateTime(timezone=True), nullable=False),
        PrimaryKeyConstraint("originator_id", "aggregate_name", "originator_version"),
        schema=schema,
    )


def create_outbox_table(table_name: str = "outbox", schema: str | None = None) -> Table:
    """Create the outbox table definition.

    Args:
        table_name: Name for the outbox table (default: 'outbox')
        schema: Optional database schema name

    Returns:
        SQLAlchemy Table object for outbox messages
    """
    table_key = _get_table_key(table_name, schema)

    # Return existing table if already defined
    if table_key in metadata.tables:
        return metadata.tables[table_key]

    return Table(
        table_name,
        metadata,
        Column("message_id", String(36), primary_key=True),
        Column("topic", Text, nullable=False),
        Column("message", LargeBinary, nullable=False),
        Column("published_at", DateTime(timezone=True), nullable=True),
        Column("failed_at", DateTime(timezone=True), nullable=True),
        Column("error", Text, nullable=True),
        Column("retry_count", Integer, nullable=False, default=0),
        Column(
            "created_at",
            DateTime(timezone=True),
            nullable=False,
        ),
        Index(f"idx_{table_name}_published", "published_at"),
        Index(f"idx_{table_name}_topic", "topic"),
        schema=schema,
    )


def create_inbox_table(table_name: str = "inbox", schema: str | None = None) -> Table:
    """Create the inbox table definition.

    Args:
        table_name: Name for the inbox table (default: 'inbox')
        schema: Optional database schema name

    Returns:
        SQLAlchemy Table object for inbox messages
    """
    table_key = _get_table_key(table_name, schema)

    # Return existing table if already defined
    if table_key in metadata.tables:
        return metadata.tables[table_key]

    return Table(
        table_name,
        metadata,
        Column("message_id", String(36), nullable=False),
        Column("handler", Text, nullable=False),
        Column("received_at", DateTime(timezone=True), nullable=False),
        Column("processed_at", DateTime(timezone=True), nullable=True),
        Column("error", Text, nullable=True),
        Column("retry_count", Integer, nullable=False, default=0),
        Column("failed_at", DateTime(timezone=True), nullable=True),
        PrimaryKeyConstraint("message_id", "handler"),
        Index(f"idx_{table_name}_processed", "processed_at"),
        schema=schema,
    )
