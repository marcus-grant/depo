# src/depo/repo/errors.py
"""
Tests for repository-specific exceptions.
Author: Marcus Grant
Date: 2026-01-30
License: Apache-2.0
"""

from depo.repo.errors import CodeCollisionError, RepoError


class TestCollisionError:
    """Tests for CodeCollisionError exception."""

    def test_attributes(self):
        """Test that attributes are set correctly."""
        error = CodeCollisionError("DUPLICATE_CODE")
        assert error.code == "DUPLICATE_CODE"

    def test_inheritance(self):
        """Test that CodeCollisionError inherits from RepoError."""
        assert isinstance(CodeCollisionError("DUPLICATE_CODE"), RepoError)

    # stores code attribute correctly
    # inherits from RepoError
