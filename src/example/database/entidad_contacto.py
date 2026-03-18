"""Modelos de base de datos para el módulo de example."""

from datetime import datetime
from typing import Optional
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
from .contacto import Contacto
from .entidad import Entidad


class ValidacionContactoEntidad(Base):
    """Tabla de validación de contacto-entidad."""

    __tablename__ = "validacion_contacto_entidad"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_validacion_contacto_entidad"),
        UniqueConstraint("nombre", name="uq_validacion_contacto_entidad_nombre"),
    )

    id: Mapped[int] = mapped_column(Integer, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)

    # Relaciones
    entidades_example: Mapped[list["EntidadContacto"]] = relationship(
        "EntidadContacto", back_populates="validacion_estado"
    )


class EntidadContacto(Base):
    """Tabla de relación entre entidades y example."""

    __tablename__ = "entidad_contacto"
    __table_args__ = (
        PrimaryKeyConstraint("id_entidad", "id_contacto", name="pk_entidad_contacto"),
        ForeignKeyConstraint(
            ["id_entidad"],
            [f"{SCHEMA_PREFIX}entidad.id_entidad"],
            name="fk_entidad_contacto_entidad",
        ),
        ForeignKeyConstraint(
            ["id_contacto"],
            [f"{SCHEMA_PREFIX}contacto.id_contacto"],
            name="fk_entidad_contacto_contacto",
        ),
        ForeignKeyConstraint(
            ["validacion"],
            [f"{SCHEMA_PREFIX}validacion_contacto_entidad.id"],
            name="fk_entidad_contacto_validacion",
        ),
    )

    id_entidad: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    id_contacto: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    validacion: Mapped[int] = mapped_column(Integer, nullable=False)
    usuario_creacion: Mapped[Optional[UUID]] = mapped_column(Uuid, nullable=True)
    usuario_validacion: Mapped[Optional[UUID]] = mapped_column(Uuid, nullable=True)
    fecha_validacion: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    fecha_creacion: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relaciones
    entidad: Mapped["Entidad"] = relationship(
        "Entidad", back_populates="entidades_example"
    )
    contacto: Mapped["Contacto"] = relationship(
        "Contacto", back_populates="entidades_example"
    )
    validacion_estado: Mapped["ValidacionContactoEntidad"] = relationship(
        "ValidacionContactoEntidad", back_populates="entidades_example"
    )
