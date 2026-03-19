import threading
from pathlib import Path

from example.contacto.domain.shared import TipoContacto
from tests.use_cases.base import bootstrap_example_stack


def test_write_scope_runner_isolates_worker_threads(tmp_path: Path):
    _, app, _ = bootstrap_example_stack(
        tmp_path / "parallel-dispatch-isolation.db",
        {"ENV_BUS": "inmemory"},
    )

    runner = app.bus_app.infrastructure.write_scope_runner
    seen: dict[str, tuple[int, int, int]] = {}

    seen["main"] = runner.run_in_write_scope(
        lambda scope: (
            threading.get_ident(),
            id(scope.uow),
            id(scope.uow.connection_manager),
        )
    )

    worker_done = threading.Event()

    def worker() -> None:
        seen["worker"] = runner.run_in_write_scope(
            lambda scope: (
                threading.get_ident(),
                id(scope.uow),
                id(scope.uow.connection_manager),
            )
        )
        worker_done.set()

    thread = threading.Thread(target=worker)
    thread.start()
    thread.join(timeout=5)

    assert worker_done.is_set()
    assert seen["worker"][0] != seen["main"][0]
    assert seen["worker"][1] != seen["main"][1]
    assert seen["worker"][2] != seen["main"][2]


def test_write_scope_runner_reuses_same_scope_for_nested_same_thread_work(tmp_path):
    _, app, _ = bootstrap_example_stack(
        tmp_path / "parallel-dispatch-nested.db",
        {"ENV_BUS": "inmemory"},
    )

    runner = app.bus_app.infrastructure.write_scope_runner

    def outer(scope):
        current_scope_ids = (id(scope.uow), id(scope.uow.connection_manager))
        nested_scope_ids = runner.run_in_write_scope(
            lambda nested_scope: (
                id(nested_scope.uow),
                id(nested_scope.uow.connection_manager),
            )
        )
        return current_scope_ids, nested_scope_ids

    current_scope_ids, nested_scope_ids = runner.run_in_write_scope(outer)

    assert nested_scope_ids == current_scope_ids


def test_queued_command_worker_uses_an_isolated_write_scope_end_to_end(tmp_path: Path):
    _, app, api = bootstrap_example_stack(
        tmp_path / "parallel-dispatch-command-worker.db",
        {
            "ENV_BUS": "inmemory_queue",
            "EVENT_BUS_WORKER_DAEMON": "false",
        },
    )

    runner = app.bus_app.infrastructure.write_scope_runner
    main_scope = runner.run_in_write_scope(
        lambda scope: (
            threading.get_ident(),
            id(scope.uow),
            id(scope.uow.connection_manager),
        )
    )

    created_scopes: list[tuple[int, int, int]] = []
    original_create_write_scope = runner._create_write_scope

    def record_write_scope():
        scope = original_create_write_scope()
        created_scopes.append(
            (
                threading.get_ident(),
                id(scope.uow),
                id(scope.uow.connection_manager),
            )
        )
        return scope

    runner._create_write_scope = record_write_scope
    created_event = {}
    contacto_api = api.contacto.contacto

    app.command_bus.consume()
    app.event_bus.consume()
    app.event_bus.wait_for_publish(
        contacto_api.Events.CREADO.value,
        lambda event: created_event.setdefault("value", event),
    )

    try:
        response = contacto_api.crear(
            TipoContacto.EMAIL.value,
            "queued-worker@example.com",
            async_dispatch=True,
        )

        assert response.has_events is False

        app.command_bus.publish_from_outbox()
        app.command_bus.queue.join()
        app.event_bus.queue.join()

        created = created_event.get("value")
        assert created is not None
        assert (
            contacto_api.get(created.id_contacto.value).contacto.value
            == "queued-worker@example.com"
        )

        worker_scopes = [scope for scope in created_scopes if scope[0] != main_scope[0]]

        assert worker_scopes
        assert all(scope[1] != main_scope[1] for scope in worker_scopes)
        assert all(scope[2] != main_scope[2] for scope in worker_scopes)
    finally:
        runner._create_write_scope = original_create_write_scope
        app.command_bus.shutdown()
        app.event_bus.shutdown()
