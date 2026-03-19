from logging import getLogger
from typing import ClassVar, Dict, Mapping, cast

from sqlalchemy import Connection, delete, insert, select, update

from example.contacto.domain.entidad import Afiliado, Entidad
from example.contacto.domain.shared import IdEntidad, TipoEntidad
from example.contacto.ports.drivens import IEntidadRepository

## Modelo de base de datos
from example.database.entidad import Afiliado as AfiliadoModel
from example.database.entidad import Entidad as EntidadModel
from example.database.entidad import TipoEntidad as TipoEntidadModel
from example.shared.mapper_enum_tables import MapperEnumTables
from hexagonal.integrations.sqlalchemy import (
    SQLAlchemyConnectionContextManager,
    SQLAlchemyEntityRepositoryAdapter,
)

logger = getLogger(__name__)


class SQLAlchemyEntidadRepositoryAdapter(
    SQLAlchemyEntityRepositoryAdapter[Entidad, IdEntidad],
    IEntidadRepository[SQLAlchemyConnectionContextManager],
):
    ENV: ClassVar[Dict[str, str]] = {"TABLE_NAME": "entidad"}

    def initialize(self, env: Mapping[str, str]) -> None:
        super().initialize(env)
        self.tipo_entidad_mapper = MapperEnumTables(
            table_model=TipoEntidadModel,
            enum_model=TipoEntidad,
            manager=self.connection_manager,
        )

    def _get(self, conn: Connection, id: IdEntidad) -> Entidad | None:
        stmt = select(EntidadModel).where(EntidadModel.id_entidad == id.value)
        result = conn.execute(stmt).fetchone()
        if not result:
            return None
        id_tipo_entidad: int = result[1]
        value_entidad: str = result[2]
        tipo_entidad = self.tipo_entidad_mapper.get_enum_from_id(id_tipo_entidad)
        if tipo_entidad == TipoEntidad.AFILIADO:
            stmt_afiliado = select(AfiliadoModel).where(
                AfiliadoModel.cd_afiliado == value_entidad
            )
            result_afiliado = conn.execute(stmt_afiliado).fetchone()
            if not result_afiliado:
                return None
            cd_asegurado, cd_dependiente = result_afiliado[0].split("-")
            value = Afiliado.new(
                cd_asegurado=cd_asegurado, cd_dependiente=cd_dependiente
            )
        else:
            raise ValueError(f"TipoEntidad {tipo_entidad} not supported")
        a = Entidad(id=id, value=value)
        return a

    def _insert(self, conn: Connection, entity: Entidad) -> None:
        tipo_entidad_id = self.tipo_entidad_mapper.get_id_from_enum(entity.value.tipo)
        # Insert new record
        stmt_insert = insert(EntidadModel).values(
            id_entidad=entity.id.value,
            id_tipo_entidad=tipo_entidad_id,
            valor=entity.value.value,
        )
        conn.execute(stmt_insert)

        if entity.value.tipo == TipoEntidad.AFILIADO:
            ev = cast(Afiliado, entity.value)
            cd_afiliado = f"{ev.cd_asegurado}-{ev.cd_dependiente}"
            stmt_insert_afiliado = insert(AfiliadoModel).values(cd_afiliado=cd_afiliado)
            conn.execute(stmt_insert_afiliado)
        else:
            raise ValueError(
                f"TipoEntidad {entity.value.tipo} not supported for insert"
            )

    def _update(self, conn: Connection, entity: Entidad) -> None:
        # Update existing record
        tipo_entidad_id = self.tipo_entidad_mapper.get_id_from_enum(entity.value.tipo)
        stmt_update = (
            update(EntidadModel)
            .where(EntidadModel.id_entidad == entity.id.value)
            .values(
                id_tipo_entidad=tipo_entidad_id,
                valor=entity.value.value,
            )
        )
        conn.execute(stmt_update)
        if entity.value.tipo == TipoEntidad.AFILIADO:
            ev = cast(Afiliado, entity.value)
            cd_afiliado = f"{ev.cd_asegurado}-{ev.cd_dependiente}"
            stmt_update_afiliado = (
                update(AfiliadoModel)
                .where(AfiliadoModel.cd_afiliado == cd_afiliado)
                .values(cd_afiliado=cd_afiliado)
            )
            conn.execute(stmt_update_afiliado)
        else:
            raise ValueError(
                f"TipoEntidad {entity.value.tipo} not supported for update"
            )

    def _delete(self, conn: Connection, id: IdEntidad) -> None:
        stmt = select(EntidadModel).where(EntidadModel.id_entidad == id.value)
        result = conn.execute(stmt).fetchone()
        if not result:
            raise KeyError(f"Entidad with id {id} not found")
        entidad_model = result[0]
        tipo_entidad = self.tipo_entidad_mapper.get_enum_from_id(
            entidad_model.id_tipo_entidad
        )
        if tipo_entidad == TipoEntidad.AFILIADO:
            stmt_delete_afiliado = delete(AfiliadoModel).where(
                AfiliadoModel.cd_afiliado == entidad_model.valor
            )
            conn.execute(stmt_delete_afiliado)
        else:
            raise ValueError(f"TipoEntidad {tipo_entidad} not supported for delete")

        stmt_delete = delete(EntidadModel).where(EntidadModel.id_entidad == id.value)
        conn.execute(stmt_delete)

    def save(self, entity: Entidad) -> None:
        """Save an entity to the repository."""
        self.verify()
        with self.connection_manager.cursor() as conn:
            existing = self._get(conn, entity.id)
            if existing is None:
                self._insert(conn, entity)
            else:
                self._update(conn, entity)
