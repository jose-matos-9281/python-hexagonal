"""
Caso de uso: Crear Contacto
Descripción: Crea un nuevo contacto (teléfono o email)
    asociado opcionalmente a un usuario.
Condiciones previas:
    - El contacto no debe estar registrado previamente en el sistema.
    - El tipo de contacto (TELEFONO, EMAIL) debe ser válido.
Condiciones posteriores:
    - El contacto se guarda en el repositorio.
    - El estado inicial del contacto es SIN_VALIDAR.
    - Se emiten los eventos Examplenapshot y ContactoCreado.
"""

from logging import getLogger

from example.contacto.domain.contacto import EstadoContacto
from example.contacto.domain.shared import TipoContacto

from ..base import BaseTest

logger = getLogger(__name__)


class TestCrearContacto(BaseTest):
    temp_db = __file__.replace(".py", ".db")

    @classmethod
    def setup_class(cls):
        super().setup_class()
        cls.api = cls.api_wrapper.contacto.contacto

    def test_crear_contacto(self):
        ## GIVEN: Un nuevo contacto con tipo y valor válidos
        tipo_contacto = TipoContacto.EMAIL
        valor_contacto = "test@example.com"

        ## WHEN: Crear un nuevo contacto
        self.logger.info(
            "Creando contacto con tipo %s y valor %s", tipo_contacto, valor_contacto
        )
        resp = self.api.crear(tipo_contacto.value, valor_contacto)

        ## THEN: se emiten los eventos
        creado = resp.get(self.api.Events.CREADO.value, raise_error=False)
        snapshot = resp.get(self.api.Events.SNAPSHOT.value, raise_error=False)
        assert creado is not None
        assert snapshot is not None
        self.logger.info("Eventos emitidos: CREADO=%s", creado.id_contacto)
        ## THEN: el contacto se guarda con estado SIN_VALIDAR
        contacto = self.api.get(creado.id_contacto.value)
        assert contacto is not None
        assert contacto.contacto.tipo == tipo_contacto
        assert contacto.contacto.value == valor_contacto
        assert contacto.estado == EstadoContacto.SIN_VALIDAR

    def test_get_contacto_by_id(self):
        ## GIVEN: Un contacto creado previamente
        tipo_contacto = TipoContacto.TELEFONO
        valor_contacto = "+123456789"
        resp = self.api.crear(tipo_contacto.value, valor_contacto)
        creado = resp.get(self.api.Events.CREADO.value, raise_error=False)
        assert creado is not None

        ## WHEN: Obtener el contacto por su ID
        contacto = self.api.get(creado.id_contacto.value)

        ## THEN: se obtiene el contacto con los datos correctos
        assert contacto is not None
        assert contacto.contacto.tipo == tipo_contacto
        assert contacto.contacto.value == valor_contacto
