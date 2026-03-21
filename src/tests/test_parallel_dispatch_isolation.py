import threading
from pathlib import Path
from typing import Any, cast

from example.contacto.domain.shared import TipoContacto
from tests.use_cases.base import bootstrap_example_stack


def test_write_scope_runner_isolates_worker_threads(tmp_path: Path):
    _, app, _ = bootstrap_example_stack(
        tmp_path / "parallel-dispatch-isolation.db",
        {"ENV_BUS": "inmemory"},
    )

    runner = cast(Any, app.bus_app).infrastructure.write_scope_runner
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

    runner = cast(Any, app.bus_app).infrastructure.write_scope_runner

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

    runner = cast(Any, app.bus_app).infrastructure.write_scope_runner
    main_scope = runner.run_in_write_scope(
        lambda scope: (
            threading.get_ident(),
            scope.uow,
            scope.uow.connection_manager,
        )
    )

    created_scopes: list[tuple[int, Any, Any]] = []
    original_create_write_scope = runner._create_write_scope

    def record_write_scope():
        scope = original_create_write_scope()
        created_scopes.append(
            (
                threading.get_ident(),
                scope.uow,
                scope.uow.connection_manager,
            )
        )
        return scope

    runner._create_write_scope = record_write_scope
    created_event = {}
    contacto_api = api.contacto.contacto
    command_bus = cast(Any, app.command_bus)
    event_bus = cast(Any, app.event_bus)

    command_bus.consume()
    event_bus.consume()
    event_bus.wait_for_publish(
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

        command_bus.publish_from_outbox()
        command_bus.queue.join()
        event_bus.queue.join()

        created = created_event.get("value")
        assert created is not None
        assert (
            contacto_api.get(created.id_contacto.value).contacto.value
            == "queued-worker@example.com"
        )

        worker_scopes = [scope for scope in created_scopes if scope[0] != main_scope[0]]

        assert worker_scopes
        assert all(scope[1] is not main_scope[1] for scope in worker_scopes)
        assert all(scope[2] is not main_scope[2] for scope in worker_scopes)
    finally:
        runner._create_write_scope = original_create_write_scope
        command_bus.shutdown()
        event_bus.shutdown()


def test_queued_command_publish_from_outbox_uses_scoped_repository(tmp_path: Path):
    _, app, api = bootstrap_example_stack(
        tmp_path / "parallel-dispatch-command-publish-routing.db",
        {
            "ENV_BUS": "inmemory_queue",
            "EVENT_BUS_WORKER_DAEMON": "false",
        },
    )

    runner = cast(Any, app.bus_app).infrastructure.write_scope_runner
    command_bus = cast(Any, app.command_bus)
    contacto_api = api.contacto.contacto
    main_scope = runner.run_in_write_scope(
        lambda scope: (
            threading.get_ident(),
            id(scope.uow),
            id(scope.uow.connection_manager),
        )
    )

    created_scopes: list[tuple[int, int, int]] = []
    scoped_publish_usage: list[tuple[int, str, int, int]] = []
    root_publish_usage: list[str] = []
    published_ids: list[object] = []
    original_create_write_scope = runner._create_write_scope
    original_publish_message = command_bus._publish_message
    root_outbox = command_bus.outbox_repository
    original_root_fetch_pending = root_outbox.fetch_pending
    original_root_mark_as_published = root_outbox.mark_as_published

    def record_write_scope():
        scope = original_create_write_scope()
        created_scopes.append(
            (
                threading.get_ident(),
                id(scope.uow),
                id(scope.uow.connection_manager),
            )
        )
        scope_outbox = scope.outbox_repository
        original_scope_fetch_pending = scope_outbox.fetch_pending
        original_scope_mark_as_published = scope_outbox.mark_as_published

        def scope_fetch_pending(*args, **kwargs):
            scoped_publish_usage.append(
                (
                    threading.get_ident(),
                    "fetch",
                    id(scope.uow),
                    id(scope_outbox),
                )
            )
            return original_scope_fetch_pending(*args, **kwargs)

        def scope_mark_as_published(*message_ids):
            scoped_publish_usage.append(
                (
                    threading.get_ident(),
                    "mark",
                    id(scope.uow),
                    id(scope_outbox),
                )
            )
            return original_scope_mark_as_published(*message_ids)

        scope_outbox.fetch_pending = scope_fetch_pending
        scope_outbox.mark_as_published = scope_mark_as_published
        return scope

    def root_fetch_pending(*args, **kwargs):
        root_publish_usage.append("fetch")
        return original_root_fetch_pending(*args, **kwargs)

    def root_mark_as_published(*message_ids):
        root_publish_usage.append("mark")
        return original_root_mark_as_published(*message_ids)

    def publish_message_noop(message):
        published_ids.append(message.message_id)

    runner._create_write_scope = record_write_scope
    command_bus._publish_message = publish_message_noop
    root_outbox.fetch_pending = root_fetch_pending
    root_outbox.mark_as_published = root_mark_as_published

    try:
        response = contacto_api.crear(
            TipoContacto.EMAIL.value,
            "queued-publish-routing@example.com",
            async_dispatch=True,
        )

        assert response.has_events is False

        command_bus.publish_from_outbox()

        publish_scopes = [
            scope for scope in created_scopes if scope[0] == main_scope[0]
        ]

        assert published_ids
        assert root_publish_usage == []
        assert [operation for _, operation, _, _ in scoped_publish_usage] == [
            "fetch",
            "mark",
        ]
        assert publish_scopes
        assert all(scope[1] != main_scope[1] for scope in publish_scopes)
        assert (
            len({repository_id for _, _, _, repository_id in scoped_publish_usage}) == 1
        )
    finally:
        runner._create_write_scope = original_create_write_scope
        command_bus._publish_message = original_publish_message
        root_outbox.fetch_pending = original_root_fetch_pending
        root_outbox.mark_as_published = original_root_mark_as_published


def test_concurrent_publish_from_outbox_on_same_bus_is_serialized(tmp_path: Path):
    _, app, api = bootstrap_example_stack(
        tmp_path / "parallel-dispatch-single-bus-serialized.db",
        {
            "ENV_BUS": "inmemory_queue",
            "EVENT_BUS_WORKER_DAEMON": "false",
        },
    )

    command_bus = cast(Any, app.command_bus)
    contacto_api = api.contacto.contacto

    response = contacto_api.crear(
        TipoContacto.EMAIL.value,
        "parallel-single-bus@example.com",
        async_dispatch=True,
    )
    assert response.has_events is False

    first_inside = threading.Event()
    release_first = threading.Event()
    active_cycles = 0
    max_overlap = 0
    published_ids: list[object] = []

    original_run_with_outbox_repository = command_bus._run_with_outbox_repository
    original_publish_message = command_bus._publish_message

    def publish_message_noop(message):
        published_ids.append(message.message_id)

    def tracked_run_with_outbox_repository(work):
        nonlocal active_cycles, max_overlap
        active_cycles += 1
        max_overlap = max(max_overlap, active_cycles)
        if active_cycles == 1:
            first_inside.set()
            release_first.wait(timeout=2)
        try:
            return original_run_with_outbox_repository(work)
        finally:
            active_cycles -= 1

    command_bus._publish_message = publish_message_noop
    command_bus._run_with_outbox_repository = tracked_run_with_outbox_repository

    try:
        first_thread = threading.Thread(target=command_bus.publish_from_outbox)
        second_thread = threading.Thread(target=command_bus.publish_from_outbox)

        first_thread.start()
        assert first_inside.wait(timeout=2)
        second_thread.start()

        # If serialization holds, second thread must still be waiting on the lock here.
        assert second_thread.is_alive()
        assert max_overlap == 1

        release_first.set()
        first_thread.join(timeout=2)
        second_thread.join(timeout=2)
    finally:
        command_bus._publish_message = original_publish_message
        command_bus._run_with_outbox_repository = original_run_with_outbox_repository

    assert not first_thread.is_alive()
    assert not second_thread.is_alive()
    assert max_overlap == 1
    assert len(set(published_ids)) == 1


def test_publish_lock_scope_is_per_bus_instance(tmp_path: Path):
    _, app, _ = bootstrap_example_stack(
        tmp_path / "parallel-dispatch-per-bus-instance.db",
        {
            "ENV_BUS": "inmemory_queue",
            "EVENT_BUS_WORKER_DAEMON": "false",
        },
    )

    command_bus = cast(Any, app.command_bus)
    event_bus = cast(Any, app.event_bus)

    command_entered = threading.Event()
    event_entered = threading.Event()
    release_both = threading.Event()

    original_command_run = command_bus._run_with_outbox_repository
    original_event_run = event_bus._run_with_outbox_repository

    def tracked_command_run(work):
        command_entered.set()
        release_both.wait(timeout=2)
        return original_command_run(work)

    def tracked_event_run(work):
        event_entered.set()
        release_both.wait(timeout=2)
        return original_event_run(work)

    command_bus._run_with_outbox_repository = tracked_command_run
    event_bus._run_with_outbox_repository = tracked_event_run

    try:
        command_thread = threading.Thread(target=command_bus.publish_from_outbox)
        event_thread = threading.Thread(target=event_bus.publish_from_outbox)

        command_thread.start()
        event_thread.start()

        assert command_entered.wait(timeout=2)
        assert event_entered.wait(timeout=2)

        release_both.set()

        command_thread.join(timeout=2)
        event_thread.join(timeout=2)
    finally:
        command_bus._run_with_outbox_repository = original_command_run
        event_bus._run_with_outbox_repository = original_event_run

    assert not command_thread.is_alive()
    assert not event_thread.is_alive()
