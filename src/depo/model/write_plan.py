# src/depo/model/write_plan.py
"""
WritePlan DTO for ingest pipeline.

Frozen dataclass representing the handoff between IngestService and Repository.
Contains all info needed to persist an item without framework dependencies.

Author: Marcus Grant
Date: 2026-01-20
License: Apache-2.0
"""

from dataclasses import dataclass
from pathlib import Path

from depo.model.enums import ContentFormat, ItemKind, PayloadKind


@dataclass(frozen=True)
class WritePlan:
    hash_full: str
    code_min_len: int
    payload_kind: PayloadKind
    kind: ItemKind
    size_b: int
    upload_at: int
    format: ContentFormat | None = None
    origin_at: int | None = None
    payload_bytes: bytes | None = None
    payload_path: Path | None = None
    width: int | None = None
    height: int | None = None
    link_url: str | None = None
