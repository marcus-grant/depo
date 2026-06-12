# src/depo/model/user.py
"""
Domain model for user identity.
Defines the User dataclass representing an authenticated system user.
Pure, frozen dataclass. No I/O or framework dependencies.
Author: Marcus Grant
Created: 2026-06-11
License: Apache-2.0
"""

from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class User:
    """Authenticated system user."""

    id: int
    email: str
    name: str
    pw_hash: str
    created_at: int
