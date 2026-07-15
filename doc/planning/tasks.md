# Task Planning

How a unit of work becomes a followable task in mvp.md. The aim is that
following the structure reproduces our workflow without having to recall it.
This doc covers task layout only. The reasoning behind TDD, typing, and
commit hygiene is in process.md. Session execution and the stub-first
workflow are in handoff.md.

## Shape of a task

A task is one PR. It is a heading under Pre-MVP work in mvp.md carrying the
branch name, followed by four phases in order, each a checklist: setup and
gating test, TDD implementation, integration and documentation, PR. The
phase order is the plan. See Error logging foundation in mvp.md for a full
worked example.

## Heading and problem statement

~~~
### Short task name (Branch: `prefix/short-topic`)

*Problem: one or two sentences on what is broken or missing and the shape of
the fix. Name anything out of scope and which follow-up owns it.*
~~~

Branch prefix matches the commit prefix (`ft`, `ref`, `fix`, `tst`, `doc`,
`pln`). The topic is short and hyphenated.

## Setup and gating test

Branch, then one skipped integration test that asserts the end state, marked
`@pytest.mark.skip("...")`. It stays red until the last unit lands, keeping
the suite green throughout. Run `uv run ruff check && uv run pytest`, then
commit with a `Tst:` prefix.

The gating test is the contract for the whole task. The TDD units below fill
in what it needs.

## TDD implementation

One bold-labeled unit per logical step, in dependency order, each naming its
test file:

~~~
**Descriptive unit name** (`tests/path/test_file.py`)
- [ ] Stub or change in `src/depo/path/module.py`
- [ ] Failing unit test for the behavior
- [ ] Minimal implementation to pass
- [ ] `uv run ruff check && uv run pytest`
- [ ] Commit: `Ft: what this unit does`
~~~

Unit names describe the work. Avoid Phase, Step, Cycle, or numbers. Each unit
is one commit under 300 lines.

## Integration and documentation

Remove the skip and verify the gating test passes. Update the affected
reference docs in doc/design or doc/module, kept linked from their README.
Run the checks, commit with a `Doc:` prefix.

## PR

`gh pr create --title "Prefix: task name" --body "..."`.

## Sizing

One PR, usually six to twelve commits, each under 300 lines. If TDD
implementation passes a dozen units, or a unit will not stay small, the task
is too big and should split into dependent tasks. Pre-MVP tasks do not bump
versions; releases live in v02.md, unplanned.md and v1.md.
