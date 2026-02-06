# src/depo/repo/errors.py
"""
Repository-specific exceptions.
Author: Marcus Grant
Date: 2026-01-30
License: Apache-2.0
"""


class RepoError(Exception):
    """Base class for repository errors."""


class CodeCollisionError(RepoError):
    """Insert attempted with duplicate code. Indicates application bug."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(f"Code collision: {code}")


class NotFoundError(RepoError):
    """Lookup found no matching item."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(f"Item not found: {code}")
