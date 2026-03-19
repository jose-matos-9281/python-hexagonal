"""
Caso de uso: Crear Entidad Contacto
Descripción: Crea la relación de vinculación entre una entidad y un contacto específico.
Condiciones previas:
    - La entidad debe existir en el sistema.
    - El contacto debe existir en el sistema.
Condiciones posteriores:
    - Se guarda el registro de EntidadContacto en el repositorio.
    - El estado de validación inicial es NO_VALIDADO.
    - Se emiten los eventos EntidadExamplenapshot y EntidadContactoCreado.
"""

from uuid6 import uuid7

from example.contacto.domain.entidad_contacto import ValidacionEntidadContacto
from example.contacto.domain.shared import TipoContacto, TipoEntidad

from ..base import BaseTest


class TestCrearEntidadContacto(BaseTest):
    temp_db = __file__.replace(".py", ".db")

    @classmethod
    def setup_class(cls):
        super().setup_class()
        cls.contacto_api = cls.api_wrapper.contacto.contacto
        cls.entidad_api = cls.api_wrapper.contacto.entidad
        cls.api = cls.api_wrapper.contacto.entidad_contacto
        cls.usuario = uuid7()

    def test_crear_entidad_contacto(self):
        contacto_resp = self.contacto_api.crear(
            TipoContacto.EMAIL.value,
            "entidad-contacto@example.com",
            usuario=self.usuario,
        )
        contacto_creado = contacto_resp.get(self.contacto_api.Events.CREADO.value)

        entidad_resp = self.entidad_api.crear(
            TipoEntidad.AFILIADO,
            {
                "cd_asegurado": "30000001",
                "cd_dependiente": "01",
            },
        )
        entidad_creada = entidad_resp.get(self.entidad_api.Events.CREADA.value)

        resp = self.api.crear(
            entidad_creada.id_entidad.value,
            contacto_creado.id_contacto.value,
            usuario=self.usuario,
        )

        creado = resp.get(self.api.Events.CREADO.value, raise_error=False)
        snapshot = resp.get(self.api.Events.SNAPSHOT.value, raise_error=False)

        assert creado is not None
        assert snapshot is not None

        entidad_contacto = self.api.get(creado.id_entidad_contacto.value)

        assert entidad_contacto.entidad == entidad_creada.id_entidad
        assert entidad_contacto.contacto == contacto_creado.id_contacto
        assert entidad_contacto.validacion == ValidacionEntidadContacto.NO_VALIDADO
        assert entidad_contacto.usuario_creacion.value == self.usuario
        assert entidad_contacto.usuario_validacion is None
        assert entidad_contacto.fecha_validacion is None
