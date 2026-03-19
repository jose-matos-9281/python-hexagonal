"""Modelos de base de datos para el módulo de example."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import (
    DateTime,
    ForeignKeyConstraint,
    Integer,
    PrimaryKeyConstraint,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import SCHEMA_PREFIX, Base


class TipoContacto(Base):
    """Tabla de tipos de contacto."""

    __tablename__ = "tipo_contacto"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_tipo_contacto"),
        UniqueConstraint("nombre", name="uq_tipo_contacto_nombre"),
    )

    id: Mapped[int] = mapped_column(Integer, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)

    # Relaciones
    example: Mapped[list["Contacto"]] = relationship(
        "Contacto", back_populates="tipo_contacto"
    )


class EstadoValidacionContacto(Base):
    """Tabla de estados de validación de contacto."""

    __tablename__ = "estado_validacion_contacto"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_estado_validacion_contacto"),
        UniqueConstraint("nombre", name="uq_estado_validacion_contacto_nombre"),
    )

    id: Mapped[int] = mapped_column(Integer, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)

    # Relaciones
    example: Mapped[list["Contacto"]] = relationship(
        "Contacto", back_populates="estado_validacion"
    )


class Contacto(Base):
    """Tabla de example."""

    __tablename__ = "contacto"
    __table_args__ = (
        PrimaryKeyConstraint("id_contacto", name="pk_contacto"),
        UniqueConstraint(
            "id_tipo_contacto", "contacto", name="uq_contacto_tipo_contacto"
        ),
        ForeignKeyConstraint(
            ["id_tipo_contacto"],
            [f"{SCHEMA_PREFIX}tipo_contacto.id"],
            name="fk_contacto_tipo_contacto",
        ),
        ForeignKeyConstraint(
            ["estado"],
            [f"{SCHEMA_PREFIX}estado_validacion_contacto.id"],
            name="fk_contacto_estado",
        ),
    )
    id_contacto: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    id_tipo_contacto: Mapped[int] = mapped_column(Integer, nullable=False)
    contacto: Mapped[str] = mapped_column(String(255), nullable=False)
    estado: Mapped[int] = mapped_column(Integer, nullable=False)
    usuario_creacion: Mapped[Optional[UUID]] = mapped_column(Uuid, nullable=True)
    usuario_validacion: Mapped[Optional[UUID]] = mapped_column(Uuid, nullable=True)
    fecha_validacion: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    fecha_creacion: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relaciones
    tipo_contacto: Mapped["TipoContacto"] = relationship(
        "TipoContacto", back_populates="example"
    )
    estado_validacion: Mapped["EstadoValidacionContacto"] = relationship(
        "EstadoValidacionContacto", back_populates="example"
    )
    entidades_example: Mapped[list["EntidadContacto"]] = relationship(
        "EntidadContacto", back_populates="contacto"
    )


if TYPE_CHECKING:
    from .entidad_contacto import EntidadContacto
