# Test use cases from the example

This guide explains the test strategy the docs can actually defend.
The baseline is `src/tests/use_cases`, because those tests exercise the same
entrypoint-driven bootstrap used by the example app.

## Outcome

After this page you should be able to explain:

- why test setup starts from entrypoints instead of internal constructors
- what the shared test bootstrap prepares before each suite runs
- how API wrappers keep test calls intention-revealing
- what kinds of behavior the current use-case tests actually prove

## The shared test bootstrap

Read `src/tests/use_cases/base.py` first.

The sequence in `BaseTest.setup_class()` is the important part:

1. create environment values for the test database
2. clear topic cache
3. run Alembic migrations
4. build the app with `exampleEntrypoint.get(env=...)`
5. wrap the app with `exampleAPI`
6. call `register_topics()` before dispatching commands or events

That setup matters because it proves the documented architecture works through a
real bootstrap path, not through a fake unit-test shortcut.

## Why entrypoint-based test setup matters

If your tests instantiate repositories, buses, or handlers directly while
production uses entrypoints and grouped infrastructure, you are testing a
different system.

The example avoids that trap.
It boots through the entrypoint first and only then exercises use cases through
the API facade.

That gives you confidence in:

- environment wiring
- infrastructure initialization
- bus registration
- application composition
- API surface used by callers

## How individual use-case suites are structured

Read these files:

- `src/tests/use_cases/contacto/test_crear_contacto.py`
- `src/tests/use_cases/contacto/test_validar_contacto.py`
- `src/tests/use_cases/contacto/test_marcar_contactado.py`

The suite pattern is consistent:

- derive from `BaseTest`
- select the API slice needed for the use case in `setup_class()`
- prepare GIVEN state through public API calls
- execute the use case through commands or published events
- assert emitted events and resulting state

That is a good hexagonal test shape because the test talks in business intent,
not repository implementation details.

## What the current tests prove

The contacto tests currently prove these documented behaviors:

- create a contacto and recover it through queries
- validate a contacto into allowed states
- emit and observe integration-driven state changes such as
  `EntidadContactoCorresponde`

They also prove some wiring assumptions indirectly:

- topics must be registered before event-driven flows work
- migrations are part of usable infrastructure setup
- the SQLAlchemy-backed path is the exercised adapter-specific baseline today

## What the tests do NOT prove

Do not overclaim.
These tests do NOT automatically prove:

- every internal helper is public API
- every adapter implementation behaves the same way
- every possible extension point is stable for consumers

That is why the docs keep a supported-surface page and an evidence map.
Without those guardrails, people start reverse-engineering internals from tests
and then act surprised when maintenance becomes a quilombo.

## Minimal suite shape you can copy

Conceptually, a new use-case suite should look like this:

```python
from tests.use_cases.base import BaseTest


class TestYourUseCase(BaseTest):
    temp_db = __file__.replace(".py", ".db")

    @classmethod
    def setup_class(cls):
        super().setup_class()
        cls.api = cls.api_wrapper.your_context.your_api

    def test_happy_path(self):
        response = self.api.do_something(...)
        event = response.get(self.api.Events.SOMETHING_HAPPENED.value)
        assert event is not None
```

Again: copy the test shape, not the example identifiers.

## Practical guardrails

- keep test setup aligned with the documented production bootstrap path
- assert behavior through the API wrapper before reaching for internals
- use emitted events plus resulting state as your proof points
- call out adapter-specific assumptions when the test relies on them

## Next reading

1. `docs/how-to/bootstrap-sqlalchemy-app.md`
2. `docs/reference/supported-surface.md`
3. `docs/reference/evidence-map.yaml`
