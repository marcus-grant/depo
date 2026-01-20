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
   IngestService.build_plan()
     │  - hashes content (util/)
     │  - infers kind/format
     │  - returns WritePlan
     ▼
   WritePlan (frozen DTO)
     │
     ▼
   Repository.persist()
     │  - resolves collisions
     │  - writes metadata to DB
     ▼
   StorageBackend.put()
        - writes bytes to filesystem
```

WritePlan is the hard interface between inference and persistence.
Neither IngestService nor Repository depend on each other.

## Documents

- [Design Requirements — MVP (v0.0.1)](./mvp.md)
  - Authoritative scope and invariants for the initial implementation
  - All MVP work must conform to this document

- [Architecture Decisions](./architecture.md)
  - Records key decisions and rationale
  - Updated as design evolves

- [Design Requirements — v1.0](./v1.md)
  - Post-MVP direction and constraints
  - Explains why certain MVP decisions exist
  - Not to be implemented until the MVP is complete
  - This is a future reference not meant to be read till after MVP
    - With the one exception of better understanding architecture in MVP
