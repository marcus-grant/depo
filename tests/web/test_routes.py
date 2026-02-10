# tests/web/test_routes.py
"""
Integration tests for route handlers.

Round-trip tests via TestClient against the FastAPI
application.

Author: Marcus Grant
Created: 2026-02-10
License: Apache-2.0
"""

from depo.util.shortcode import _CROCKFORD32
from tests.factories.web import make_client


class TestUploadText:
    """Tests for text content upload."""

    # Empty payload returns 400
    # Classification failure returns 400 with message


class TestUploadImage:
    """Tests for image content upload."""

    # Multipart image upload returns 201 with short code


class TestUploadLink:
    """Tests for link/URL submission."""

    # Query param url= returns 201 with short code
    # Raw body containing URL is detected as link


class TestUploadShortcuts:
    """Tests for convenience route aliases."""

    # POST /upload works same as /api/upload
    # POST / works same as /api/upload
