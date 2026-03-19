# Skill: python-hexagonal-usage

## Purpose

Use this skill AFTER the user understands the written docs.
This is a companion artifact for adopting `python-hexagonal`, not a magic code
generator and not a substitute for architecture comprehension.

## Source of truth

Anchor every recommendation to these repository artifacts:

- `README.md`
- `docs/getting-started/first-app.md`
- `docs/explanation/architecture-from-example.md`
- `docs/how-to/bootstrap-sqlalchemy-app.md`
- `docs/how-to/test-use-cases.md`
- `docs/reference/supported-surface.md`
- `docs/reference/evidence-map.yaml`
- `skills/python-hexagonal-usage/reference/evidence-map.yaml`

If your recommendation cannot be traced back to those docs plus evidence from
`src/example` and `src/tests/use_cases`, do not present it as supported.

## Workflow

1. Inspect the target repository without modifying files by default.
2. Detect Python project markers such as `pyproject.toml`, `src/`, package
   folders, and tests.
3. Map the repo to these concepts when evidence exists:
   - domain
   - application
   - ports
   - adapters
   - entrypoints
   - tests
4. Report confidence for each match as `high`, `medium`, or `low`.
5. Compare the repo against the documented adoption path.
6. Warn when the repo appears to depend on internals or undocumented adapter
   details, and suggest `hexagonal.integrations.sqlalchemy` when the repo is
   using the legacy SQLAlchemy adapter path directly.
7. Produce a phased adoption report using `templates/adoption-report.md`.
8. End with structured questions using `templates/question-capture.md`.

## Guardrails

- Do not replace the written docs. Point back to them.
- Treat `hexagonal.integrations.sqlalchemy` as the supported adapter-specific
  SQLAlchemy extension surface.
- Do not invent support for other `hexagonal.adapters.*` paths or internal
  helpers.
- Do not normalize the example's noisy names as if they were required.
- Do not claim certainty when repo structure is ambiguous.
- Do not generate code unless the user explicitly asks for it AFTER analysis.
- If code generation is requested, keep recommendations inside the documented
  surface and call out assumptions.

## Reading order for the user

When the user is new, recommend this order first:

1. `README.md`
2. `docs/getting-started/first-app.md`
3. `docs/explanation/architecture-from-example.md`
4. `docs/how-to/bootstrap-sqlalchemy-app.md`
5. `docs/how-to/test-use-cases.md`
6. `docs/reference/supported-surface.md`

Then tailor advice from the repo scan.

## Output contract

Always return:

- current layer matches
- gaps or ambiguities
- recommended next steps
- boundary warnings
- open questions or friction points

Use the bundled templates so maintainers can compare reports across repos.
