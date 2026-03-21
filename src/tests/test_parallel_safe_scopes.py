import threading
from pathlib import Path
from typing import Any, cast

from example.contacto.domain.shared import TipoContacto
from hexagonal.domain import CloudMessage
from tests.use_cases.base import (
    bootstrap_example_stack,
    count_inbox_rows,
    count_outbox_rows,
)


def test_write_scopes_create_fresh_mutable_objects_and_reuse_cached_primitives(
    tmp_path: Path,
):
    _, app, _ = bootstrap_example_stack(
        tmp_path / "parallel-safe-scopes.db",
        {"ENV_BUS": "inmemory"},
    )

    infrastructure = cast(Any, app.bus_app).infrastructure

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
    tmp_path: Path,
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


def test_publish_from_outbox_uses_current_write_scope_outbox_repository(tmp_path: Path):
    _, app, api = bootstrap_example_stack(
        tmp_path / "parallel-safe-scope-publish-routing.db",
        {"ENV_BUS": "inmemory"},
    )

    contacto_api = api.contacto.contacto
    created = contacto_api.crear(
        TipoContacto.EMAIL.value,
        "scope-routing@example.com",
    ).get(contacto_api.Events.CREADO.value)
    message = CloudMessage[type(created)].new(created)

    event_bus = cast(Any, app.event_bus)
    root_outbox = event_bus.outbox_repository
    runner = cast(Any, app.bus_app).infrastructure.write_scope_runner
    root_usage: list[str] = []
    scope_usage: list[str] = []
    published_ids: list[object] = []

    original_publish_message = event_bus._publish_message

    def publish_message_noop(cloud_message):
        published_ids.append(cloud_message.message_id)

    event_bus._publish_message = publish_message_noop

    def exercise(scope):
        scope_outbox = scope.outbox_repository
        original_root_fetch_pending = root_outbox.fetch_pending
        original_root_mark_as_published = root_outbox.mark_as_published
        original_scope_fetch_pending = scope_outbox.fetch_pending
        original_scope_mark_as_published = scope_outbox.mark_as_published

        def root_fetch_pending(*args, **kwargs):
            root_usage.append("fetch")
            return [message]

        def root_mark_as_published(*message_ids):
            root_usage.append("mark")
            return original_root_mark_as_published(*message_ids)

        def scope_fetch_pending(*args, **kwargs):
            scope_usage.append("fetch")
            return [message]

        def scope_mark_as_published(*message_ids):
            scope_usage.append("mark")
            return original_scope_mark_as_published(*message_ids)

        root_outbox.fetch_pending = root_fetch_pending
        root_outbox.mark_as_published = root_mark_as_published
        scope_outbox.fetch_pending = scope_fetch_pending
        scope_outbox.mark_as_published = scope_mark_as_published

        try:
            event_bus.publish_from_outbox(limit=1)
        finally:
            root_outbox.fetch_pending = original_root_fetch_pending
            root_outbox.mark_as_published = original_root_mark_as_published
            scope_outbox.fetch_pending = original_scope_fetch_pending
            scope_outbox.mark_as_published = original_scope_mark_as_published

    try:
        runner.run_in_write_scope(exercise)
    finally:
        event_bus._publish_message = original_publish_message

    assert published_ids == [message.message_id]
    assert root_usage == []
    assert scope_usage == ["fetch", "mark"]


def test_publish_from_outbox_marks_failure_with_current_write_scope_outbox_repository(
    tmp_path: Path,
):
    _, app, api = bootstrap_example_stack(
        tmp_path / "parallel-safe-scope-publish-failure-routing.db",
        {"ENV_BUS": "inmemory"},
    )

    contacto_api = api.contacto.contacto
    created = contacto_api.crear(
        TipoContacto.EMAIL.value,
        "scope-routing-failure@example.com",
    ).get(contacto_api.Events.CREADO.value)
    message = CloudMessage[type(created)].new(created)

    event_bus = cast(Any, app.event_bus)
    root_outbox = event_bus.outbox_repository
    runner = cast(Any, app.bus_app).infrastructure.write_scope_runner
    root_usage: list[str] = []
    scope_usage: list[str] = []
    captured_errors: list[str] = []

    original_publish_message = event_bus._publish_message

    def publish_message_boom(cloud_message):
        raise RuntimeError(f"boom:{cloud_message.message_id}")

    event_bus._publish_message = publish_message_boom

    def exercise(scope):
        scope_outbox = scope.outbox_repository
        original_root_fetch_pending = root_outbox.fetch_pending
        original_root_mark_as_failed = root_outbox.mark_as_failed
        original_scope_fetch_pending = scope_outbox.fetch_pending
        original_scope_mark_as_failed = scope_outbox.mark_as_failed

        def root_fetch_pending(*args, **kwargs):
            root_usage.append("fetch")
            return [message]

        def root_mark_as_failed(*message_ids, error):
            root_usage.append("fail")

        def scope_fetch_pending(*args, **kwargs):
            scope_usage.append("fetch")
            return [message]

        def scope_mark_as_failed(*message_ids, error):
            scope_usage.append("fail")
            captured_errors.append(error)

        root_outbox.fetch_pending = root_fetch_pending
        root_outbox.mark_as_failed = root_mark_as_failed
        scope_outbox.fetch_pending = scope_fetch_pending
        scope_outbox.mark_as_failed = scope_mark_as_failed

        try:
            event_bus.publish_from_outbox(limit=1)
        finally:
            root_outbox.fetch_pending = original_root_fetch_pending
            root_outbox.mark_as_failed = original_root_mark_as_failed
            scope_outbox.fetch_pending = original_scope_fetch_pending
            scope_outbox.mark_as_failed = original_scope_mark_as_failed

    try:
        runner.run_in_write_scope(exercise)
    finally:
        event_bus._publish_message = original_publish_message

    assert root_usage == []
    assert scope_usage == ["fetch", "fail"]
    assert captured_errors == [f"boom:{message.message_id}"]


def test_publish_from_outbox_without_active_scope_creates_fresh_write_scope(
    tmp_path: Path,
):
    _, app, api = bootstrap_example_stack(
        tmp_path / "parallel-safe-scope-publish-fresh-scope.db",
        {"ENV_BUS": "inmemory"},
    )

    contacto_api = api.contacto.contacto
    created = contacto_api.crear(
        TipoContacto.EMAIL.value,
        "scope-routing-fresh-scope@example.com",
    ).get(contacto_api.Events.CREADO.value)
    message = CloudMessage[type(created)].new(created)

    event_bus = cast(Any, app.event_bus)
    root_outbox = event_bus.outbox_repository
    runner = cast(Any, app.bus_app).infrastructure.write_scope_runner
    root_usage: list[str] = []
    scope_usage: list[tuple[str, int]] = []
    created_scope_ids: list[int] = []
    published_ids: list[object] = []

    original_publish_message = event_bus._publish_message
    original_create_write_scope = runner._create_write_scope
    original_root_fetch_pending = root_outbox.fetch_pending
    original_root_mark_as_published = root_outbox.mark_as_published

    def publish_message_noop(cloud_message):
        published_ids.append(cloud_message.message_id)

    def record_write_scope():
        scope = original_create_write_scope()
        created_scope_ids.append(id(scope))
        scope_outbox = scope.outbox_repository
        original_scope_fetch_pending = scope_outbox.fetch_pending
        original_scope_mark_as_published = scope_outbox.mark_as_published

        def scope_fetch_pending(*args, **kwargs):
            scope_usage.append(("fetch", id(scope_outbox)))
            return [message]

        def scope_mark_as_published(*message_ids):
            scope_usage.append(("mark", id(scope_outbox)))

        scope_outbox.fetch_pending = scope_fetch_pending
        scope_outbox.mark_as_published = scope_mark_as_published
        return scope

    def root_fetch_pending(*args, **kwargs):
        root_usage.append("fetch")
        return [message]

    def root_mark_as_published(*message_ids):
        root_usage.append("mark")

    runner._create_write_scope = record_write_scope
    event_bus._publish_message = publish_message_noop
    root_outbox.fetch_pending = root_fetch_pending
    root_outbox.mark_as_published = root_mark_as_published

    try:
        event_bus.publish_from_outbox(limit=1)
    finally:
        runner._create_write_scope = original_create_write_scope
        event_bus._publish_message = original_publish_message
        root_outbox.fetch_pending = original_root_fetch_pending
        root_outbox.mark_as_published = original_root_mark_as_published

    assert published_ids == [message.message_id]
    assert len(created_scope_ids) == 1
    assert root_usage == []
    assert [operation for operation, _ in scope_usage] == ["fetch", "mark"]
    assert len({repository_id for _, repository_id in scope_usage}) == 1


def test_publish_from_outbox_without_scope_runtime_falls_back_to_root_repository(
    tmp_path: Path,
):
    _, app, api = bootstrap_example_stack(
        tmp_path / "parallel-safe-scope-publish-root-fallback.db",
        {"ENV_BUS": "inmemory"},
    )

    contacto_api = api.contacto.contacto
    created = contacto_api.crear(
        TipoContacto.EMAIL.value,
        "scope-routing-root-fallback@example.com",
    ).get(contacto_api.Events.CREADO.value)
    message = CloudMessage[type(created)].new(created)

    event_bus = cast(Any, app.event_bus)
    event_bus.configure_scope_runtime()
    root_outbox = event_bus.outbox_repository
    root_usage: list[str] = []
    published_ids: list[object] = []

    original_publish_message = event_bus._publish_message
    original_root_fetch_pending = root_outbox.fetch_pending
    original_root_mark_as_published = root_outbox.mark_as_published

    def publish_message_noop(cloud_message: CloudMessage[Any]):
        published_ids.append(cloud_message.message_id)

    def root_fetch_pending(*args: Any, **kwargs: Any):
        root_usage.append("fetch")
        return [message]

    def root_mark_as_published(*message_ids: Any):
        root_usage.append("mark")

    event_bus._publish_message = publish_message_noop
    root_outbox.fetch_pending = root_fetch_pending
    root_outbox.mark_as_published = root_mark_as_published

    try:
        event_bus.publish_from_outbox(limit=1)
    finally:
        event_bus._publish_message = original_publish_message
        root_outbox.fetch_pending = original_root_fetch_pending
        root_outbox.mark_as_published = original_root_mark_as_published

    assert published_ids == [message.message_id]
    assert root_usage == ["fetch", "mark"]


def test_publish_from_outbox_nested_same_thread_is_reentrant_and_no_deadlock(
    tmp_path: Path,
):
    _, app, api = bootstrap_example_stack(
        tmp_path / "parallel-safe-scope-nested-publish.db",
        {"ENV_BUS": "inmemory"},
    )

    contacto_api = api.contacto.contacto
    created = contacto_api.crear(
        TipoContacto.EMAIL.value,
        "scope-nested-publish@example.com",
    ).get(contacto_api.Events.CREADO.value)
    message = CloudMessage[type(created)].new(created)

    event_bus = cast(Any, app.event_bus)
    event_bus.configure_scope_runtime()
    root_outbox = event_bus.outbox_repository
    publish_calls: list[object] = []
    mark_calls: list[object] = []
    fetch_calls: list[str] = []
    nested_triggered = False

    original_publish_message = event_bus._publish_message
    original_fetch_pending = root_outbox.fetch_pending
    original_mark_as_published = root_outbox.mark_as_published

    def fetch_pending(*args: Any, **kwargs: Any):
        fetch_calls.append("fetch")
        if len(fetch_calls) == 1:
            return [message]
        return []

    def mark_as_published(*message_ids: Any):
        mark_calls.extend(message_ids)

    def nested_publish_once(cloud_message: CloudMessage[Any]):
        nonlocal nested_triggered
        publish_calls.append(cloud_message.message_id)
        if not nested_triggered:
            nested_triggered = True
            event_bus.publish_from_outbox(limit=1)

    root_outbox.fetch_pending = fetch_pending
    root_outbox.mark_as_published = mark_as_published
    event_bus._publish_message = nested_publish_once

    try:
        event_bus.publish_from_outbox(limit=1)
    finally:
        root_outbox.fetch_pending = original_fetch_pending
        root_outbox.mark_as_published = original_mark_as_published
        event_bus._publish_message = original_publish_message

    assert nested_triggered is True
    assert fetch_calls == ["fetch", "fetch"]
    assert publish_calls == [message.message_id]
    assert mark_calls == [message.message_id]


def test_publish_from_outbox_releases_lock_after_failure_for_retry_attempt(
    tmp_path: Path,
):
    _, app, api = bootstrap_example_stack(
        tmp_path / "parallel-safe-scope-publish-failure-retry.db",
        {"ENV_BUS": "inmemory"},
    )

    contacto_api = api.contacto.contacto
    created = contacto_api.crear(
        TipoContacto.EMAIL.value,
        "scope-publish-failure-retry@example.com",
    ).get(contacto_api.Events.CREADO.value)
    message = CloudMessage[type(created)].new(created)

    event_bus = cast(Any, app.event_bus)
    event_bus.configure_scope_runtime()
    root_outbox = event_bus.outbox_repository
    failure_errors: list[str] = []
    published_ids: list[object] = []
    publish_attempts = 0

    original_publish_message = event_bus._publish_message
    original_fetch_pending = root_outbox.fetch_pending
    original_mark_as_failed = root_outbox.mark_as_failed
    original_mark_as_published = root_outbox.mark_as_published

    def fetch_pending(*args: Any, **kwargs: Any):
        return [message]

    def mark_as_failed(*message_ids: Any, error: str):
        failure_errors.append(error)

    def mark_as_published(*message_ids: Any):
        published_ids.extend(message_ids)

    def fail_then_succeed(cloud_message: CloudMessage[Any]):
        nonlocal publish_attempts
        publish_attempts += 1
        if publish_attempts == 1:
            raise RuntimeError("first-attempt-failure")

    root_outbox.fetch_pending = fetch_pending
    root_outbox.mark_as_failed = mark_as_failed
    root_outbox.mark_as_published = mark_as_published
    event_bus._publish_message = fail_then_succeed

    retry_done = threading.Event()

    def retry_publish() -> None:
        event_bus.publish_from_outbox(limit=1)
        retry_done.set()

    try:
        event_bus.publish_from_outbox(limit=1)
        retry_thread = threading.Thread(target=retry_publish)
        retry_thread.start()
        retry_thread.join(timeout=2)
    finally:
        root_outbox.fetch_pending = original_fetch_pending
        root_outbox.mark_as_failed = original_mark_as_failed
        root_outbox.mark_as_published = original_mark_as_published
        event_bus._publish_message = original_publish_message

    assert retry_done.is_set()
    assert publish_attempts == 2
    assert failure_errors == ["first-attempt-failure"]
    assert published_ids == [message.message_id]


def test_read_scopes_create_fresh_managers_and_repositories(tmp_path: Path):
    _, app, _ = bootstrap_example_stack(
        tmp_path / "parallel-safe-read-scopes.db",
        {"ENV_BUS": "inmemory"},
    )

    infrastructure = cast(Any, app.bus_app).infrastructure
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
