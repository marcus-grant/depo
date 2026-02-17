# Shortcodes

The shortcode is the primary user-facing identifier for content. Every item
gets a unique shortcode derived from its content hash.

## Hashing

- Algorithm: BLAKE2b
- Digest size: 120 bits (15 bytes)
- Encoding: Crockford base32
- Canonical output: uppercase
- Full encoded hash length: 24 characters

## Storage model

- `hash_full` - the complete 24-char hash, used as primary identity in the DB
- `code` - a unique prefix (8-24 chars), assigned at creation time
- `hash_remainder` - the rest of the hash after the code prefix

## Collision handling

Codes start at a configurable minimum length (default 8). If a new item's
prefix collides with an existing item that has different content, the prefix
extends one character at a time (9, 10, ..., up to the full 24). The DB
stores the resolved canonical code.

Uploading identical content is not a collision. It is deduplicated and
returns the existing item.

## Canonicalization

Input is normalized before lookup:

- `o` and `O` become `0`
- `i`, `I`, `l`, `L` become `1`
- Lowercased input is uppercased

The DB stores canonical uppercase only. Ambiguous input from users is
accepted and silently corrected (Postel's Law).

## Related docs

- [Architecture](./architecture.md) - system layering
- [Items](./items.md) - domain model using shortcodes as identity
- [Module reference: util/](../module/util.md) - shortcode implementation
