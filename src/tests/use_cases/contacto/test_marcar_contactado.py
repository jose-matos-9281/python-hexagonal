"""
Caso de uso: Marcar Contactado
Descripción:
    Marca un contacto como "CONTACTADO" ,
    cuando se emite el evento de EntidadContactoCorresponde.
Condiciones previas:
    - El contacto debe existir en el repositorio.
    - El contacto no debe estar ya en estado CONTACTADO
        (si lo está, no se realiza acción).
Condiciones posteriores:
    - El estado del contacto cambia a CONTACTADO.
    - El usuario que realiza la acción queda registrado en el contacto.
    - Se emiten los eventos Examplenapshot y ContactoContactado.
"""

from uuid6 import uuid7

from example.contacto.domain.contacto import EstadoContacto
from example.contacto.domain.entidad_contacto import IdEntidadContacto
from example.contacto.domain.shared import IdEntidad, TipoContacto

from ..base import BaseTest, count_inbox_rows, count_outbox_rows


class TestMarcarContactado(BaseTest):
    temp_db = __file__.replace(".py", ".db")
    env = {
        "EVENT_BUS_WORKER_DAEMON": "false",
    }

    @classmethod
    def setup_class(cls):
        super().setup_class()
        cls.api = cls.api_wrapper.contacto.contacto
        cls.ec_api = cls.api_wrapper.contacto.entidad_contacto
        cls.usuario = uuid7()
        cls.id_entidad = IdEntidad.from_value(uuid7())
        cls.id_entidad_contacto = IdEntidadContacto.from_value(uuid7())

        # Eventos
        cls.CONTACTADO = cls.api.Events.CONTACTADO.value
        cls.SNAPSHOT = cls.api.Events.SNAPSHOT.value
        cls.CORRESPONDE = cls.ec_api.Events.CORRESPONDE.value
        cls.CREADO = cls.api.Events.CREADO.value

        cls.app.event_bus.consume()

    @classmethod
    def teardown_class(cls):
        shutdown = getattr(cls.app.event_bus, "shutdown", None)
        if callable(shutdown):
            shutdown()
        # Cerrar el bus de eventos después de las pruebas

    def test_marcar_contactado(self):
        ## GIVEN: Un contacto creado previamente
        tipo_contacto = TipoContacto.EMAIL
        valor_contacto = "test@example.com"
        resp = self.api.crear(tipo_contacto.value, valor_contacto, usuario=self.usuario)
        creado = resp.get(self.CREADO)
        assert creado.usuario is not None
        snapshot = resp.get(self.SNAPSHOT)
        assert snapshot.estado == EstadoContacto.SIN_VALIDAR

        ## WHEN: Emitir el evento de EntidadContactoCorresponde

        event = self.CORRESPONDE(
            id_entidad_contacto=self.id_entidad_contacto,
            entidad=self.id_entidad,
            contacto=creado.id_contacto,
            usuario=creado.usuario,
        )
        outbox_before = count_outbox_rows(self.app)
        inbox_before = count_inbox_rows(self.app, processed=True)
        resp = self.api.publish_and_wait(
            event,
            wait=0.5,
            events=[self.SNAPSHOT, self.CONTACTADO],
        )
        # THEN: se emiten los eventos
        snapshot = resp.get(self.SNAPSHOT, raise_error=False)
        contactado = resp.get(self.CONTACTADO, raise_error=False)
        assert snapshot is not None
        assert contactado is not None
        # THEN: el contacto se actualiza con estado CONTACTADO y usuario registrado
        contacto = self.api.get(creado.id_contacto.value)
        assert contacto.estado == EstadoContacto.CONTACTADO
        assert count_outbox_rows(self.app) - outbox_before == 3
        assert count_outbox_rows(self.app, published=False) == 0
        assert count_inbox_rows(self.app, processed=True) - inbox_before == 1
