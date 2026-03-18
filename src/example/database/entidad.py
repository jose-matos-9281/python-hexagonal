"""Modelos de base de datos para el módulo de example."""

from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import (
    ForeignKeyConstraint,
    Integer,
    PrimaryKeyConstraint,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import SCHEMA_PREFIX, Base


class TipoEntidad(Base):
    """Tabla de tipos de entidad."""

    __tablename__ = "tipo_entidad"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_tipo_entidad"),
        UniqueConstraint("nombre", name="uq_tipo_entidad_nombre"),
    )

    id: Mapped[int] = mapped_column(Integer, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)

    # Relaciones
    entidades: Mapped[list["Entidad"]] = relationship(
        "Entidad", back_populates="tipo_entidad"
    )


class Afiliado(Base):
    """Tabla de afiliados."""

    __tablename__ = "afiliado"
    __table_args__ = (PrimaryKeyConstraint("cd_afiliado", name="pk_afiliado"),)

    cd_afiliado: Mapped[str] = mapped_column(String(36))
    nss: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    cedula: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    edad: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    sexo: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    parentesco: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    nombre: Mapped[Optional[str]] = mapped_column(String, nullable=True)


class Entidad(Base):
    """Tabla de entidades."""

    __tablename__ = "entidad"
    __table_args__ = (
        PrimaryKeyConstraint("id_entidad", name="pk_entidad"),
        UniqueConstraint("id_tipo_entidad", "valor", name="uq_entidad_tipo_valor"),
        ForeignKeyConstraint(
            ["id_tipo_entidad"],
            [f"{SCHEMA_PREFIX}tipo_entidad.id"],
            name="fk_entidad_tipo_entidad",
        ),
    )
    id_entidad: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    id_tipo_entidad: Mapped[int] = mapped_column(Integer, nullable=False)
    valor: Mapped[str] = mapped_column(String(255), nullable=False)

    # Relaciones
    tipo_entidad: Mapped["TipoEntidad"] = relationship(
        "TipoEntidad",
        back_populates="entidades",
    )
    entidades_example: Mapped[list["EntidadContacto"]] = relationship(
        "EntidadContacto", back_populates="entidad"
    )


if TYPE_CHECKING:
    from .entidad_contacto import EntidadContacto
