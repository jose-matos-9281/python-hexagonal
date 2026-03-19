import logging
from dataclasses import dataclass
from typing import Any, Iterable
from uuid import UUID

from example.contacto.domain.contacto import EstadoContacto
from example.contacto.domain.shared import ContactoValue, IdContacto, IdUsuario
from example.contacto.ports.drivens import IContactoRepository
from hexagonal.ports.drivens import IUseCase

from .shared import Examplenapshot, TContactoEvent
from .validar_contacto import ContactoContactado

logger = logging.getLogger(__name__)


class MarcarContactadoUseCase(IUseCase):
    repository: IContactoRepository[Any]

    @dataclass
    class Input:
        id_contacto: IdContacto
        usuario: IdUsuario

    def __init__(
        self,
        repository: IContactoRepository[Any],
        id_contacto: IdContacto | ContactoValue | UUID,
        usuario: IdUsuario | UUID,
    ):
        self.repository = repository
        if isinstance(id_contacto, ContactoValue):
            contacto_id = id_contacto.to_id()
        else:
            contacto_id = IdContacto.from_value(id_contacto)

        self.input = self.Input(
            id_contacto=contacto_id,
            usuario=IdUsuario.from_value(usuario),
        )

    def execute(self) -> Iterable[TContactoEvent]:
        contacto = self.repository.get(self.input.id_contacto)
        if contacto.estado == EstadoContacto.CONTACTADO:
            return []
        contacto.marcar_contactado(self.input.usuario)
        evento = ContactoContactado.new(contacto.state)
        self.repository.save(contacto)
        snap = Examplenapshot.new(contacto.state)
        return [snap, evento]
