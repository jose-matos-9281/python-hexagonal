# First app from the example

This guide is for first-time adopters.
The job is not to memorize framework internals. The job is to understand the
shape of a real app and then translate that shape into your own codebase.

## Outcome

By the end of this guide you should be able to explain:

- what belongs in domain, application, ports, adapters, and entrypoints
- how the example app assembles those layers
- which imports are part of the documented path and which ones are evidence only
- how the use-case tests prove the app wiring

## Read the blueprint in this order

### 1. Start at the domain

Read `src/example/contacto/domain/contacto.py` first.

That file shows the part that actually matters in hexagonal architecture:

- value objects and IDs define the language of the domain
- `Contacto` keeps business state and transitions
- commands change aggregate state
- queries stay explicit instead of leaking repository details everywhere

The important lesson is not the example names. The important lesson is that the
domain owns behavior and vocabulary before infrastructure gets involved.

### 2. Define the contracts around the domain

Read these files next:

- `src/example/contacto/ports/drivens.py`
- `src/example/contacto/ports/drivers.py`

`drivens.py` defines the infrastructure the app needs: repositories, scope
creation, and unit-of-work boundaries. `drivers.py` defines the
application-facing contract.

That separation matters because the application layer depends on interfaces, not
database code.

### 3. Compose the application layer

Read `src/example/contacto/application/app.py`.

That file wires infrastructure into several bus apps and then groups them with
`BusAppGroup`. The pattern is simple:

1. verify infrastructure
2. create focused app modules for each capability
3. compose them behind one application object

If you are new to the library, THIS is the pattern to copy. Not the module
names. Not the `contacto` bounded context. The composition pattern.

### 4. Expose a narrow API facade

Read these files together:

- `src/example/contacto/application/api.py`
- `src/example/contacto/application/contacto/api.py`
- `src/example/app/application/api.py`

The example uses `BaseAPI` wrappers so tests and consumers call intentful
methods like `crear()` and `validar()` instead of shoving raw bus operations all
over the codebase.

Conceptually the wrapper looks like this:

```python
from hexagonal.application.api import BaseAPI, TBaseApp


class YourAppAPI(BaseAPI[TBaseApp]):
    def __init__(self, app: TBaseApp):
        super().__init__(app)
        self._contacts = ContactsAPI(app)

    @property
    def contacts(self) -> ContactsAPI[TBaseApp]:
        return self._contacts
```

That is the point: give callers a stable, intention-revealing facade over the
application buses.

### 5. Bootstrap through entrypoints

Read these files:

- `src/example/app/entrypoints/main.py`
- `src/example/app/entrypoints/db/sqlalchemy.py`

The example does NOT start from `hexagonal.__init__`.
It starts from entrypoints.

`exampleEntrypoint` is an `EntrypointGroup` that selects an infrastructure
variant from environment. The SQLAlchemy variant then uses
`SQLAlchemyInfrastructureEntrypoint` to build the mapper, datastore, and
connection manager before creating the app.

If you need reusable SQLAlchemy repository or unit-of-work primitives in your
own adapter code, import them from `hexagonal.integrations.sqlalchemy`. That is
the supported adapter-specific extension surface, not the old
`hexagonal.adapters...` path.

Conceptually the pattern looks like this:

```python
from hexagonal.entrypoints import Entrypoint, EntrypointGroup
from hexagonal.entrypoints.sqlalchemy import SQLAlchemyAppEntrypoint


class Sqlalchemy(Entrypoint[object]):
    @classmethod
    def get(cls, env=None):
        class AppEntrypoint(SQLAlchemyAppEntrypoint):
            BUS_APP = YourInfrastructureEntrypoint
            BUS_GROUP = YourBusEntrypointGroup

        return AppEntrypoint.get(env)


class YourEntrypoint(EntrypointGroup[object]):
    env_key = "ENV_REPOSITORY"
    entrypoints = [Sqlalchemy]
    env = {"ENV_REPOSITORY": "sqlalchemy"}
```

Use the pattern. Translate the names. Do not copy example identifiers into your
real domain unless you enjoy future cleanup debt.

### 6. Prove the workflow with use-case tests

Read `src/tests/use_cases/base.py` and then the contacto tests under
`src/tests/use_cases/contacto/`.

The test bootstrap proves the intended flow:

- prepare environment
- run migrations
- create the app through `exampleEntrypoint.get(env=...)`
- wrap it with `exampleAPI`
- let buses resolve handlers and repositories inside fresh scopes
- call `register_topics()` before dispatching commands or publishing events

That is the evidence-backed baseline for testing your own app.

## Minimal reading path after this page

1. `README.md`
2. `docs/explanation/architecture-from-example.md`
3. `docs/how-to/bootstrap-sqlalchemy-app.md`
4. `docs/how-to/migrate-to-0.3.0-scoped-execution.md`
5. `docs/how-to/test-use-cases.md`
6. `docs/reference/supported-surface.md`
7. `docs/reference/evidence-map.yaml`

If you want repo-specific guidance after that, run the companion skill in
`skills/python-hexagonal-usage/SKILL.md`.
