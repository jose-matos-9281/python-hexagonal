from example.contacto.domain.shared import TipoContacto
from tests.use_cases.base import (
    bootstrap_example_stack,
    count_inbox_rows,
    count_outbox_rows,
)


def test_write_scopes_create_fresh_mutable_objects_and_reuse_cached_primitives(
    tmp_path,
):
    _, app, _ = bootstrap_example_stack(
        tmp_path / "parallel-safe-scopes.db",
        {"ENV_BUS": "inmemory"},
    )

    infrastructure = app.bus_app.infrastructure

    first_scope = infrastructure.create_write_scope()
    second_scope = infrastructure.create_write_scope()

    assert first_scope is not second_scope
    assert first_scope.uow is not second_scope.uow
    assert first_scope.uow.connection_manager is not second_scope.uow.connection_manager
    assert first_scope.contacto_repository is not second_scope.contacto_repository
    assert first_scope.entidad_repository is not second_scope.entidad_repository
    assert (
        first_scope.entidad_contacto_repository
        is not second_scope.entidad_contacto_repository
    )

    assert (
        first_scope.uow.connection_manager.datastore
        is second_scope.uow.connection_manager.datastore
    )
    assert (
        first_scope.contacto_repository._mapper
        is second_scope.contacto_repository._mapper
    )
    assert (
        first_scope.entidad_repository._mapper
        is second_scope.entidad_repository._mapper
    )
    assert first_scope.inbox_repository is not second_scope.inbox_repository
    assert first_scope.outbox_repository is not second_scope.outbox_repository


def test_scoped_command_execution_publishes_without_leaking_pending_outbox_rows(
    tmp_path,
):
    _, app, api = bootstrap_example_stack(
        tmp_path / "parallel-safe-scope-outbox.db",
        {"ENV_BUS": "inmemory"},
    )

    before_outbox_total = count_outbox_rows(app)
    before_outbox_pending = count_outbox_rows(app, published=False)
    before_inbox_processed = count_inbox_rows(app, processed=True)

    api.contacto.contacto.crear(TipoContacto.EMAIL.value, "scope-check@example.com")

    assert count_outbox_rows(app) - before_outbox_total == 2
    assert count_outbox_rows(app, published=False) == before_outbox_pending
    assert count_outbox_rows(app, published=True) - before_outbox_total == 2
    assert count_inbox_rows(app, processed=True) - before_inbox_processed == 1


def test_read_scopes_create_fresh_managers_and_repositories(tmp_path):
    _, app, _ = bootstrap_example_stack(
        tmp_path / "parallel-safe-read-scopes.db",
        {"ENV_BUS": "inmemory"},
    )

    infrastructure = app.bus_app.infrastructure
    runner = infrastructure.read_scope_runner

    first_scope = runner.run_in_read_scope(
        lambda manager: (
            manager,
            infrastructure.build_contacto_repository(manager),
            infrastructure.build_entidad_contacto_repository(manager),
            manager.datastore,
        )
    )
    second_scope = runner.run_in_read_scope(
        lambda manager: (
            manager,
            infrastructure.build_contacto_repository(manager),
            infrastructure.build_entidad_contacto_repository(manager),
            manager.datastore,
        )
    )

    assert first_scope[0] is not second_scope[0]
    assert first_scope[1] is not second_scope[1]
    assert first_scope[2] is not second_scope[2]
    assert first_scope[3] is second_scope[3]
