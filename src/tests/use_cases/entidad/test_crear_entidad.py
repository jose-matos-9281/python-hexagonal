"""
Caso de uso: Crear Entidad
Descripción: Registra una nueva entidad (Núcleo o Afiliado) en el sistema.
Condiciones previas:
    - La entidad no debe estar registrada previamente.
    - Los datos de la entidad (cd_asegurado, cd_dependiente)
        deben ser válidos para su tipo.
Condiciones posteriores:
    - La entidad se guarda en el repositorio con un ID derivado de sus valores.
    - Se emite el evento EntidadCreada.
"""

from logging import getLogger
from typing import cast

from example.contacto.domain.shared import TipoEntidad
from example.database.entidad import Afiliado

from ..base import BaseTest

logger = getLogger(__name__)


class TestCrearEntidad(BaseTest):
    temp_db = __file__.replace(".py", ".db")

    @classmethod
    def setup_class(cls):
        super().setup_class()
        cls.api = cls.api_wrapper.contacto.entidad

    def test_crear_entidad(self):
        ## GIVEN: Una nueva entidad con datos válidos
        cd_asegurado = "12345678"
        cd_dependiente = "01"
        tipo_entidad = TipoEntidad.AFILIADO
        datos = {
            "cd_asegurado": cd_asegurado,
            "cd_dependiente": cd_dependiente,
        }
        ## WHEN: Crear una nueva entidad
        self.logger.info(
            "Creando entidad con cd_asegurado %s y cd_dependiente %s",
            cd_asegurado,
            cd_dependiente,
        )
        resp = self.api.crear(tipo_entidad, datos)

        ## THEN: se emite el evento EntidadCreada
        creado = resp.get(self.api.Events.CREADA.value, raise_error=False)
        assert creado is not None
        self.logger.info("Evento emitido: CREADO=%s", creado.id_entidad)

    def test_obtener_entidad_creada(self):
        ## GIVEN: Una entidad creada previamente
        cd_asegurado = "12345678"
        cd_dependiente = "02"
        tipo_entidad = TipoEntidad.AFILIADO
        datos = {
            "cd_asegurado": cd_asegurado,
            "cd_dependiente": cd_dependiente,
        }
        self.logger.info(
            "Creando entidad con cd_asegurado %s y cd_dependiente %s",
            cd_asegurado,
            cd_dependiente,
        )
        resp = self.api.crear(tipo_entidad, datos)
        creado = resp.get(self.api.Events.CREADA.value, raise_error=False)
        assert creado is not None
        self.logger.info("Entidad creada con ID: %s", creado.id_entidad)
        ## WHEN: Obtener la entidad creada
        self.logger.info("Obteniendo entidad con ID: %s", creado.id_entidad)
        entidad = self.api.get(creado.id_entidad)

        ## THEN: se obtiene la entidad con los datos correctos
        assert entidad is not None
        assert entidad.id == creado.id_entidad
        assert entidad.value.tipo == tipo_entidad
        afiliado_value = cast(Afiliado, entidad.value)
        assert afiliado_value.cd_afiliado == f"{cd_asegurado}-{cd_dependiente}"

    def test_crear_entidad_duplicada(self):
        ## GIVEN: Una entidad ya registrada
        cd_asegurado = "87654321"
        cd_dependiente = "02"
        tipo_entidad = TipoEntidad.AFILIADO
        datos = {
            "cd_asegurado": cd_asegurado,
            "cd_dependiente": cd_dependiente,
        }
        self.logger.info(
            "Creando entidad con cd_asegurado %s y cd_dependiente %s",
            cd_asegurado,
            cd_dependiente,
        )
        resp = self.api.crear(tipo_entidad, datos)
        creado = resp.get(self.api.Events.CREADA.value, raise_error=False)
        assert creado is not None
        self.logger.info("Entidad creada con ID: %s", creado.id_entidad)

        ## WHEN: Intentar crear la misma entidad nuevamente
        self.logger.info(
            "Intentando crear entidad duplicada con cd_asegurado %s y cd_dependiente %s",
            cd_asegurado,
            cd_dependiente,
        )
        resp_duplicada = self.api.crear(tipo_entidad, datos)
        ## THEN: se debe sobreescribir la entidad existente sin crear una nueva
        creado_duplicada = resp_duplicada.get(
            self.api.Events.CREADA.value, raise_error=False
        )
        assert creado_duplicada is not None
        self.logger.info(
            "Entidad duplicada actualizada con ID: %s", creado_duplicada.id_entidad
        )
