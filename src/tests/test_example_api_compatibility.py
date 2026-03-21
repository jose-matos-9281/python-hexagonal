from pathlib import Path

from example import exampleEntrypoint
from example.app.entrypoints.db.sqlalchemy import SQLAlchemyexampleEntrypoint
from example.app.entrypoints.main import exampleEntrypoint as main_example_entrypoint
from example.contacto.domain.shared import TipoContacto
from tests.use_cases.base import (
    bootstrap_example_stack,
    build_example_env,
    count_outbox_rows,
    migrate_example_database,
    reset_example_runtime_state,
)


def test_public_example_exports_keep_bootstrap_contract(tmp_path: Path):
    assert exampleEntrypoint is main_example_entrypoint

    _, app, api = bootstrap_example_stack(
        tmp_path / "example-api-compatibility.db",
        {"ENV_BUS": "inmemory"},
    )

    assert api.app is app
    assert api.contacto.app is app

    contacto_api = api.contacto.contacto
    response = contacto_api.crear(TipoContacto.EMAIL.value, "compat@example.com")
    created = response.get(contacto_api.Events.CREADO.value, raise_error=False)

    assert created is not None
    assert (
        contacto_api.get(created.id_contacto.value).contacto.value
        == "compat@example.com"
    )
    assert count_outbox_rows(app) == 2
    assert count_outbox_rows(app, published=True) == 2
    assert count_outbox_rows(app, published=False) == 0


def test_sqlalchemy_example_entrypoint_still_builds_a_bus_app(tmp_path: Path):
    env = build_example_env(
        tmp_path / "example-db-entrypoint-compatibility.db",
        {"ENV_BUS": "inmemory"},
    )
    reset_example_runtime_state()
    migrate_example_database(env)

    app = SQLAlchemyexampleEntrypoint.get(env)

    assert app.infrastructure is not None
    assert app.uow is app.infrastructure.uow

    reset_example_runtime_state()
