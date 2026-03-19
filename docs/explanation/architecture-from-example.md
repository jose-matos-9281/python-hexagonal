# Architecture from the example

This page explains the architecture the docs keep pointing at.
The point is not to worship the example names. The point is to understand the
responsibilities each layer owns so you can reproduce the shape in your own
service without coupling yourself to repo-specific noise.

## Outcome

After this page you should be able to explain:

- why the domain stays isolated from infrastructure
- how ports keep application code honest about dependencies
- why application composition happens before entrypoint bootstrap
- where adapters fit without becoming your public API story
- how entrypoints and tests prove the whole flow

## Domain defines behavior and vocabulary

Start with `src/example/contacto/domain/contacto.py`.

That file is where the business language lives:

- `Telefono` and `Email` are domain values
- `EstadoContacto` defines allowed lifecycle states
- `Contacto` owns state transitions through commands such as
  `marcar_contactado()`
- `GetContactoById` keeps query intent explicit instead of leaking repository
  mechanics into callers

That separation matters because the domain should answer business questions
without caring whether persistence is SQLAlchemy, in-memory, or something else.
If you start from the database layer, you already lost the plot.

## Ports define what the application needs

The next stop is the ports layer:

- `src/example/contacto/ports/drivens.py`
- `src/example/contacto/ports/drivers.py`
- `src/example/app/ports/drivens.py`
- `src/example/app/ports/drivers.py`

The drivens describe required collaborators such as repositories and unit of
work. The drivers describe the application-facing contracts.

That gives you two guardrails:

1. infrastructure must satisfy the application contract
2. application code depends on interfaces before concrete adapters exist

This is why the docs keep pushing ports so hard. They are the line between a
hexagonal architecture and a thin service layer glued directly to ORM code.

## Application composition groups use cases behind one app

Read these files together:

- `src/example/contacto/application/app.py`
- `src/example/app/application/app.py`

`ContactoApp` composes focused bus apps for contacto, entidad,
entidad_contacto, and integration handlers, then groups them with
`BusAppGroup`.

`exampleApp` composes that bounded-context application with a top-level
`ComposableBusApp`.

The architectural lesson is simple:

- verify infrastructure first
- compose focused capabilities second
- expose one application object third

Do not confuse this with a requirement to mirror the example folder names.
What matters is the layering and composition sequence.

## API facades keep callers out of bus plumbing

Read:

- `src/example/contacto/application/api.py`
- `src/example/app/application/api.py`

The example uses `BaseAPI` wrappers to expose intentful entry points over the
underlying command, query, and event buses.

That gives consumers a stable place to call use cases, while the application can
still keep bus orchestration internal. In other words: callers ask for business
operations, not transport details.

This is part of the documented surface.
What is NOT part of the public story is every internal bus implementation or
adapter helper the repo happens to use today.

## Adapters implement ports, but they are not your first teaching surface

Read:

- `src/example/app/adapters/drivens/repository/sqlalchemy.py`
- `src/example/app/adapters/drivers/proxy_adapters.py`

Adapters exist to satisfy ports with concrete technology.
The SQLAlchemy infrastructure groups repository implementations and unit-of-work
behavior. The proxy adapter wraps the app in a driver-facing shape.

This is useful evidence, but it is NOT the first thing a new adopter should copy
blindly. The docs keep adapter details behind guardrails because adapters change
faster than architectural roles do.

## Entrypoints assemble the app from environment and infrastructure

Read:

- `src/example/app/entrypoints/main.py`
- `src/example/app/entrypoints/db/sqlalchemy.py`
- `src/example/app/entrypoints/bus/main.py`

This is where the whole graph gets assembled.

- `exampleEntrypoint` selects an infrastructure path from environment
- `Sqlalchemy` chooses the SQLAlchemy app entrypoint
- `SQLAlchemyexampleEntrypoint` builds infrastructure, initializes it, creates
  the app, and returns the driver-facing application
- `BusEntrypointGroupApp` selects the bus transport strategy

This is the real integration surface for the first documented path.
Not `hexagonal.__init__`. Not random adapter internals. Entrypoints.

## Tests are the proof that the architecture actually works

Read:

- `src/tests/use_cases/base.py`
- `src/tests/use_cases/contacto/test_crear_contacto.py`
- `src/tests/use_cases/contacto/test_validar_contacto.py`
- `src/tests/use_cases/contacto/test_marcar_contactado.py`

The tests do three critical things:

1. create environment and infrastructure
2. bootstrap the application through the entrypoint
3. exercise use cases through the API wrapper

That is why this docs set keeps citing the tests. They are not marketing copy.
They are executable evidence for the documented workflow.

## What to copy into your own app

Copy these ideas:

- domain behavior before persistence
- ports before adapters
- application composition before transport-specific entrypoints
- narrow API facades for consumers and tests
- evidence-backed tests that use the same bootstrap path as production

Do NOT copy these things as doctrine:

- example naming like `exampleApp`, `exampleEntrypoint`, or `Exampletate`
- internal adapter helpers as if they were guaranteed public contracts
- package-root imports as your primary integration story

## Keep going

If you want the practical path next, read:

1. `docs/how-to/bootstrap-sqlalchemy-app.md`
2. `docs/how-to/test-use-cases.md`
3. `docs/reference/supported-surface.md`
