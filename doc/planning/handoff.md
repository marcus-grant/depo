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

Date: YYYY-MM-DD

What just finished:

- (1-3 bullet summary of completed work, not a changelog)
- (focus on outcomes, not individual steps)

What's in progress:

- (anything partially done, with enough context to resume)
- (omit if nothing is in progress)

What's next:

- (the next planned task from [mvp.md](./mvp.md) or relevant planning doc)
- (link to the specific section, not just the doc)

## Layer status **[per-session]**

Only list layers that changed this session or have caveats for the
next session. If a layer is stable and untouched, omit it. The goal
is to flag what the next collaborator needs to be careful about.

| Layer | Status | Notes |
|-------|--------|-------|
| (e.g. service/classify) | (changed/broken/stable) | (brief caveat) |

## Known issues **[per-session]**

Bugs or broken states only. Not design decisions or future work — those
are deferrals. Long-lived issues belong in planning docs, not here.

- (issue and how it manifests)

## Test fixtures **[per-session]**

Brief snapshot of what's available.
See [module docs](../module/README.md) for full details.
Brief snapshot of what's available.
Must reflect actual state after this session's changes —
don't copy from previous handoff without verifying.

Factories:

- (list current factory modules and key helpers)

Fixtures:

- (list shared fixtures)

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
- PayloadTooLargeError inherits from ValueError. Catch it before ValueError
  in except chains. **Does this still belong here?**
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

## Conventions **[static]**

- Read planning docs as needed for current work, not in full every session
- Update session learnings during the session, not just at the end
- Deferrals go in planning docs, not just the handoff
- Completed planning items get trimmed and moved to reference docs
- Reference docs live in `doc/design/` and `doc/module/`
- Planning docs live in `doc/planning/`
- See [planning README](./README.md) for current priorities

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
elements, and where in the file — don't provide full code blocks
unless explicitly asked or it's clearly busywork. For CSS, name the
properties and values. For templates, describe the structure and
classes. The user writes the actual code.

### Improving this document **[static]**

This handoff is a living process document.
At the end of each session,
consider whether workflow friction could be reduced by
updating the static sections.
If a mistake keeps recurring,
it belongs here as a convention or learning -
not just a mental note.
Future collaborators benefit from every improvement.
