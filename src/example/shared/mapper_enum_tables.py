from enum import Enum
from typing import Generic, Mapping, Type, TypeVar

from sqlalchemy import insert, select
from sqlalchemy.orm import DeclarativeBase

from hexagonal.application import Infrastructure
from hexagonal.integrations.sqlalchemy import SQLAlchemyConnectionContextManager

T = TypeVar("T", bound=DeclarativeBase)
E = TypeVar("E", bound=Enum)


class MapperEnumTables(Generic[T, E], Infrastructure):
    def __init__(
        self,
        table_model: Type[T],
        enum_model: Type[E],
        manager: SQLAlchemyConnectionContextManager,
    ) -> None:
        super().__init__()
        self.table_model = table_model
        self.enum_model = enum_model
        self.manager = manager

        self._enum_to_id: dict[E, int] = {}
        self._id_to_enum: dict[int, E] = {}

    def initialize(self, env: Mapping[str, str]) -> None:
        super().initialize(env)
        self._sync()

    @property
    def table(self) -> Type[T]:
        return self.table_model

    @property
    def enum(self) -> Type[E]:
        return self.enum_model

    def _sync(self) -> None:
        """Sincroniza de forma optimista el enum con los registros de la tabla."""
        # Usamos el manager para obtener una conexión y ejecutar los insert necesarios
        with self.manager.cursor(commit=True) as conn:
            # Consultar todos los registros existentes
            stmt = select(self.table_model)
            results = conn.execute(stmt).all()
            db_map = {row.nombre: row.id for row in results}

            for member in self.enum_model:
                nombre = member.name
                if nombre not in db_map:
                    # Si no existe, insertar registro (sincronización optimista)
                    stmt_insert = insert(self.table_model).values(nombre=nombre)
                    conn.execute(stmt_insert)

                    # Obtener el ID recién insertado
                    stmt_id = select(self.table_model).where(
                        self.table_model.nombre == nombre  # type: ignore
                    )
                    db_map[nombre] = conn.execute(stmt_id).scalars().first()

                # Poblar mapeos internos
                item_id = db_map[nombre]
                self._enum_to_id[member] = item_id
                self._id_to_enum[item_id] = member

    def get_id_from_enum(self, value: E) -> int:
        if not self.initialized:
            self.initialize({})
        """Dado un valor del enum, devuelve el id correspondiente en la tabla."""
        if value not in self._enum_to_id:
            msg = (
                f"Valor '{value}' no encontrado en el mapper de la tabla "
                f"{self.table_model.__name__}"
            )
            raise ValueError(msg)
        return self._enum_to_id[value]

    def get_enum_from_id(self, item_id: int) -> E:
        if not self.initialized:
            self.initialize({})
        """Dado un id, devuelve el valor del enum correspondiente."""
        if item_id not in self._id_to_enum:
            msg = (
                f"ID '{item_id}' no encontrado en el mapper de la tabla "
                f"{self.table_model.__name__}"
            )
            raise ValueError(msg)
        return self._id_to_enum[item_id]
