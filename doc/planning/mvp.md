# MVP Plan

Tracks remaining work to reach a shippable MVP. Completed work lives in
reference docs under `doc/design/` and `doc/module/`.

## Quick reminders

These are settled. Full detail lives in the linked reference docs.

**Layering** ([architecture](../design/architecture.md)):
Dependencies flow inward: web -> service -> repo -> storage -> model -> util.
No business logic in routes. No framework objects below orchestration.
Services write, selectors read.

**Items** ([items](../design/items.md)):
Immutable, content-addressed. Primary key is `hash_full` (24-char BLAKE2b,
Crockford base32). `code` is a unique prefix (8-24 chars). `kind` discriminates
into TextItem, PicItem, LinkItem.

**Shortcodes** ([shortcodes](../design/shortcodes.md)):
The shortcode is the primary interface. `/{code}` is the canonical URL.
Smart defaults based on request context. `/raw` and `/info` sub-paths
are explicit overrides.

**Ingest pipeline** ([ingest](../design/ingest.md)):
Payload enters, gets hashed, classified, persisted. Orchestrator coordinates
service, repo, and storage. Dedupe by content hash.

## Pre-MVP work

The cutoff test: does this block deploying a real instance with real data?
Everything that does not is in [v0.2](./v02.md).

Ordered by dependency. Each heading is one PR. The end of this list is `v0.1`.

### Hash and encode changeover (Branch: `ft/hash-update`)

Replace blake2b integer high-pad with blake3 bitstream low-pad per the
[conformance](../design/conformance.md) contract. Latent-correct today
(depo only encodes on-ladder 120 bits), so no data migration; rewrite
`util/shortcode.py` and its tests.

- [ ] Converge vectors with normpic before merge (cross-repo gate)
Before PR submit:
- [ ] Share findings and converged vectors with the normpic peer

### Logging to file (Branch: `ft/log-file`)

An instance you cannot see is an instance you cannot operate. Logs need to land
in a file that survives, readable over ssh.

Deliberately minimal. The user-facing versus admin-facing message split is a
real problem but not a deployment blocker: `DepoError.ctx` already carries
call-site detail for log handlers, and `AuthRequiredError` already uses it. That
split is v0.2 work.

- [ ] Add a `FileHandler` in `configure_logging`, path from config
- [ ] Config field for the log file path, alongside the existing `log_level`
- [ ] Keep propagation on so test capture still works

### Deploy (Branch: `ft/deploy`)

Minimal deployment tooling. No Ansible, no orchestration: a Dockerfile and a few
scripts. Target environment is a server running nginx and letsencrypt as a
reverse proxy, app in a container.

- [ ] Dockerfile
- [ ] Container lifecycle: SIGTERM handling, WAL checkpoint on shutdown so the
      DB is consistent when the container stops
- [ ] Backup script for the SQLite DB, with retention pruning
- [ ] Update path: run migrations, restart the service
- [ ] Production config:
  - `DEPO_MODE` (`dev`/`prod`) config field
  - `gen-secret` CLI command printing a suitable random session secret
  - `load_config` behaviour per mode: dev auto-generates an ephemeral secret
    with a warning, prod keeps the hard-fail sentinel
  - A `depo.toml` fit for a live instance
- [ ] Deployment and ops doc: required config, WAL journal mode, store directory
      setup

The store is deliberately out of scope for backup here. A separate borgbackup
job from a home NAS covers it.

### Extract the shortcode codec as its own library

The codec is shared with sibling projects; extracting before MVP means
consumers integrate against a library rather than depo's internals, so later
releases are not reshaping a shared dependency after the fact. A Rust port
becomes the default implementation eventually, with the Python one kept as a
cross-reference oracle.

- [ ] Extract `util/shortcode.py`, its vectors, and its conformance suite
- [ ] Import back into depo as a dependency
- [ ] Decide depo's canary tests: the whole conformance suite belongs to the
      library, so depo needs only enough to catch a divergence from the
      contract, not to re-prove it

### Hash-named storage (Branch: `ft/hash-named-store`)

Rung 1 of the ingest redesign ladder. Store payload files under
`{hash_full}.{ext}` instead of `{code}.{ext}`. The code stays a DB-level
alias for the hash, which it conceptually already is. This decouples the
storage write from code resolution (which happens at repo insert), and is
the prerequisite for the durable ordering below. Read path resolves
code -> item -> hash via the repo it already queries.

- [ ] Rename scheme in `FilesystemStorage._path_for`: hash, not code
  - [ ] `put`/`open`/`delete` signatures take `hash_full` + format
  - [ ] Update call sites: orchestrator, `selector.get_raw`
- [ ] One-time migration script renaming existing store files
  - [ ] DB already holds hash + format for every item; walk rows,
        rename `{code}.{ext}` to `{hash_full}.{ext}`

### Durable ingest ordering (Branch: `ft/durable-ingest`)

Rung 2. The guarantee: a returned shortcode is a promise the content is
stored under it (policy deletions excepted). Achieved by sealing the file
before the DB row exists, so no crash interleaving can produce a durable
code without its durable content. Costs three fsyncs per upload: well
under a millisecond on NVMe, low single-digit ms on SATA SSD. Slower IO
servers are a supported target, and per-upload fsync stays acceptable
there; it is sustained aggregate ingress that slower drives bound, not
request latency. In-flight loss stays cheap and acceptable: a client
that never got a 201 knows it failed.

- [ ] `FilesystemStorage.put` seals instead of bare-writing
  - [ ] Write to `{store_root}/.incoming/{random}` (same filesystem
        as the store root so the rename stays atomic; never `/tmp`,
        which is tmpfs and forces a cross-device copy)
  - [ ] `fsync` file, rename to `{hash_full}.{ext}`, `fsync` dir
- [ ] Reorder orchestrator: store file first, then repo insert
  - [ ] Delete-on-storage-failure rollback in `ingest` goes away;
        worst crash case is an orphan hash-named file, never a row
        without its file
- [ ] `PRAGMA synchronous = FULL` in `init_db` (WAL stays)
  - [ ] NORMAL lets recent commits vanish on power loss, which is
        exactly the broken-promise case
- [ ] GC sweep, startup or cron
  - [ ] `.incoming/` files older than N hours: delete (crashed
        mid-stream uploads)
  - [ ] Hash-named files with no matching row and old mtime: delete
        (crash between seal and commit)

### Manual Testing

- Manual route testing with posting collections saved to repo
- Manual testing of browser UI and styling across browsers and devices and pages.

## Explicit exclusions

These are not MVP:

- Aliases
- Editing UI
- Version history
- Groups and moderation
- Object storage origin
- Redis and metadata caching
- Public registration and password recovery
- JSON API responses (plain text + headers for MVP)
