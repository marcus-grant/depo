# tests/util/test_validate.py
"""
Tests for util/validate.py input validation functions.

Author: Marcus Grant
Date: 2026-01-20
License: Apache-2.0
"""

from pathlib import Path

import pytest

from depo.util.validate import validate_payload, validate_size


class TestValidatePyaload:
    """Tests depo.util.validate.validate_payload function"""

    def test_raises_if_args_none(self):
        """Raises ValueError if both payload_{bytes,path} are None"""
        with pytest.raises(ValueError):
            validate_payload(None, None)

    def test_raises_if_both_not_none(self):
        """Raises ValueError if both args are provided (not None)"""
        with pytest.raises(ValueError):
            validate_payload(b"Hello, World!", Path("/"))

    def test_none_if_only_bytes(self):
        """Runs successfully if only payload_bytes provided"""
        assert validate_payload(b"Hello, World!", None) is None

    def test_none_if_only_path(self):
        """Runs successfully if only payload_path provided"""
        assert validate_payload(None, Path("/")) is None


class TestValidateSize:
    """Tests depo.util.validate_payload_size function"""

    def test_raises_if_size_gt_max(self):
        """Raises ValueError if size > max_size"""
        with pytest.raises(ValueError):
            validate_size(513, 512)

    def test_raises_if_size_le_zero(self):
        """Raises ValueError if size <= 0"""
        size_max_32bit = (2**32) - 1
        with pytest.raises(ValueError):
            validate_size(-1, size_max_32bit)
        with pytest.raises(ValueError):
            validate_size(0, size_max_32bit)

    def test_none_if_size_eq_max(self):
        """Returns None if size == max_size (boundary)"""
        assert validate_size(4096, 4096) is None

    def test_none_if_size_lt_max(self):
        """Returns None if size < max_size"""
        assert validate_size(1, 4096) is None
