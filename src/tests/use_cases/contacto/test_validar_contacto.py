"""
Caso de uso: Validar Contacto
Descripción: Valida el estado de un contacto asignándole un
resultado específico (CONTACTADO, NO_CONTACTADO, NO_CONTACTABLE).
Condiciones previas:
    - El contacto debe existir en el repositorio.
    - El estado proporcionado debe ser uno de los permitidos por el dominio.
Condiciones posteriores:
    - El contacto actualiza su estado según la validación recibida.
    - Se registran el usuario de validación y la fecha de validación.
    - Se emiten los eventos de dominio correspondientes al nuevo estado.
"""

import pytest
from uuid6 import uuid7

from example.contacto.domain.contacto import EstadoContacto
from example.contacto.domain.shared import TipoContacto
from hexagonal.domain import DomainException

from ..base import BaseTest


class TestValidarContacto(BaseTest):
    temp_db = __file__.replace(".py", ".db")

    @classmethod
    def setup_class(cls):
        super().setup_class()
        cls.api = cls.api_wrapper.contacto.contacto
        cls.usuario = uuid7()

    def test_validar_como_contactado(self):
        ## GIVEN: Un nuevo contacto con tipo y valor válidos
        tipo_contacto = TipoContacto.EMAIL
        valor_contacto = "test2@example.com"

        resp = self.api.crear(tipo_contacto.value, valor_contacto, usuario=self.usuario)
        creado = resp.get(self.api.Events.CREADO.value)
        ## WHEN: Marcar el contacto como contactado
        self.logger.info(
            "Marcando contacto con ID %s como CONTACTADO", creado.id_contacto
        )
        resp = self.api.validar(
            creado.id_contacto.value,
            EstadoContacto.CONTACTADO,
            usuario=self.usuario,
        )
        ## THEN: se emiten los eventos
        contactado = resp.get(self.api.Events.CONTACTADO.value, raise_error=False)
        snapshot = resp.get(self.api.Events.SNAPSHOT.value, raise_error=False)
        assert contactado is not None
        assert snapshot is not None

    def test_validar_como_no_contactado(self):
        ## GIVEN: Un nuevo contacto con tipo y valor válidos
        tipo_contacto = TipoContacto.EMAIL
        valor_contacto = "test3@example.com"
        resp = self.api.crear(tipo_contacto.value, valor_contacto, usuario=self.usuario)
        creado = resp.get(self.api.Events.CREADO.value)
        ## WHEN: Marcar el contacto como NO_CONTACTADO
        self.logger.info(
            "Marcando contacto con ID %s como NO_CONTACTADO", creado.id_contacto
        )
        resp = self.api.validar(
            creado.id_contacto.value,
            EstadoContacto.NO_CONTACTADO,
            usuario=self.usuario,
        )
        ## THEN: se emiten los eventos
        no_contactado = resp.get(self.api.Events.NO_CONTACTADO.value, raise_error=False)
        snapshot = resp.get(self.api.Events.SNAPSHOT.value, raise_error=False)
        assert no_contactado is not None
        assert snapshot is not None

    def test_validar_como_no_contactable(self):
        ## GIVEN: Un nuevo contacto con tipo y valor válidos
        tipo_contacto = TipoContacto.EMAIL
        valor_contacto = "test4@example.com"
        resp = self.api.crear(tipo_contacto.value, valor_contacto, usuario=self.usuario)
        creado = resp.get(self.api.Events.CREADO.value)
        ## WHEN: Marcar el contacto como NO_CONTACTABLE
        self.logger.info(
            "Marcando contacto con ID %s como NO_CONTACTABLE", creado.id_contacto
        )
        resp = self.api.validar(
            creado.id_contacto.value,
            EstadoContacto.NO_CONTACTABLE,
            usuario=self.usuario,
        )
        ## THEN: se emiten los eventos
        no_contactable = resp.get(
            self.api.Events.NO_CONTACTABLE.value, raise_error=False
        )
        snapshot = resp.get(self.api.Events.SNAPSHOT.value, raise_error=False)
        assert no_contactable is not None
        assert snapshot is not None

    def test_validar_varias_veces(self):
        ## GIVEN: Un nuevo contacto con tipo y valor válidos
        tipo_contacto = TipoContacto.EMAIL
        valor_contacto = "test5@example.com"
        resp = self.api.crear(tipo_contacto.value, valor_contacto, usuario=self.usuario)
        creado = resp.get(self.api.Events.CREADO.value)

        resp = self.api.validar(
            creado.id_contacto.value,
            EstadoContacto.CONTACTADO,
            usuario=self.usuario,
        )
        contactado = resp.get(self.api.Events.CONTACTADO.value, raise_error=False)
        assert contactado is not None
        ## WHEN: Marcar el contacto con un estado inválido
        self.logger.info(
            "Marcando contacto con ID %s como estado inválido", creado.id_contacto
        )
        resp = self.api.validar(
            creado.id_contacto.value,
            EstadoContacto.NO_CONTACTABLE,
            usuario=self.usuario,
        )
        ## THEN: se emiten los eventos de error
        event = resp.get(self.api.Events.NO_CONTACTABLE.value, raise_error=False)
        assert event is not None

        ## WHEN: Marcar el contacto con un estado válido
        self.logger.info(
            "Marcando contacto con ID %s como NO_CONTACTADO", creado.id_contacto
        )
        resp = self.api.validar(
            creado.id_contacto.value,
            EstadoContacto.NO_CONTACTADO,
            usuario=self.usuario,
        )
        ## THEN: se emiten los eventos de dominio correspondientes
        no_contactado = resp.get(self.api.Events.NO_CONTACTADO.value, raise_error=False)
        snapshot = resp.get(self.api.Events.SNAPSHOT.value, raise_error=False)
        assert no_contactado is not None
        assert snapshot is not None

        ## when: Marcar el contacto como contactado nuevamente
        self.logger.info(
            "Marcando contacto con ID %s como CONTACTADO nuevamente", creado.id_contacto
        )
        resp = self.api.validar(
            creado.id_contacto.value,
            EstadoContacto.CONTACTADO,
            usuario=self.usuario,
        )
        ## THEN: se emiten los eventos de dominio correspondientes
        contactado = resp.get(self.api.Events.CONTACTADO.value, raise_error=False)
        snapshot = resp.get(self.api.Events.SNAPSHOT.value, raise_error=False)
        assert contactado is not None
        assert snapshot is not None

        # WHEN: Marcar el contacto como Sin validar nuevamente
        self.logger.info(
            "Marcando contacto con ID %s como SIN_VALIDAR nuevamente",
            creado.id_contacto,
        )

        with pytest.raises(
            DomainException,
            match="El estado debe ser CONTACTADO, NO_CONTACTADO o NO_CONTACTABLE",
        ):
            resp = self.api.validar(
                creado.id_contacto.value,
                EstadoContacto.SIN_VALIDAR,
                usuario=self.usuario,
            )
