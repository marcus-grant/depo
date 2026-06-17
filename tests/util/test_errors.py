# tests/util/test_errors.py
"""
Tests for centralized error types in util/errors.py.
Author: Marcus Grant
Created: 2026-03-10
Revised: [2026-06-16]
License: Apache-2.0
"""

from depo.util import errors


class TestSeverity:
    """Tests for the Severity IntEnum."""

    def test_levels_match_stdlib(self):
        """Severity members map to stdlib logging level ints."""
        assert errors.Severity.DEBUG == 10
        assert errors.Severity.INFO == 20
        assert errors.Severity.WARNING == 30
        assert errors.Severity.ERROR == 40
        assert errors.Severity.CRITICAL == 50


class TestErrorSeverity:
    """Severity resolution across the concrete error hierarchy (gap test)."""

    EXPECTED = {
        errors.ConfigError: errors.Severity.CRITICAL,
        errors.ServerError: errors.Severity.ERROR,
        errors.UnknownServerError: errors.Severity.ERROR,
        errors.MissingDependencyError: errors.Severity.WARNING,
        errors.RepoError: errors.Severity.WARNING,
        errors.NotFoundError: errors.Severity.INFO,
        errors.InsertFailedError: errors.Severity.ERROR,
        errors.UniqueViolationError: errors.Severity.WARNING,
        errors.ExtensionMismatchError: errors.Severity.INFO,
        errors.LinkRawNotSupportedError: errors.Severity.INFO,
        errors.CodeCollisionError: errors.Severity.WARNING,
        errors.ValidationError: errors.Severity.INFO,
        errors.PayloadTooLargeError: errors.Severity.INFO,
        errors.PayloadEmptyError: errors.Severity.INFO,
        errors.PayloadSourceError: errors.Severity.INFO,
        errors.ClassificationError: errors.Severity.INFO,
        errors.UnknownClassificationError: errors.Severity.ERROR,
        errors.ImageDecodeError: errors.Severity.INFO,
        errors.UnsupportedFormatError: errors.Severity.INFO,
    }

    def test_each_subclass_resolves_expected_severity(self):
        """Each concrete subclass resolves to its expected severity."""
        for cls, expected in self.EXPECTED.items():
            msg = f"{cls.__name__}: severity {cls.severity!r}, expected {expected!r}"
            assert cls.severity == expected, msg

    def test_every_subclass_has_a_severity_decision(self):
        """Discovered subclasses match EXPECTED, so new ones force a decision."""

        def descendants(cls):
            subs = set(cls.__subclasses__())
            return subs.union(*(descendants(s) for s in subs))

        assert descendants(errors.DepoError) == set(self.EXPECTED)


# == Base DepoError ==


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

    def test_severity_and_exception_defaults(self):
        """DepoError defaults severity to ERROR and exception to None."""
        assert errors.DepoError.severity == errors.Severity.ERROR
        assert errors.DepoError.exception is None


# == Preflight Domain ==


class TestConfigError:
    """Tests for ConfigError."""

    def _default_err(self):
        """Alias helper for default test ConfigError instance."""
        return errors.ConfigError("key", "value", "expect", {"foo": "bar"})

    def test_is_depo_error(self) -> None:
        """ConfigError is a DepoError subclass."""
        assert isinstance(self._default_err(), errors.DepoError)

    def test_severity_is_critical(self) -> None:
        """ConfigError reports CRITICAL severity."""
        assert self._default_err().severity == errors.Severity.CRITICAL

    def test_status_inherits_500(self) -> None:
        """ConfigError carries the inherited, inert 500 status."""
        assert self._default_err().status == 500

    def test_stashes_key_and_value(self) -> None:
        """The offending key and value are kept on the instance."""
        assert errors.ConfigError("log_level", "BANANA").key == "log_level"
        assert errors.ConfigError("log_level", "BANANA").value == "BANANA"

    def test_message_names_key_and_value(self) -> None:
        """With no expected set, the message names just key and value."""
        msg = errors.ConfigError("log_level", "BANANA").message
        assert msg == "Invalid config for 'log_level': 'BANANA'."

    def test_message_lists_expected(self) -> None:
        """Given expected values, the message appends them."""
        assert (
            errors.ConfigError("log_level", "BANANA", ["DEBUG", "WARNING"]).message
            == "Invalid config for 'log_level': 'BANANA'. Expected: DEBUG, WARNING."
        )


# == Server Domain ==


class TestServerError:
    """Tests for ServerError domain base (500)."""

    def test_defaults(self):
        err = errors.ServerError
        assert issubclass(err, errors.DepoError)
        assert err.status == 500
        assert "server" in err.message.lower() or "error" in err.message.lower()


class TestUnknownServerError:
    """Tests for UnknownServerError (500)."""

    def test_defaults(self):
        err = errors.UnknownServerError
        assert issubclass(err, errors.ServerError)
        assert err.status == 500
        for s in ["unknown", "server", "bug"]:
            assert s in err.message.lower(), f"Expected '{s}' in message"

    def test_with_exception(self):
        """Accepts exception as first positional arg, includes it in message."""
        err = RuntimeError("disk full")
        e = errors.UnknownServerError(err)
        assert e.status == 500
        assert "disk full" in str(e)
        assert e.exception is err


# == Repo Domain ==


class TestMissingDependencyError:
    """Tests for MissingDependencyError (501)."""

    def test_defaults(self):
        err = errors.MissingDependencyError
        assert issubclass(err, errors.ServerError)
        assert err.status == 501
        for s in ["depend", "missing", "install"]:
            assert s in err.message.lower(), f"Expected '{s}' in message"

    def test_with_dependency(self):
        e = errors.MissingDependencyError(dependency="Pillow")
        assert e.dependency == "Pillow"
        assert "Pillow" in str(e)
        assert e.status == 501


class TestRepoError:
    """Tests for the RepoError domain base."""

    def test_inheritance_and_status(self):
        """Inherits from DepoError and has status 500."""
        assert issubclass(errors.RepoError, errors.DepoError)
        assert errors.RepoError.status == 500


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


class TestInsertFailedError:
    """Tests for InsertFailedError."""

    def test_defaults(self):
        """Inherits RepoError, severity ERROR."""
        assert issubclass(errors.InsertFailedError, errors.RepoError)
        assert errors.InsertFailedError.severity == errors.Severity.ERROR


class TestUniqueViolationError:
    """Tests for UniqueViolationError."""

    def test_defaults(self):
        """Inherits RepoError, severity WARNING."""
        assert issubclass(errors.UniqueViolationError, errors.RepoError)
        assert errors.UniqueViolationError.severity == errors.Severity.WARNING

    def test_with_field_and_value(self):
        """Constructor stores field and value; message reflects them."""
        e = errors.UniqueViolationError(field="email", value="a@b.com")
        assert e.field == "email"
        assert e.value == "a@b.com"
        assert e.domain is None
        assert str(e) == "A record with email 'a@b.com' already exists."

    def test_with_domain(self):
        """Domain is included in message when provided."""
        e = errors.UniqueViolationError(field="email", value="a@b.com", domain="User")
        assert e.domain == "User"
        assert str(e) == "A User with email 'a@b.com' already exists."


# == Validation Domain ==


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


# == Classification Domain ==


class TestClassificationError:
    """Tests for ClassificationError domain base (422)."""

    def test_defaults(self):
        err = errors.ClassificationError
        assert issubclass(err, errors.DepoError)
        assert err.status == 422
        msg_substrs = ["class", "error", "no", "format", "support"]
        for s in msg_substrs:
            assert s in err.message.lower(), f"Expected '{s}' in message"


class TestUnknownClassificationError:
    """Tests for UnknownClassificationError (422)."""

    def test_defaults(self):
        err = errors.UnknownClassificationError
        assert issubclass(err, errors.ClassificationError)
        assert err.status == 500
        for s in ["unknown", "classif", "bug"]:
            assert s in err.message.lower(), f"Expected '{s}' in message"

    def test_with_exception(self):
        """Accepts exception arg, includes it in message, status 500."""
        err = RuntimeError("pipeline exploded")
        e = errors.UnknownClassificationError(err)
        assert e.status == 500
        assert e.exception is err
        assert "pipeline exploded" in str(e)
        for s in ["unknown", "class", "error", "bug"]:
            assert s in str(e).lower(), f"expected {s} in error message: {str(e)}"


class TestImageDecodeError:
    """Tests for ImageDecodeError (422)."""

    def test_defaults(self):
        err = errors.ImageDecodeError
        assert issubclass(err, errors.ClassificationError)
        assert err.status == 422
        for s in ["error", "decod", "image"]:
            assert s in err.message.lower(), f"Expected '{s}' in message"


class TestUnsupportedFormatError:
    """Tests for UnsupportedFormatError (422)."""

    err = errors.UnsupportedFormatError

    def test_defaults(self):
        """Tests class-level defaults:
        inherits ClassificationError, status 422, message contains key info."""
        assert issubclass(self.err, errors.ClassificationError)
        assert self.err.status == 422
        for s in ["unsupport", "format", "classif", "depo"]:
            assert s in self.err.message.lower(), f"Expected '{s}' in message"

    def test_with_format(self):
        """Tests constructor accepts format and includes it in message."""
        err = self.err(format="ICO")
        assert err.status == 422
        assert err.format == "ICO"
        assert "ICO" in str(err) and "unsupport" in str(err).lower()


# == Shortcode Domain ==


class TestExtensionMismatchError:
    """Tests for ExtensionMismatchError (404)."""

    err = errors.ExtensionMismatchError

    def test_defaults(self):
        """Tests class-level defaults:
        inherits NotFoundError, status 404."""
        assert issubclass(self.err, errors.NotFoundError)
        assert self.err.status == 404

    def test_with_args(self):
        """Tests constructor stores attributes and formats message."""
        err = self.err(code="abc123", expected="txt", got="png")
        assert err.code == "abc123"
        assert err.expected == "txt"
        assert err.got == "png"
        for s in ["abc123", "txt", "png"]:
            assert s in str(err), f"Expected '{s}' in message"


class TestLinkRawNotSupportedError:
    """Tests for LinkRawNotSupportedError (404)."""

    err = errors.LinkRawNotSupportedError

    def test_defaults(self):
        """Tests class-level defaults:
        inherits NotFoundError, status 404."""
        assert issubclass(self.err, errors.NotFoundError)
        assert self.err.status == 404

    def test_with_code(self):
        """Tests constructor stores code and includes it in message."""
        err = self.err(code="abc123")
        assert err.code == "abc123"
        assert "abc123" in str(err)
