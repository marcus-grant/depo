# Handoff

This document is both a template and a living handoff. Sections marked
[static] stay across all handoffs. Sections marked [per-session]
get replaced each time.

## How to use this document [static]

This handoff is read by a collaborator at the start of each session. The
collaborator has no direct filesystem access. The user shares file
contents by piping shell command output to clipboard with their `cc`
command. The collaborator suggests commands for the user to run, then
works with whatever comes back.

Sections marked [static] persist across all handoffs. Sections marked
[per-session] are rewritten fresh each session.

At session start:

- Read this document in full
- Follow links to planning and reference docs only as needed for the
  current work

Before ending a session:

- Rewrite the per-session sections fresh from current context; do not
  carry forward stale content from a previous handoff
- Carry static sections forward, with any updates made during the session
- Trim completed items from planning docs
- Record deferrals in the appropriate planning doc, not just here
- Present the finished handoff for the user to persist

## Test fixtures and factories [static]

Shared test scaffolding lives in two places. Examine the existing ones
before writing a new test module or fixture; the suite leans on them
heavily and a new test that rolls its own setup instead of reusing them
is almost always wrong.

- Factories in `tests/factories/` build domain objects and wired test
  apps. `make_config` builds a `DepoConfig` under a tmp path;
  `make_client` builds a wired `TestClient`; `make_user` and friends
  build model instances. Keyword overrides replace defaults.
- Fixtures in `tests/fixtures/` provide ready-to-use test dependencies.
  The `t_*` naming marks them: `t_client`, `t_browser`, `t_htmx` for
  the three client flavors, `t_conn`/`t_db`/`t_repo`/`t_store` for the
  storage layers, `t_seeded` for an app pre-loaded with sample items.
- Isolation helpers compose setup: e.g. `_isolate_config_env` clears
  `DEPO_*`, sets a valid session secret, points XDG at tmp, and chdirs.
  Prefer an autouse fixture calling a module-level helper over repeating
  setup per method.

When the shared scaffolding changes, note it in the per-session Layer
status so the next reader knows.

## Conventions [static]

### Working rhythm

- One thing at a time. One question, one decision, one task per exchange.
- Pre-change, await, post-change. The user pastes the current state of
  the code, the collaborator gives edit guidance, the user applies it and
  pastes the result. This rhythm is what keeps the collaborator from
  pre-filling work that is the user's to write.
- Discuss plan changes before executing. Debate freely, but never
  silently expand scope or nest unplanned work without checking in. A
  better path to higher-quality code is welcome; springing it is not.
- Provide a commit message before moving to the next task.
- Don't re-ask for context already provided. Track what's been shared.

### Context economy

- Prefer surgical retrieval over reading whole files. grep for headers or
  symbols, sed the specific range, `git diff` to review changes. Reach for
  cat when the whole file is genuinely needed or it is small enough not to
  matter.
- Verify project layout before specifying file edits or test placements.
  Plan from the tree, not from memory; planning docs can be wrong about
  exact names and paths.

### Architecture

- Dependencies flow inward: web, service, repo, storage, model, util.
  Never outward. `util` importing `model` is the canonical violation;
  util-layer enums live in `util`.
- Route ordering matters in Starlette. Specific routes register first,
  wildcards (`/{code}`) last.

### Style

- ASCII-128 only in all docs and code. No em-dashes, no arrows, no
  emoji, no section symbols.
- Header levels, not bold markers, for structure in docs.

### Testing

- Hardcoded test assertions over dynamic ones, to prevent false positives.
- Examine existing fixtures and factories before writing a new test
  module. See the Test fixtures and factories section.

### Documentation and planning

- Read planning docs as needed for current work, not in full every
  session.
- Deferrals go in the appropriate planning doc, cross-referenced, not
  just in the handoff.
- Completed planning items get trimmed; reference material moves to
  `doc/design/` and `doc/module/`. Planning docs live in `doc/planning/`.
- See [planning README](./README.md) for current priorities.
- New tasks and PRs follow the [Task Planning](./tasks.md) guide: one PR
  per task, four phases (setup and gating test, TDD implementation,
  integration and documentation, PR), descriptively named units, commits
  under 300 lines.

## Commit and PR rules [static]

Commit prefixes by primary work type:

- `Ft:` - features
- `Tst:` - testing work not in service of a feature
- `Doc:` - documentation updates (can exceed 300 LOC rule)
- `Pln:` - planning decisions documented
- `Ref:` - refactoring
- `Fix:` - bug fixes
- `Chr:`- Chore tasks
- `Chk:` - Checkpoints for when work must be preserved and resumed

Commits should usually stay under 300 LOC. If not, the work probably
needs better division. Commit bodies use nested `-` lists with no line
longer than 72 characters.

PRs get a title reflecting the branch name. Branches follow the same
prefix pattern: `ft/core-api-layer`, `tst/client-fixture`,
`doc/design-refs`, etc.

## Stub workflow [static]

This is the core of how we work, and the most violated rule when it goes
wrong. Read it carefully.

### Division of labor

- The user writes all real code: test bodies and implementations.
- The collaborator provides only stubs (signatures, docstrings, spec
  comments) and edit guidance. The collaborator does not write
  implementations or fill test bodies unless the user explicitly asks, or
  the work is pure mechanical busywork the user has delegated.

### The loop

TDD by default, including refactors and fixes. Each unit of work moves
red, green, blue:

- The collaborator provides a stub: the failing test's signature,
  docstring, and spec comments, with a `...` body.
- The user fills the test body and runs it, confirming it fails (red) for
  the expected reason.
- The collaborator confirms the diagnosis (right failure, right cause),
  then provides the implementation stub: signatures and docstrings, no
  body.
- The user writes the implementation and confirms the test passes (green).
- Either party may propose a refactor (blue); the user makes the change,
  tests stay green.

One atomic step per exchange. Confirm the current step before moving to
the next.

### Stub means stub

A stub is signatures plus docstrings plus spec comments, with `...`
bodies. Do not pre-fill implementations. Do not pre-fill dataclass
fields. Provide the real thing only when the user asks, and not one step
earlier. Repeatedly handing the user code they must delete and rewrite is
the single worst way to waste their time.

### Code block conventions

- State a snippet's location in prose before the fence: the file path,
  and the class or function if nested. Never put the path as a comment
  inside the block; the user copies blocks verbatim.
- Exception: a brand-new file starts with its project-root-relative path
  as a literal first-line comment header, since that line is part of the
  file. New modules use this header:

```python
# src/depo/path/to/module.py
"""
Module description.
Author: Marcus Grant
Created: YYYY-MM-DD
License: Apache-2.0
"""
```

- Include imports likely to be needed.
- Delivered code carries no explanatory comments. The only comments
  allowed are spec comments inside test stubs. Rationale and
  edit-framing go in prose outside the block.
- When the user is editing a file themselves, name the exact lines or
  anchors to change and give only the replacement text framed by its
  surrounding lines. Do not hand back a full rewritten block they must
  diff by hand.

### Test stub specifics

- Test modules include a module docstring, imports, and `TestClass`
  stubs.
- Each test class and each test method gets a docstring AND spec
  comments, not one or the other:

```python
class TestSomething:
    """Tests for Something."""
    # should do X when given Y
    # should raise Z when given W
    ...
```

- When updating an existing module, include only the stubs being added.

### Non-Python work (CSS, templates, HTML)

Same stub-first principle. Describe what to add, which selectors or
elements, and where in the file. For CSS, always provide full code
blocks; descriptions cause errors and waste time. For templates,
describe the structure and classes unless explicitly asked for full
markup. The user writes the actual code.

## Improving this document [static]

This handoff is a living process document. At the end of each session,
consider whether workflow friction could be reduced by updating the
static sections. If a mistake keeps recurring, it belongs here as a
convention, not just a mental note. Every improvement compounds for the
next session.

## Orientation [per-session]

Rewrite fresh each session. Capture, concisely:

- Date.
- What just finished: the committed work this session, in commit order,
  each with a one-line description of what it delivered. Name the branch.
- What's in progress: anything uncommitted or mid-stream, and any
  deliberate scope decisions a fresh reader would otherwise re-litigate
  (e.g. a dependency intentionally deferred to a later PR).
- What's next: the immediate next action, the branch it happens on, and a
  link to the relevant planning block in mvp.md.

## Layer status [per-session]

Rewrite fresh each session. A nested list of the architectural layers
touched this session and their state, so a fresh reader sees the blast
radius at a glance.

- One top-level item per layer or area touched (e.g. src/depo/cli,
  tests/cli, doc/module)
  - State: changed / added / unchanged
  - The specific files touched and what changed in them, terse
- Omit untouched layers, unless their unchanged state matters to the
  next step

## Known issues [per-session]

Rewrite fresh each session. Anything broken, fragile, or deferred that
the next session should know before touching the code.

- Active bugs or rough edges, with where they live
- Deferrals made this session, cross-referenced to the planning doc that
  now tracks them
- "None open" is a valid and good state to record
