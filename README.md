# python-hexagonal

`python-hexagonal` is a library for building hexagonal applications in Python.
The real usage story lives in `src/example` and the proof lives in
`src/tests/use_cases`, so this documentation starts there instead of pretending a
two-line snippet is enough.

## Start here

- Install the package: `pip install python-hexagonal`
- Follow the example-backed guide: [`docs/getting-started/first-app.md`](docs/getting-started/first-app.md)
- Understand the architecture roles:
  [`docs/explanation/architecture-from-example.md`](docs/explanation/architecture-from-example.md)
- Bootstrap the adapter-specific SQLAlchemy path:
  [`docs/how-to/bootstrap-sqlalchemy-app.md`](docs/how-to/bootstrap-sqlalchemy-app.md)
- Migrate existing apps to the scoped execution model:
  [`docs/how-to/migrate-to-0.3.0-scoped-execution.md`](docs/how-to/migrate-to-0.3.0-scoped-execution.md)
- Learn the canonical testing workflow:
  [`docs/how-to/test-use-cases.md`](docs/how-to/test-use-cases.md)
- Check the guardrails before copying imports:
  [`docs/reference/supported-surface.md`](docs/reference/supported-surface.md)
- Review the evidence map if you want to verify a claim against code or tests:
  [`docs/reference/evidence-map.yaml`](docs/reference/evidence-map.yaml)

## What you learn from the first path

After the first-app guide you should understand:

- where the domain model lives and why it stays isolated
- how application APIs wrap command, query, and event buses
- how ports describe the infrastructure your app needs
- how entrypoints assemble an app from environment and infrastructure
- how the use-case tests prove the workflow end to end

## The blueprint we actually trust

These files are the baseline for the supported adoption story:

- `src/example/contacto/domain/contacto.py` - aggregate behavior, value-object
  strategy, and query entry points
- `src/example/contacto/application/app.py` - application composition through
  `BusAppGroup`
- `src/example/contacto/ports/drivens.py` - infrastructure contracts and
  repository boundaries
- `src/example/app/application/api.py` - top-level API wrapper consumers call
- `src/example/app/entrypoints/main.py` - environment-driven bootstrap via
  `EntrypointGroup`
- `src/example/app/entrypoints/db/sqlalchemy.py` - SQLAlchemy-specific
  infrastructure assembly
- `src/tests/use_cases/base.py` - canonical test bootstrap with migrations,
  entrypoint creation, and topic registration

## Supported path vs internals

The documented path is intentionally narrow.

- Start from `hexagonal.domain`, `hexagonal.application`,
  `hexagonal.ports.drivens`, `hexagonal.ports.drivers`, and
  `hexagonal.entrypoints`
- Reach for `hexagonal.integrations.sqlalchemy` when you need the reusable
  SQLAlchemy repository and unit-of-work utilities
- Treat scoped execution as the default mental model: shared datastore and
  mapper, fresh write/read scope per operation
- Treat `hexagonal.entrypoints.sqlalchemy` as adapter-specific convenience, not
  the whole framework story
- Do not treat `hexagonal.__init__` as the public integration surface; right now
  it only exposes `hello()`
- Do not cargo-cult example names like `exampleAPI`, `exampleEntrypoint`, or
  `Exampletate`; copy the roles, not the labels
- Do not build new code against `hexagonal.adapters.*`; that path is kept for
  compatibility, while the supported SQLAlchemy extension surface now lives under
  `hexagonal.integrations.sqlalchemy`

## Companion skill

This repo also ships an installable companion skill at
`skills/python-hexagonal-usage/SKILL.md`.
It is there to inspect a user repository, map it to the same architecture, and
point people back to the written docs. It does NOT replace the docs and it does
NOT get to invent new supported APIs.
