# tests/util/test_b3c32_smoke.py
"""
Smoke checks against the pinned b3c32 dependency.
Author: Marcus Grant
Date: 2026-08-02
License: Apache-2.0
"""

import pytest
from b3c32 import UncertifiedWidthError, hash_b32, verify_conformance


class TestB3c32Smoke:
    """The pinned b3c32 still honors the contract depo consumes.

    A red here means check the pin before anything else. Contract-level
    claims are certified upstream in b3c32's own suite; this module only
    proves depo's installed copy is the certified surface.
    """

    def test_verify_conformance(self) -> None:
        """The library's own smoke set passes in depo's environment."""
        verify_conformance()

    def test_width_gate_survives(self) -> None:
        """Uncertified widths still raise, so the gate outlived the pin."""
        with pytest.raises(UncertifiedWidthError):
            hash_b32(b"", 42)

