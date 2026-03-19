"""
Caso de uso: Validar Entidad Contacto
Descripción: Valida si un contacto realmente pertenece o corresponde
    a la entidad vinculada.
Condiciones previas:
    - La relación EntidadContacto debe existir previamente.
    - El resultado de validación debe ser CORRESPONDE o NO_CORRESPONDE.
Condiciones posteriores:
    - El estado de la relación se actualiza según el resultado.
    - Se registra el usuario responsable y la fecha de validación.
    - Se emiten los eventos de dominio correspondientes
      (EntidadContactoCorresponde o EntidadContactoNoCorresponde).
"""

import pytest
from uuid6 import uuid7

from example.contacto.domain.entidad_contacto import ValidacionEntidadContacto
from example.contacto.domain.shared import TipoContacto, TipoEntidad
from hexagonal.domain import DomainValueError

from ..base import BaseTest


class TestValidarEntidadContacto(BaseTest):
    temp_db = __file__.replace(".py", ".db")

    @classmethod
    def setup_class(cls):
        super().setup_class()
        cls.contacto_api = cls.api_wrapper.contacto.contacto
        cls.entidad_api = cls.api_wrapper.contacto.entidad
        cls.api = cls.api_wrapper.contacto.entidad_contacto
        cls.usuario = uuid7()

    def _crear_entidad_contacto(self, *, suffix: str):
        contacto_resp = self.contacto_api.crear(
            TipoContacto.EMAIL.value,
            f"validar-entidad-contacto-{suffix}@example.com",
            usuario=self.usuario,
        )
        contacto_creado = contacto_resp.get(self.contacto_api.Events.CREADO.value)

        entidad_resp = self.entidad_api.crear(
            TipoEntidad.AFILIADO,
            {
                "cd_asegurado": f"4000000{suffix}",
                "cd_dependiente": suffix,
            },
        )
        entidad_creada = entidad_resp.get(self.entidad_api.Events.CREADA.value)

        resp = self.api.crear(
            entidad_creada.id_entidad.value,
            contacto_creado.id_contacto.value,
            usuario=self.usuario,
        )
        creado = resp.get(self.api.Events.CREADO.value)
        return entidad_creada, contacto_creado, creado

    def test_validar_entidad_contacto_como_corresponde(self):
        entidad_creada, contacto_creado, creado = self._crear_entidad_contacto(
            suffix="1"
        )

        resp = self.api.validar(
            entidad_creada.id_entidad.value,
            contacto_creado.id_contacto.value,
            ValidacionEntidadContacto.CORRESPONDE,
            self.usuario,
        )

        corresponde = resp.get(self.api.Events.CORRESPONDE.value, raise_error=False)
        snapshot = resp.get(self.api.Events.SNAPSHOT.value, raise_error=False)

        assert corresponde is not None
        assert snapshot is not None

        entidad_contacto = self.api.get(creado.id_entidad_contacto.value)
        assert entidad_contacto.validacion == ValidacionEntidadContacto.CORRESPONDE
        assert entidad_contacto.usuario_validacion.value == self.usuario
        assert entidad_contacto.fecha_validacion is not None

    def test_validar_entidad_contacto_como_no_corresponde(self):
        entidad_creada, contacto_creado, creado = self._crear_entidad_contacto(
            suffix="2"
        )

        resp = self.api.validar(
            entidad_creada.id_entidad.value,
            contacto_creado.id_contacto.value,
            ValidacionEntidadContacto.NO_CORRESPONDE,
            self.usuario,
        )

        no_corresponde = resp.get(
            self.api.Events.NO_CORRESPONDE.value, raise_error=False
        )
        snapshot = resp.get(self.api.Events.SNAPSHOT.value, raise_error=False)

        assert no_corresponde is not None
        assert snapshot is not None

        entidad_contacto = self.api.get(creado.id_entidad_contacto.value)
        assert entidad_contacto.validacion == ValidacionEntidadContacto.NO_CORRESPONDE
        assert entidad_contacto.usuario_validacion.value == self.usuario
        assert entidad_contacto.fecha_validacion is not None

    def test_validar_entidad_contacto_rechaza_estado_no_validado(self):
        entidad_creada, contacto_creado, _ = self._crear_entidad_contacto(suffix="3")

        with pytest.raises(
            DomainValueError,
            match="La validación debe ser CORRESPONDE o NO_CORRESPONDE",
        ):
            self.api.validar(
                entidad_creada.id_entidad.value,
                contacto_creado.id_contacto.value,
                ValidacionEntidadContacto.NO_VALIDADO,
                self.usuario,
            )
