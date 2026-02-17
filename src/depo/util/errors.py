# src/depo/util/errors.py
"""
Central error types for depo.
Author: Marcus Grant
Created: 2026-02-12
License: Apache-2.0
"""


class PayloadTooLargeError(ValueError):
    """Payload exceeds maximum allowed size."""

    pass
