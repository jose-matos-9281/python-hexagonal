import os

from sqlalchemy.orm import DeclarativeBase

from hexagonal.adapters.drivens.repository.sqlalchemy.models import metadata

SCHEMA = os.getenv(
    "SCHEMA_NAME",
)
DATABASE_URL = os.getenv("SQLALCHEMY_DATABASE_URL", "")

if "sqlite" not in DATABASE_URL.lower() and DATABASE_URL:
    metadata.schema = SCHEMA

SCHEMA_PREFIX = f"{SCHEMA}." if SCHEMA else ""

metadata.naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = metadata

    __abstract__ = True
