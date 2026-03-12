# tests/util/test_errors.py
"""
Tests for centralized error types in util/errors.py.
Author: Marcus Grant
Created: 2026-03-10
License: Apache-2.0
"""

from depo.util import errors


class TestDepoError:
    """Tests for the DepoError base class."""

    def test_class_attributes(self):
        """Is an Exception subclass with status 500."""
        assert issubclass(errors.DepoError, Exception)
        assert errors.DepoError.status == 500
        msg_substrs = ["unexpect", "error", "github.com/marcus-grant/depo/issues"]
        assert all(s in errors.DepoError.message.lower() for s in msg_substrs)

    def test_message_and_context(self):
        """Accepts message and context arguments & stores them."""
        e = errors.DepoError("Test message", {"key": "value"})
        assert str(e) == "Test message"
        assert e.ctx == {"key": "value"}


class TestRepoError:
    """Tests for the RepoError domain base."""

    def test_inheritance_and_status(self):
        """Inherits from DepoError and has status 500."""
        assert issubclass(errors.RepoError, errors.DepoError)
        assert errors.RepoError.status == 500


class TestNotFoundError:
    """Tests for NotFoundError (404)."""

    def test_defaults(self):
        """Class-level defaults: inherits RepoError, status 404, resource 'Item'."""
        assert issubclass(errors.NotFoundError, errors.RepoError)
        assert errors.NotFoundError.status == 404
        assert errors.NotFoundError.resource == "Item"

    def test_with_id_and_resource(self):
        """Constructor stores id, resource, status, & context; message reflects them."""
        e = errors.NotFoundError("01234567", "Tag", status=420)
        assert e.status == 420
        assert e.id == "01234567"
        assert e.resource == "Tag"
        assert str(e) == "Tag with ID 01234567 not found."


class TestCodeCollisionError:
    """Tests for CodeCollisionError."""

    def test_defaults(self):
        """Class-level defaults: inherits RepoError, status 409."""
        assert issubclass(errors.CodeCollisionError, errors.RepoError)
        assert errors.CodeCollisionError.status == 409
        assert errors.CodeCollisionError.message == "Code collision error occurred."

    def test_with_code_and_hash(self):
        """Constructor accepts code and hash, message reflects them."""
        e = errors.CodeCollisionError(code="C0DE1234", hash_full="HASH6789", status=420)
        assert str(e) == "Code collision with code C0DE1234 and hash HASH6789."
        assert e.status == 420
        assert e.code == "C0DE1234"
        assert e.hash_full == "HASH6789"


class TestValidationError:
    """Tests for ValidationError domain base (400)."""

    def test_defaults(self):
        assert issubclass(errors.ValidationError, errors.DepoError)
        assert errors.ValidationError.status == 400
        assert errors.ValidationError.message == "Validation error occurred."


class TestPayloadTooLargeError:
    """Tests for PayloadTooLargeError (413)."""

    def test_defaults(self):
        """Class-level defaults: inherits ValidationError, status 413."""
        assert issubclass(errors.PayloadTooLargeError, errors.ValidationError)
        assert errors.PayloadTooLargeError.status == 413
        assert errors.PayloadTooLargeError.message == "Payload size exceeds maximum."

    def test_with_size_and_max_size(self):
        """Constructor accepts size and max_size, message reflects them."""
        e = errors.PayloadTooLargeError(2048, 1024, status=420)
        assert str(e) == "Payload of 2048 bytes exceeds max size of 1024 bytes."
        assert e.status == 420

    def test_with_limit_kind(self):
        """Optional kind appears in message."""
        e = errors.PayloadTooLargeError(11, 4, kind="URL")
        assert "11" in str(e)
        assert "4" in str(e)
        assert "url" in str(e).lower()


class TestPayloadEmptyError:
    """Tests for PayloadEmptyError (400)."""

    def test_defaults(self):
        assert issubclass(errors.PayloadEmptyError, errors.ValidationError)
        assert errors.PayloadEmptyError.status == 400
        assert errors.PayloadEmptyError.message == "Payload is empty."


class TestPayloadSourceError:
    """Tests for PayloadSourceError (400)."""

    def test_defaults(self):
        """Inherits ValidationError, status 400, default message."""
        assert issubclass(errors.PayloadSourceError, errors.ValidationError)
        assert errors.PayloadSourceError.status == 400
        assert errors.PayloadSourceError.message == "Provided invalid payload sources."

    def test_with_sources(self):
        """Stores sources list and generates message from it."""
        e = errors.PayloadSourceError(sources=["payload_bytes", "payload_path"])
        assert e.sources == ["payload_bytes", "payload_path"]
        assert "payload_bytes" in str(e)
        assert "payload_path" in str(e)
        assert "one of" in str(e).lower()
