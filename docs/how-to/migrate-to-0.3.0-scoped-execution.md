# Migrate to 0.3.0 scoped execution

This guide is for clients upgrading to `0.3.0`.

The headline is simple:

- shared infrastructure stays shared
- live execution objects do not

If your app already uses `exampleEntrypoint.get(env)` and `exampleAPI(app)` as
the adoption model, the migration should be moderate.
If you built directly against mutable internals, you have cleanup to do. That is
not the library being mean; that is your coupling showing up.

## What changed

The library now treats execution through explicit scopes.

- commands and events use fresh write scopes
- queries use fresh read scopes
- buses resolve handlers inside those scopes
- repositories and `UnitOfWork` instances are scope-bound, not long-lived

What is still safe to share:

- datastore / engine
- mapper and configuration
- provider and factory objects

What should stop being shared:

- `UnitOfWork` instances used for active work
- repositories that hold a live manager/connection boundary
- handlers prebuilt with mutable write dependencies captured forever

## If you are already on the documented path

If your app looks like the example:

- entrypoint chooses infrastructure from environment
- infrastructure builds the app
- callers use `exampleAPI(app)`-style wrappers

then your public calling code should barely change.

The main changes are in bootstrap and wiring.

## Migration checklist

### 1. Stop storing a live `uow` as shared app state

Old mental model:

```python
uow = SQLAlchemyUnitOfWork(connection_manager=manager)
handler = CrearContactoHandler(repo=repo, uow=uow)
```

New mental model:

```python
scope_runner = SQLAlchemyScopeRunner(create_write_scope, create_read_scope)
command_bus.configure_scope_runtime(
    write_scope_runner=scope_runner,
    outbox_repository_getter=lambda scope: scope.outbox_repository,
)
```

The point is not the exact API spelling. The point is that live write objects now
come from scope factories.

### 2. Build repositories inside the scope

Old pattern:

- build repositories once at bootstrap
- reuse them for every command/event/query

New pattern:

- keep datastore and mapper shared
- create repositories from the scope manager created for that operation

Conceptually:

```python
def create_write_scope() -> YourWriteScope:
    manager = create_read_scope()
    contacto_repository = ContactoRepository(mapper, manager)
    outbox_repository = SQLAlchemyOutboxRepository(mapper, manager)
    uow = SQLAlchemyUnitOfWork(
        contacto_repository,
        outbox_repository,
        connection_manager=manager,
    )
    return YourWriteScope(
        uow=uow,
        contacto_repository=contacto_repository,
        outbox_repository=outbox_repository,
    )
```

### 3. Register handler providers, not only prebuilt instances

If you were registering long-lived handler instances that captured repositories
or a mutable `uow`, migrate that wiring so the bus resolves handlers through the
scope runtime.

What changes conceptually:

- before: handler already held write dependencies
- after: handler uses dependencies tied to the active scope

## Client impact by usage style

### Low impact

Your app:

- boots through entrypoints
- exposes a stable API facade
- does not import `hexagonal.adapters.*` directly for new code

What you likely change:

- infrastructure wiring only

### Medium impact

Your app:

- has custom bus bootstrap
- manually assembles SQLAlchemy infrastructure

What you likely change:

- add read/write scope factories
- configure buses with scope runtime
- move repository creation into scopes

### High impact

Your app:

- keeps one `uow` around forever
- stores repositories as singleton collaborators
- depends on compatibility helpers like `attach_repo()` as normal design

What you likely change:

- rewrite bootstrap and handler wiring to provider/factory-based execution

## Compatibility notes

These compatibility paths still exist, but treat them as bridges:

- `uow`
- `attach_repo()`
- `attach_to_unit_of_work()`

They are there to reduce migration pain, not to define the future architecture.

## Recommended rollout plan for clients

1. keep your public API facade stable
2. migrate bootstrap to scope factories
3. move repository creation into scopes
4. configure command/event/query flows with scope runtime
5. remove direct dependencies on long-lived mutable write objects

## Evidence to copy from this repo

- `src/example/app/adapters/drivens/repository/sqlalchemy.py`
- `src/example/app/application/app.py`
- `src/example/app/entrypoints/db/sqlalchemy.py`
- `src/tests/test_parallel_safe_scopes.py`
- `src/tests/test_parallel_dispatch_isolation.py`

Use those files to copy the roles and flow, not the naming.

## Follow-up reading

1. `docs/how-to/bootstrap-sqlalchemy-app.md`
2. `docs/reference/supported-surface.md`
3. `docs/explanation/architecture-from-example.md`
