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

- [ ] Rewrite hasher: blake2b to unkeyed blake3, 120-bit on the 40-bit ladder
- [ ] Rewrite encoder: integer high-pad to bitstream low-pad Crockford
- [ ] Implement the conformance assertion classes as the test suite
- [ ] Derive depo's frozen vectors independently from the external oracles
- [ ] Converge vectors with normpic before merge (cross-repo gate)
Before PR submit:
- [ ] Verify every process step in the shared plan was walked
- [ ] Update `conformance.md` with anything found during implementation
- [ ] Update `shortcodes.md` Hashing and Canonicalization to match shipped code
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
