# Design Patterns

Recurring patterns and learnings from depo development.

## Data-Driven Classification

Complex classification behavior built from simple data structures.

### Pattern: Enum as Source of Truth

```python
class ContentFormat(StrEnum):
    PLAINTEXT = "txt"
    PNG = "png"
    # ...
```

The enum value *is* the canonical extension.
MIME types, kinds, and variants derive from it.

### Pattern: Declarative Mappings

```python
_FORMAT_TO_MIME: dict[ContentFormat, str] = {
    ContentFormat.PLAINTEXT: "text/plain",
    ContentFormat.PNG: "image/png",
}
```

Thin lookup functions over declarative dicts.
Adding a format means adding data, not logic.

### Pattern: Accept Variants, Output Canonical (Postel's Law)

```python
# Outbound: always canonical
def mime_for_format(fmt: ContentFormat) -> str:
    return _FORMAT_TO_MIME[fmt]

# Inbound: accept variants
_MIME_TO_FORMAT["application/x-yaml"] = ContentFormat.YAML
_EXT_TO_FORMAT["jpeg"] = ContentFormat.JPEG
```

### Pattern: Strategy Chain with `or`

```python
result = (
    _from_requested_format(requested_format)
    or _from_declared_mime(declared_mime)
    or _from_magic_bytes(data)
    or _from_filename(filename)
)
```

Each strategy returns `ContentClassification | None`.
Priority is explicit in order.
Orchestrator stays thin.

### Pattern: Isolated Detectors

```python
_MAGIC_DETECTORS = [_detect_png_magic, _detect_jpeg_magic, _detect_webp_magic]

def _from_magic_bytes(data: bytes) -> ContentClassification | None:
    for detector in _MAGIC_DETECTORS:
        fmt = detector(data)
        if fmt is not None:
            return ContentClassification(kind_for_format(fmt), fmt)
    return None
```

Each detector handles one format's variants.
Adding format = add detector + append to list.

## Test Patterns

### Pattern: Central Test Specs

```python
_FORMAT_SPECS = [
    (ContentFormat.PLAINTEXT, "text/plain", "txt", ItemKind.TEXT),
    (ContentFormat.PNG, "image/png", "png", ItemKind.PICTURE),
]

_FMT_MIME = [(f, m) for f, m, _, _ in _FORMAT_SPECS]
_FMT_EXT = [(f, e) for f, _, e, _ in _FORMAT_SPECS]
```

One tuple defines all relationships.
Derived lists feed parametrized tests.
Adding format = one row.

### Pattern: Gap Detection Tests

```python
def test_all_formats_have_mime(self):
    for fmt in ContentFormat:
        result = mime_for_format(fmt)
        assert isinstance(result, str)
```

Loops over enum catch missing implementations.
Fails when someone adds a format but forgets the mapping.

### Pattern: Test Helper for Repeated Assertions

```python
def _assert_content_class(result, expected_format, msg_prefix=""):
    assert isinstance(result, ContentClassification)
    assert result.format == expected_format
    assert result.kind == kind_for_format(expected_format)
```

Centralizes multi-field assertions. Reduces boilerplate, improves error messages.

## Principles

- **Data structures are the spec**
  - Mappings define behavior, functions just navigate them.
- **Exhaustive tests over examples**
  - Loop over enums, not cherry-picked cases.
- **Fail at boundaries**
  - Validate input at edges (web layer), trust types internally.
- **Thin orchestrators**
  - Complex behavior emerges from composing simple parts.
