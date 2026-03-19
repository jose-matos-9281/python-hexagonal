# Bootstrap a SQLAlchemy app

This guide explains the practical bootstrap path evidenced by the example.
It is intentionally narrow: SQLAlchemy is the documented adapter-specific path
today, not proof that every adapter follows the same convenience API.

The reusable SQLAlchemy extension utilities now live under
`hexagonal.integrations.sqlalchemy`. That is the public adapter-specific
namespace. The legacy `hexagonal.adapters.drivens.repository.sqlalchemy` path is
kept for compatibility, not as the preferred import target.

## When to use this guide

Use this when you already understand the layer responsibilities and want to wire
your first app with the same shape as `src/example`.

If you do NOT understand domain, ports, and entrypoints yet, go back to:

1. `docs/getting-started/first-app.md`
2. `docs/explanation/architecture-from-example.md`

## The bootstrap chain

The example composes the app in this order:

1. entrypoint group selects infrastructure from environment
2. SQLAlchemy entrypoint builds mapper and connection manager
3. infrastructure object groups repositories and unit of work
4. application object composes bounded-context bus apps
5. proxy adapter returns the driver-facing app contract

The evidence is in:

- `src/example/app/entrypoints/main.py`
- `src/example/app/entrypoints/db/sqlalchemy.py`
- `src/example/app/adapters/drivens/repository/sqlalchemy.py`
- `src/example/app/application/app.py`

## Step 1: define the infrastructure your app needs

Your application ports should describe collaborators before SQLAlchemy enters the
conversation.

The example does that in:

- `src/example/contacto/ports/drivens.py`
- `src/example/app/ports/drivens.py`

That means your bootstrap code can assemble concrete infrastructure later
without rewriting application logic.

## Step 2: compose SQLAlchemy-backed infrastructure

The SQLAlchemy-specific infrastructure lives in
`src/example/app/adapters/drivens/repository/sqlalchemy.py`.

The important pattern is:

- accept a mapper and connection manager
- create a unit of work
- build the infrastructure needed by the bounded context
- group those pieces into one object that satisfies the application ports

Conceptually the shape looks like this:

```python
from hexagonal.application import InfrastructureGroup
from hexagonal.integrations.sqlalchemy import SQLAlchemyUnitOfWork


class YourSQLAlchemyInfrastructure(InfrastructureGroup):
    def __init__(self, mapper, manager):
        self._uow = SQLAlchemyUnitOfWork(connection_manager=manager)
        self._context = YourContextInfrastructure(manager, mapper, self._uow)
        super().__init__(self._context & self._uow)
```

Copy the role separation, not the example class names.

## Step 3: create the application from infrastructure

The example app creation happens in two layers:

- `src/example/contacto/application/app.py` builds the bounded-context app
- `src/example/app/application/app.py` builds the top-level app

The bootstrap rule is boring on purpose:

1. infrastructure verifies itself
2. each focused app is created with the dependencies it needs
3. one top-level app groups the result

If your bootstrap needs ten conditionals and half a framework container before
you can instantiate a use case, you are building a mess, not architecture.

## Step 4: expose the app through an entrypoint

The example entrypoint pair is:

- `src/example/app/entrypoints/main.py`
- `src/example/app/entrypoints/db/sqlalchemy.py`

`exampleEntrypoint` is an `EntrypointGroup` that chooses the infrastructure
variant from `ENV_REPOSITORY`.

`SQLAlchemyexampleEntrypoint` then:

- constructs environment values
- gets SQLAlchemy primitives from `SQLAlchemyInfrastructureEntrypoint`
- builds the grouped infrastructure
- initializes it
- creates the app
- wraps it with `exampleAppProxyAdapter`

Conceptually the pattern looks like this:

```python
from hexagonal.entrypoints import Entrypoint, EntrypointGroup
from hexagonal.entrypoints.sqlalchemy import (
    SQLAlchemyAppEntrypoint,
    SQLAlchemyInfrastructureEntrypoint,
)


class YourInfrastructureEntrypoint(Entrypoint[object]):
    @classmethod
    def get(cls, env=None):
        env = cls.construct_env(env)
        sqlalchemy_infra = SQLAlchemyInfrastructureEntrypoint.get(env)
        infrastructure = YourSQLAlchemyInfrastructure(
            sqlalchemy_infra.mapper,
            sqlalchemy_infra.connection_manager,
        )
        infrastructure.initialize(env)
        return YourAppProxyAdapter(YourApp(infrastructure))


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

## Step 5: keep the guardrails explicit

Do this:

- import from `hexagonal.entrypoints` for the general entrypoint model
- import reusable SQLAlchemy infrastructure helpers from
  `hexagonal.integrations.sqlalchemy`
- treat `hexagonal.entrypoints.sqlalchemy` as an adapter-specific path
- keep adapter details behind your own entrypoint boundary

Do NOT do this:

- teach your team that `hexagonal.adapters.*` is the official first stop for new
  integration code
- expose internal SQLAlchemy helpers directly to the rest of your codebase
- pretend the package root is the integration entrypoint

The supported boundary is documented in `docs/reference/supported-surface.md`.

## Step 6: verify bootstrap through the same path tests use

The example tests do NOT instantiate random internals directly.
They call `exampleEntrypoint.get(env=...)` in `src/tests/use_cases/base.py`.

That is the pattern to keep.
If production bootstraps one way and tests bypass it entirely, your test story is
lying to you.

## Next reading

1. `docs/how-to/test-use-cases.md`
2. `docs/reference/supported-surface.md`
3. `docs/reference/evidence-map.yaml`
