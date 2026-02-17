# Items

The item is the core domain object. All content in depo is an item.

## Identity

Every item is immutable and content-addressed.

- `hash_full` - primary key. 24-char BLAKE2b digest in Crockford base32.
- `code` - unique shortcode prefix (8-24 chars) derived from the hash.
  This is the user-facing identifier.
- `kind` - type discriminator pointing to a subtype table.

Items also carry `size_b`, `upload_at`, `uid`, `perm`, and optional `origin_at`.

## Subtypes

### TextItem

Covers notes, scripts, lists, markdown, data formats. The `format` field
(a ContentFormat enum) determines how `/info` renders the content. `/raw`
always returns bytes regardless of format.

Dangerous formats (html, svg) are never rendered, only highlighted.

### PicItem

Images with `format`, `width`, and `height`. MIME is derived from format
at serve time, not stored.

SVG and EXIF support are deferred to post-MVP.

### LinkItem

A URL, stored as metadata only with no payload bytes. Created explicitly
(no implicit URL auto-detection in MVP, though the classification pipeline
will handle this).

`/{code}` redirects to the target URL (302). `/{code}/info` shows link
metadata.

## Immutability

Items are never modified after creation. Content is deduplicated by hash.
Uploading identical content returns the existing item. Mutable references
to items (aliases, tags) are a post-MVP concern.

## Related docs

- [Module reference: model/](../module/model.md) - implementation details,
  field types, enum values
- [Shortcodes](./shortcodes.md) - hashing, encoding, collision handling
- [Ingest](./ingest.md) - how items are created
