from typing import ClassVar, Dict, Mapping, cast

from sqlalchemy import Connection, delete, insert, update

from example.contacto.domain.contacto import Contacto, EstadoContacto, Exampletate
from example.contacto.domain.shared import IdContacto, TipoContacto
from example.contacto.ports.drivens import IContactoRepository

## Modelo de base de datos
from example.database.contacto import Contacto as ContactoModel
from example.database.contacto import EstadoValidacionContacto as EstadoContactoModel
from example.database.contacto import TipoContacto as TipoContactoModel
from example.shared.mapper_enum_tables import MapperEnumTables
from hexagonal.domain import AggregateSnapshot, SnapshotState
from hexagonal.integrations.sqlalchemy import (
    SQLAlchemyConnectionContextManager,
    SQLAlchemyRepositoryAdapter,
)


class SQLAlchemyContactoRepositoryAdapter(
    SQLAlchemyRepositoryAdapter[Contacto, IdContacto],
    IContactoRepository[SQLAlchemyConnectionContextManager],
):
    ENV: ClassVar[Dict[str, str]] = {"TABLE_NAME": "contacto"}

    def initialize(self, env: Mapping[str, str]) -> None:
        super().initialize(env)
        self.tipo_contacto_mapper = MapperEnumTables(
            table_model=TipoContactoModel,
            enum_model=TipoContacto,
            manager=self.connection_manager,
        )
        self.estado_contacto_mapper = MapperEnumTables(
            table_model=EstadoContactoModel,
            enum_model=EstadoContacto,
            manager=self.connection_manager,
        )

    def _insert_snapshot(
        self, conn: Connection, snap: AggregateSnapshot[SnapshotState[IdContacto]]
    ) -> None:
        super()._insert_snapshot(conn, snap)
        state = cast(Exampletate, snap.state)  # type: ignore
        usuario = state.usuario_validacion.value if state.usuario_validacion else None
        user_create = state.usuario_creacion.value if state.usuario_creacion else None
        stmt = insert(ContactoModel).values(
            id_contacto=state.id.value,
            id_tipo_contacto=self.tipo_contacto_mapper.get_id_from_enum(
                state.contacto.tipo
            ),
            contacto=state.contacto.value,
            estado=self.estado_contacto_mapper.get_id_from_enum(state.estado),
            usuario_creacion=user_create,
            usuario_validacion=usuario,
            fecha_validacion=state.fecha_validacion,
            fecha_creacion=state.created_on,
        )
        conn.execute(stmt)

    def _update_snapshot(
        self, conn: Connection, snap: AggregateSnapshot[SnapshotState[IdContacto]]
    ) -> None:
        super()._update_snapshot(conn, snap)
        state = cast(Exampletate, snap.state)  # type: ignore
        usuario = state.usuario_validacion.value if state.usuario_validacion else None
        user_create = state.usuario_creacion.value if state.usuario_creacion else None
        stmt = (
            update(ContactoModel)
            .where(ContactoModel.id_contacto == state.id.value)
            .values(
                id_tipo_contacto=self.tipo_contacto_mapper.get_id_from_enum(
                    state.contacto.tipo
                ),
                contacto=state.contacto.value,
                estado=self.estado_contacto_mapper.get_id_from_enum(state.estado),
                usuario_creacion=user_create,
                usuario_validacion=usuario,
                fecha_validacion=state.fecha_validacion,
                fecha_creacion=state.created_on,
            )
        )
        conn.execute(stmt)

    def _delete(self, conn: Connection, id: IdContacto) -> None:
        super()._delete(conn, id)
        stmt = delete(ContactoModel).where(ContactoModel.id_contacto == id.value)
        conn.execute(stmt)
