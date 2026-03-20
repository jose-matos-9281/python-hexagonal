# Supported surface

This page is the guardrail.
If you skip it, you will confuse evidence of how the example works today with a
supported integration contract. That is how people create their own pain.

## Tiers

### Documented

These modules are part of the documented first-adoption path:

- `hexagonal.domain`
- `hexagonal.application`
- `hexagonal.ports.drivens`
- `hexagonal.ports.drivers`
- `hexagonal.entrypoints`

Why: the example and tests use these concepts directly to express domain
behavior, app composition, port contracts, and environment-driven bootstrap.

### Adapter-specific

- `hexagonal.integrations.sqlalchemy`
- `hexagonal.entrypoints.sqlalchemy`

Why: the example uses SQLAlchemy entrypoints for a concrete infrastructure path,
and the reusable repository/unit-of-work helpers are now promoted behind an
explicit public namespace. Treat both as SQLAlchemy-only integration surfaces,
not as the whole architecture.

## Scoped execution rule

Starting in `0.3.0`, the supported execution model is:

- share datastore, mapper, and provider/factory objects
- create a fresh write scope per command/event dispatch
- create a fresh read scope per query/read operation
- treat long-lived `uow` or repository instances as compatibility shims, not as
  the preferred integration pattern

If your app wiring still captures repositories or a mutable `uow` at bootstrap
time, you are fighting the supported model.

### Internal or evidence-only

- `hexagonal.__init__`
- `hexagonal.adapters.*`
- `src/example/**`
- helper details like `clear_infrastructure_cache`

Why: these are useful for understanding the current implementation, but they are
not the stable story we want adopters depending on by default.
For SQLAlchemy specifically, prefer `hexagonal.integrations.sqlalchemy` instead
of the legacy adapter package path.

## Rules for docs and examples

- Public docs should teach from documented modules first.
- Public docs may cite adapter-specific modules only when the adapter is labeled
  clearly.
- Public docs may cite internal or example-only files as evidence, NEVER as a
  blanket support promise.
- If a recommendation requires `hexagonal.adapters.*`, the docs or skill must
  call out the coupling risk explicitly unless it is pointing users to the new
  `hexagonal.integrations.sqlalchemy` namespace instead.
- If a user repo already depends on evidence-only modules, the companion skill
  should warn before normalizing that pattern.

## Evidence for this boundary

- `src/hexagonal/domain/__init__.py` - broad domain primitives collected into a
  coherent surface
- `src/hexagonal/application/__init__.py` - application composition and API
  primitives used by the example
- `src/hexagonal/ports/drivens/__init__.py` - repository and infrastructure
  contracts
- `src/hexagonal/ports/drivers/__init__.py` - application-facing contracts
- `src/hexagonal/entrypoints/__init__.py` - base entrypoint contracts
- `src/hexagonal/integrations/sqlalchemy.py` - public SQLAlchemy extension
  surface for repository and unit-of-work utilities
- `src/hexagonal/entrypoints/sqlalchemy.py` - SQLAlchemy bootstrap path and
  cache helper
- `src/hexagonal/__init__.py` - evidence that the package root is NOT the real
  integration story
