# Claude Development Instructions

This file contains instructions and guidelines for Claude when working on the Depo codebase.

## Important Reminders

- Do what has been asked; nothing more, nothing less
- NEVER create files unless they're absolutely necessary for achieving your goal
- ALWAYS prefer editing an existing file to creating a new one
- NEVER proactively create documentation files (*.md) or README files unless explicitly requested

## Development Guidelines

### Commit Message Format
- Title: Maximum 50 characters including prefix
- Body: Maximum 72 characters per line
- Body text should use '-' bullets with proper nesting
- Use prefixes:
  - `Tst:` for test-related changes
  - `Fix:` for bug fixes
  - `Ft:` for new features
  - `Ref:` for refactoring
  - `Doc:` for documentation
  - `Pln:` for planning/TODO updates
- No signature block - do not include emoji, links, or Co-Authored-By lines

### Testing Requirements
- ALWAYS run tests before suggesting a commit
- Follow E2E + TDD approach:
  - E2E tests find larger missing or broken pieces
  - TDD fills or fixes those pieces incrementally
- TDD/E2E workflow:
  - Build tests singularly first
  - Ensure test fails as expected (red)
  - Implement change to make test pass (green)
  - Consider refactors for better solution (refactor)
  - Move to next test when complete
- Task management:
  - Each test typically corresponds to a TODO task
  - Some tasks require multiple tests
  - After test(s) pass and refactors complete: update TODO.md, git commit
- Implement in small steps with clear logical breaks:
  - Add one test case or feature at a time
  - Test immediately after each testable addition
  - Never write massive amounts of code without testing

### Code Style
- Follow existing patterns in the codebase
- Check neighboring files for conventions
- Never assume a library is available - verify in package.json/requirements
- Don't add comments unless explicitly asked
- Match indentation and formatting of existing code
- Follow PEP 8 and typical Python conventions:
  - No trailing whitespace
  - Blank line at end of file
  - Two blank lines between top-level definitions
  - One blank line between method definitions
  - Spaces around operators and after commas
  - No unnecessary blank lines within functions
  - Maximum line length of 88 characters (Black/Ruff default)

### Project-Specific Instructions
- This is a Django file-sharing application called "Depo"
- Supports web uploads, API uploads, deduplication, and various content types
- Current focus areas are tracked in TODO.md
- Keep TODO.md updated:
  - Update "Current Tasks" section when starting/stopping work
  - Mark completed items with [x]
  - Add new tasks as they're discovered
  - Document progress for easy resumption

### Function Refactoring Procedure

When extracting business logic from views to utilities (established pattern):

1. **Analyze function part-by-part** - identify each responsibility
2. **Find existing integration tests** that cover the logic being extracted
3. **Create utility function stub** with `pass` (red-green-refactor approach)
4. **TDD approach**: Write failing unit test → implement → green → next test
5. **Update calling code** to use new utility function
6. **Add integration test** to verify new utility is called correctly with right parameters
7. **Run full test suite** to ensure nothing breaks
8. **Update TODO.md** and **commit frequently** (small, focused commits)

**Key patterns established:**
- Boolean validators: `file_empty()`, `file_too_big()`
- Keep existing integration tests as safety net  
- Unit tests focus on utility functions in isolation
- Integration tests verify the wiring works
- Mock where functions are used, not where defined
- Mock parameter order matches decorator order (bottom-to-top)