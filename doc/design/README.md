# Design documentation

This directory contains the authoritative design requirements for the project.

Design documents define:

- core invariants
- architectural boundaries
- version-specific scope

These documents are normative. If there is a conflict between
implementation and a design requirement, the design requirement wins.

## Architecture overview

The system is a content-addressed paste/image service. Every upload is
immutable and identified by a hash-derived short code.

### Layers

Dependencies flow inward. Lower layers must not depend on higher layers.

```
web/ → service/ → repo/ → storage/ → model/ → util/
```

- **web/** — HTTP boundary (FastAPI)
- **service/** — orchestration and ingest logic
- **repo/** — persistence, collision resolution
- **storage/** — bytes in, bytes out
- **model/** — domain types, DTOs, enums (no I/O)
- **util/** — hashing, helpers

### Ingest flow

```
POST /upload
     │
     ▼
   web/ (receives bytes, auth)
     │
     ▼
   IngestOrchestrator.ingest()
     ├── IngestService.build_plan()
     │      - hashes content (util/)
     │      - infers kind/format
     │      - returns WritePlan
     ├── Repository.get_by_full_hash()
     │      - dedupe check
     ├── Repository.resolve_code()
     │      - collision handling
     ├── StorageBackend.put()
     │      - writes bytes to filesystem
     └── Repository.insert()
            - writes metadata to DB
     │
     ▼
   PersistResult (item, created)
```

WritePlan is the hard interface between inference and persistence.
IngestOrchestrator coordinates Repository and StorageBackend as siblings.

## Documents

- [Design Requirements — MVP (v0.0.1)](./mvp.md)
  - Authoritative scope and invariants for the initial implementation
  - All MVP work must conform to this document

- [Design Requirements — v1.0](./v1.md)
  - Post-MVP direction and constraints
  - Explains why certain MVP decisions exist
  - Not to be implemented until the MVP is complete
  - This is a future reference not meant to be read till after MVP
    - With the one exception of better understanding architecture in MVP

- [Design Patterns](./patterns.md)
  - Recurring patterns and learnings from development
  - Data-driven classification, test strategies, composition
