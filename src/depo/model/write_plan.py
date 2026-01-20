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

from depo.model.enums import ItemKind, PayloadKind


@dataclass(frozen=True)
class WritePlan:
    hash_full: str
    code_min_len: int
    payload_kind: PayloadKind
    kind: ItemKind
    mime: str
    size_b: int
    upload_at: int
    origin_at: int | None = None
    payload_bytes: bytes | None = None
    payload_path: Path | None = None
    text_format: str | None = None
    link_url: str | None = None
    pic_format: str | None = None
    pic_width: int | None = None
    pic_height: int | None = None
