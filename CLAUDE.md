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

### Testing Requirements
- ALWAYS run tests before suggesting a commit
- When implementing new features, write tests incrementally
- Run tests after each significant change
- Use the E2E test approach: implement → test → verify → continue

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