from typing import ClassVar, Dict, Mapping, cast

from sqlalchemy import Connection, delete, insert, update

from example.contacto.domain.entidad_contacto import (
    EntidadContacto,
    EntidadExampletate,
    IdEntidadContacto,
    ValidacionEntidadContacto,
)
from example.contacto.ports.drivens import IEntidadContactoRepository

## Modelo de base de datos
from example.database.entidad_contacto import (
    EntidadContacto as EntidadContactoModel,
)
from example.database.entidad_contacto import (
    ValidacionContactoEntidad as ValidacionContactoEntidadModel,
)
from example.shared.mapper_enum_tables import MapperEnumTables
from hexagonal.domain import AggregateSnapshot, SnapshotState
from hexagonal.integrations.sqlalchemy import (
    SQLAlchemyConnectionContextManager,
    SQLAlchemyRepositoryAdapter,
)


class SQLAlchemyEntidadContactoRepositoryAdapter(
    SQLAlchemyRepositoryAdapter[EntidadContacto, IdEntidadContacto],
    IEntidadContactoRepository[SQLAlchemyConnectionContextManager],
):
    ENV: ClassVar[Dict[str, str]] = {"TABLE_NAME": "entidad_contacto"}

    def initialize(self, env: Mapping[str, str]) -> None:
        super().initialize(env)
        self.validacion_mapper = MapperEnumTables(
            table_model=ValidacionContactoEntidadModel,
            enum_model=ValidacionEntidadContacto,
            manager=self.connection_manager,
        )

    def _insert_snapshot(
        self,
        conn: Connection,
        snap: AggregateSnapshot[SnapshotState[IdEntidadContacto]],
    ) -> None:
        super()._insert_snapshot(conn, snap)
        state = cast(EntidadExampletate, snap.state)  # type: ignore
        stmt = insert(EntidadContactoModel).values(
            id_entidad=state.entidad.value,
            id_contacto=state.contacto.value,
            validacion=self.validacion_mapper.get_id_from_enum(state.validacion),
            usuario_creacion=state.usuario_creacion.value
            if state.usuario_creacion
            else None,
            usuario_validacion=state.usuario_validacion.value
            if state.usuario_validacion
            else None,
            fecha_validacion=state.fecha_validacion,
            fecha_creacion=state.created_on,
        )
        conn.execute(stmt)

    def _update_snapshot(
        self,
        conn: Connection,
        snap: AggregateSnapshot[SnapshotState[IdEntidadContacto]],
    ) -> None:
        super()._update_snapshot(conn, snap)
        state = cast(EntidadExampletate, snap.state)  # type: ignore
        stmt = (
            update(EntidadContactoModel)
            .where(
                EntidadContactoModel.id_entidad == state.entidad.value,
                EntidadContactoModel.id_contacto == state.contacto.value,
            )
            .values(
                validacion=self.validacion_mapper.get_id_from_enum(state.validacion),
                usuario_creacion=state.usuario_creacion.value
                if state.usuario_creacion
                else None,
                usuario_validacion=state.usuario_validacion.value
                if state.usuario_validacion
                else None,
                fecha_validacion=state.fecha_validacion,
                fecha_creacion=state.created_on,
            )
        )
        conn.execute(stmt)

    def _delete(self, conn: Connection, id: IdEntidadContacto) -> None:
        super()._delete(conn, id)
        # Note: EntidadContacto uses composite key (id_entidad, id_contacto)
        # The id contains the composite information
        stmt = delete(EntidadContactoModel).where(
            EntidadContactoModel.id_entidad == id.value
        )
        conn.execute(stmt)
