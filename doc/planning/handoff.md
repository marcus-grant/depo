# Handoff

This document is both a template and a living handoff. Sections marked
**[static]** stay across all handoffs. Sections marked **[per-session]**
get replaced each time.

## How to use this document **[static]**

This handoff is read by a collaborator at the start of a session.
The collaborator does not have direct access to the project filesystem.
The user shares file contents by running shell commands and piping
output to clipboard with their `cc` command.
The collaborator's role is to suggest commands for the user to run,
then work with whatever they paste back.

Sections marked **[static]** persist across all handoffs. Sections marked
**[per-session]** get replaced each time.

At session start:

- Read this document in full
- Follow links to planning and reference docs only as needed
  for the current work

During the session:

- Stubs, snippets, and instructions over full implementations
- One task at a time, one question at a time
- Provide `cc`-piped commands to gather context, don't ask
  the user to paste. Combine into single commands where possible.
  grep/sed over cat — never cat whole files unless small and
  fully needed
- Verify project layout with a command before specifying file edits
  or test placements. Plan from the tree, not from memory
- Track tasks, deferrals, and doc items as they arise
- Commit messages in code fences, never mixed with other content

Before ending a session:

- Write per-session sections fresh from current session context.
  Don't carry forward stale content from previous handoffs
- Copy static sections verbatim, with any updates made during
  the session
- Trim completed items from planning docs, move to reference docs
- Document deferrals in the appropriate planning doc with
  cross-references
- Add new session learnings
- Present the completed handoff for the user to copy and persist

## Orientation **[per-session]**

Date: 2026-05-29

What just finished:

- Planned the error-logging work end to end. Errors carry a self-describing
  `severity` (new `Severity` IntEnum, set per domain base with leaf
  overrides). The three builders in `web/error.py` are the single logging
  seam through a `_log` helper. An app-level exception handler backstops
  unexpected non-DepoError exceptions.
- Split it into two PRs, both written as task blocks in mvp.md: Error
  logging foundation (`ft/error-logging`, additive expected-error logging)
  and Unexpected-error boundary (`ref/error-boundary`, the handler plus
  `htmx_error` normalization and `hx_upload` thinning).
- Added the Task Planning guide (`doc/planning/tasks.md`), linked from the
  planning README and referenced in this handoff.

What's in progress:

- Nothing. Planning only, no source changed.

What's next:

- Execute Error logging foundation (`ft/error-logging`) in [mvp.md](./mvp.md),
  then Unexpected-error boundary (`ref/error-boundary`).
- Loose end: the non-logging items that left the old "Error handling
  (deferred)" section need a home. `StorageError` and `FormatMismatchError`
  fit existing unplanned.md sections; the logging observability follow-up
  (request IDs, middleware, JSON formatting), validation extraction, the
  LinkItem format gap, MIME review, and bug-report UX read as v0.2. Place
  against v0.2.md next session.

## Layer status **[per-session]**

| Layer | Status | Notes |
|-------|--------|-------|
| doc/planning | changed | mvp.md PR 1/PR 2 blocks replace the old deferred checklist; new tasks.md; README and handoff link tasks.md |
| source | unchanged | planning only, no code written this session |

## Known issues **[per-session]**

- None open. The previous `hx_upload` silent-swallow is now tracked as
  planned work: PR 1's builder logging closes the swallow, PR 2 removes the
  bare except.

## Test fixtures **[per-session]**

Verified against the tree this session.

Factories (`tests/factories/`): `__init__.py`, `db.py`, `models.py`,
`payloads.py`. `make_client` builds the wired TestClient.

Fixtures (`tests/fixtures/__init__.py`):

- `t_conn`, `t_db`, `t_repo`, `t_store`, `t_orch_env`
- `t_client` bare TestClient, empty db and store
- `t_browser` same with `Accept: text/html`
- `t_htmx` same with `HX-Request: true`
- `t_seeded` `SeededApp` bundling `.client`/`.browser`/`.htmx` and one
  `.txt`/`.pic`/`.link` item each

No fixture changes this session. PR 2 will add a
`raise_server_exceptions=False` client fixture to observe the boundary
handler's response.

## Session learnings **[static, cumulative]**

Add new learnings as they come up during a session.
Do not remove old ones.
If a learning becomes a formal convention,
note where it's documented and keep the entry here as a reminder.

- Always run `uv run ruff check` before pytest. Use `uv run` for all
  project python commands.
- Always discuss plan changes before executing. Debate freely but never
  silently expand scope without checking in.
- One thing at a time. Present one question, one decision, one task.
- Don't modify files the user is actively editing. Provide snippets instead.
- Stubs and guidance, not implementations. Provide file stubs with signatures,
  docstrings, and test specs. Only generate full implementations when
  explicitly asked or when it's clearly busywork.
- Always provide a commit message before moving on to the next task.
- Route ordering matters in FastAPI. Specific routes register first,
  wildcards last.
- Hardcoded test assertions over dynamic ones to prevent false positives.
- Test stubs must include module docstring, imports, and spec comments.
- Don't re-ask for context already provided in conversation. Track what's been shared.
- Pico styles `footer` element directly. Use compound selector
  (e.g. `footer.site-footer`) to beat its specificity.
- SVG data URI dither patterns need `background-size` scaling
  for high-DPI. 1px bits are sub-pixel on retina screens.
- Shadow `z-index: -1` pseudo-elements fall behind page background
  unless an ancestor (not the parent) establishes a stacking context.
- System mono font stacks are sufficient for retro aesthetic —
  visual identity comes from structural choices, not typeface.
- Replacing static asset stubs may require users to clear browser
  cache. Note in release docs.
- Catch DepoError broadly in route handlers — covers all typed exceptions
  via inheritance. Domain base classes need passthrough constructors or
  subclasses must call DepoError.**init** directly.
- `DepoError.message` is a class attribute default; set `self.message`
  in `__init__` for instance messages to work correctly.
- BS4 class checks use `find("tag", class_="name")` pattern;
  `get("class")` returns list or None, never crash on missing class.
- Pico styles `article` as a card. Prefer `section` for record
  inspection views.
- Em-dashes are forbidden in all docs and code comments.
- Verify project layout with `cc`/bash before specifying file edits or
  test placements. Plan from the tree, not from memory.
- `util` cannot import `model`. Util-layer enums such as error `Severity`
  live in `util`, not `model/enums.py`.
- `caplog` is not yet used in the suite. Log-capture tests need
  `caplog.set_level(...)` and the `depo` logger to propagate.
- Testing an app-level exception handler needs
  `TestClient(raise_server_exceptions=False)`. The default re-raises.
- Errors self-describe with a `severity` member, the builders are the single
  logging seam, and an app-level handler backstops non-DepoError exceptions.

## Conventions **[static]**

- Read planning docs as needed for current work, not in full every session
- Update session learnings during the session, not just at the end
- Deferrals go in planning docs, not just the handoff
- Completed planning items get trimmed and moved to reference docs
- Reference docs live in `doc/design/` and `doc/module/`
- Planning docs live in `doc/planning/`
- See [planning README](./README.md) for current priorities
- New tasks and PRs follow the [Task Planning](./tasks.md) guide: one PR per
  task, four phases (setup and gating test, TDD implementation, integration
  and documentation, PR), descriptively named units, commits under 300 lines

### Commit and PR rules

Commit prefixes by primary work type:

- `Ft:` - features
- `Tst:` - testing work not in service of a feature
- `Doc:` - documentation updates (can exceed 300 LOC rule)
- `Pln:` - planning decisions documented
- `Ref:` - refactoring
- `Fix:` - bug fixes

Commits should usually stay under 300 LOC. If not, the work probably
needs better division. Commit bodies use nested `-` lists with no line
longer than 72 characters.

PRs get a title reflecting the branch name. Branches follow the same
prefix pattern: `ft/core-api-layer`, `tst/client-fixture`,
`doc/design-refs`, etc.

### Stub workflow

We work by providing stubs, not full implementations.
TDD by default whenever possible, including refactors and fixes.

New modules get this header:

```python
# src/depo/path/to/module.py
"""
Module description.
Author: Marcus Grant
Created: YYYY-MM-DD
License: Apache-2.0
"""
```

Include imports likely to be needed.

Test modules include `TestClass` stubs with a docstring, spec comments
describing what to test, and `...` as the body:

```python
class TestSomething:
    """Tests for Something."""
    # should do X when given Y
    # should raise Z when given W
    ...
```

Implementation modules include class, function, and method signatures
with docstrings but no implementation unless explicitly asked.

When updating an existing module, only include the stubs being added.

### Non-Python work (CSS, templates, HTML)

Same stub-first principle. Describe what to add, which selectors or
elements, and where in the file. For CSS, always provide full code
blocks — descriptions cause errors and waste time. For templates,
describe the structure and classes unless explicitly asked for full
markup. The user writes the actual code.

### Improving this document **[static]**

This handoff is a living process document.
At the end of each session,
consider whether workflow friction could be reduced by
updating the static sections.
If a mistake keeps recurring,
it belongs here as a convention or learning -
not just a mental note.
Future collaborators benefit from every improvement.
