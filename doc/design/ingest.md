# Ingest pipeline

The ingest pipeline takes a payload, classifies it, and persists it as an
immutable item. The orchestrator coordinates the process across service,
repo, and storage layers.

## Pipeline steps

1. Validate payload (exactly one of bytes or file path, non-empty, within size limit)
2. Hash the payload (BLAKE2b-120, Crockford base32)
3. Classify content (format detection via strategy chain)
4. Extract metadata (image dimensions for PicItem)
5. Assemble a WritePlan DTO
6. Deduplicate by content hash (return existing item if found)
7. Resolve a unique shortcode prefix
8. Write bytes to storage (skipped for LinkItem)
9. Insert metadata into DB
10. Return a PersistResult (item + created flag)

## Key interfaces

### WritePlan

Framework-agnostic DTO that passes between inference and persistence. Carries
identity (hash, code length), payload reference (bytes or path), classification
(kind, format), and type-specific metadata (dimensions). Hashing happens before
persistence. Bytes are never modified. The DTO has no ORM or request objects.

### IngestService

Owns steps 1-5. Takes raw payload and hints (filename, declared MIME,
requested format), returns a WritePlan. Has no access to DB, HTTP, or
filesystem writes.

### IngestOrchestrator

Owns coordination across service, repo, and storage. Single entry point
for the web layer. Handles dedupe checks, delegates persistence, and
manages rollback if storage fails after a DB write.

### PersistResult

Simple DTO: the created item and a boolean indicating whether it was newly
created or deduplicated.

## Design decisions

- Orchestrator owns coordination. Repo and storage are siblings, not a chain.
- Dedupe happens at the orchestrator level before any writes.
- Storage writes before DB insert. Orphan files are easier to clean up than
  orphan rows.
- LinkItem payload is the URL as bytes. The repo decodes it for storage.
  The orchestrator skips file storage for links.

## Classification

Content is classified through a strategy chain with priority:
requested_format > declared_mime > magic bytes > filename > URL pattern > text

Classification is data-driven. Format mappings in the model layer are
the source of truth. The classifier delegates to isolated helpers for
each strategy. URL detection validates scheme, domain, and path separately.
Text fallback requires valid UTF-8 with no banned control characters.

The API accepts format overrides via `?format=` query param or
`X-Depo-Format` header. Query param takes precedence.

## Related docs

- [Architecture](./architecture.md) - layering and coordination model
- [Items](./items.md) - what the pipeline produces
- [Module reference: service/](../module/service.md) - implementation details
- [Module reference: model/](../module/model.md) - WritePlan, enums, format mappings
