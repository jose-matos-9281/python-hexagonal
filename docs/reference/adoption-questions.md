# Adoption questions backlog

Use this file to capture repeated friction from real adopters.
If a question shows up more than once, the docs are probably under-explaining
something.

## Open now

- Should other adapters get an explicit public namespace like
  `hexagonal.integrations.sqlalchemy` once we decide they are stable enough to
  support?
- What is the minimal subset of `hexagonal.application` and `hexagonal.domain`
  primitives a first adopter actually needs?
- Which testing patterns beyond `src/tests/use_cases/contacto/` are proven enough
  to document next?

## Capture format

When you add a new question, use this structure:

```md
## Short title
- category: terminology | bootstrap | testing | public-api-boundary | repo-structure | other
- source: skill-run | issue-template | review
- blocker: yes | no
- question: What confused the adopter?
- current-doc-gap: Which page failed them?
- proposed-follow-up: What doc change or experiment should happen next?
```
