# Documentation

This is you first stop for better understanding this project.

## How to use this documentation

This directory is the documentation root for the project.

Documentation is organized around topics, and each topic is anchored by a
`README.md` file that serves as both an overview and an index.

To navigate:

- Start at `doc/README.md`
- Read the overview for the topic you are interested in
- Follow links to peer documents or to a subtopic `README.md`
- Repeat as needed

READMEs provide context and structure.
Non-README documents provide detail and authority.

## Documentation linking rules

To keep documentation navigable and predictable, the following rules apply.

A `README.md` file may link to:

- non-README documents in the same directory
- a `README.md` in an immediate subdirectory
- a parent or sibling `README.md` via a relative path

A `README.md` file must not link to:

- a `README.md` more than one directory deeper
- a non-README document outside its own directory

As a result:

- READMEs act as topic overviews and indexes
- deeper detail is reached by hopping through READMEs
- links remain stable as documentation grows

## Planning

Tracks priorities, remaining work, and development workflow.

- [Planning documentation](./planning/README.md)

## Design requirements

The authoritative design specifications live under
the design documentation.

Read these before making implementation decisions:

- [Design documentation](./design/README.md)

## Code organization

Guidance on how application code and tests are structured.

- [Module organization](./module/README.md)

## What this is

At its core, this service is:

- A **pastebin** for text, code, and structured data
- A **short-content host** for images and small files
- A **URL shortener** (explicit, not implicit)
- A foundation for **editable documents with history**, without mutating content

Every upload is **content-addressed**.
If the bytes are the same, the identifier is the same.
Once created, content never changes.

---

## Core ideas

### Immutability by default

All uploaded content is immutable and identified by
a short code derived from its bytes.

- Same content -> same code
- Content is never edited in place
- Old links never break

### Two guarantees

Every item has two canonical views:

- `/{code}/raw`: always returns the exact bytes
- `/{code}/info`: a safe, human-friendly view based on content format

This makes the service predictable for both humans and machines.

### Explicit mutability with aliases

When you *do* want editing or versioning, it's explicit.

Aliases act as named pointers to immutable items:

- Editing creates a new immutable version
- The alias moves forward
- History is preserved

Mutability lives at the alias layer -- not in the content itself.

### Format-driven rendering

Text content is stored as bytes, but classified by a single **format** field:

- `markdown` renders as markdown
- `python`, `json`, `yaml`, etc. are syntax-highlighted
- Dangerous formats like HTML or SVG are never executed in the UI

Raw bytes are always available regardless of format.

---

## Why this exists

Most pastebins and snippet tools optimize for convenience first and correctness later.
This project does the opposite:

- Predictable behavior over clever inference
- Explicit choices over magic
- Clear architectural boundaries
- Designed for self-hosting from day one

It's meant to be small, understandable, and boring in the best possible way.

---

## Intended audience

- Developers who want a reliable pastebin they can trust
- Self-hosters who prefer SQLite and the filesystem
- Small groups, friends, or communities sharing notes and snippets
- Anyone who values stable links and simple infrastructure

---

## Technical overview

- **Backend**: FastAPI
- **Database**: SQLite (first-class)
- **Storage**: Filesystem (object store support planned)
- **Frontend**: Server-rendered HTML with HTMX
- **Auth**: Authenticated uploads, no anonymous posting by default

The architecture is layered so
storage back-ends, caching, and richer features can be added without
changing core behavior.

---

## Philosophy (short version)

- Bytes are truth
- Raw is always available
- Rendering is safe by default
- Mutability is explicit
- Links should last

---
