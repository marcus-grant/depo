# src/depo/util/errors.py
"""
Central error types for depo.
Author: Marcus Grant
Created: 2026-03-10
License: Apache-2.0
"""

from enum import IntEnum
from typing import Literal

# Severity Enum used in errors


class Severity(IntEnum):
    """Logging severity levels for errors."""

    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50


# == Base ==


class DepoError(Exception):
    """Root exception for all depo errors."""

    severity: Severity = Severity.ERROR
    status = 500
    message = "Unexpected error occurred, report to https://github.com/marcus-grant/depo/issues"
    exception: Exception | None = None

    def __init__(
        self,
        message: str | None = None,
        context: dict | None = None,
        status: int | None = None,
    ):
        self.message = message or self.__class__.message
        super().__init__(self.message)
        self.status = status if status is not None else self.__class__.status
        self.ctx = context


# == Server Domain ==


class ServerError(DepoError):
    """Base for server-side errors."""

    status = 500
    message = "An internal server error occurred."

    def __init__(
        self,
        message: str | None = None,
        context: dict | None = None,
        status: int | None = None,
    ):
        super().__init__(message, context, status)


class UnknownServerError(ServerError):
    """Unknown/unexpected server error, likely a bug."""

    message = "Unknown server error, likely a bug. Please report."

    def __init__(self, exception: Exception | None = None, context: dict | None = None):
        cls_msg = self.__class__.message
        msg = f"{cls_msg}: {exception}" if exception else cls_msg
        super().__init__(msg, context)
        self.exception = exception


class MissingDependencyError(ServerError):
    """A required dependency is missing or not installed."""

    severity = Severity.WARNING
    status = 501
    message = "A required dependency is missing or not installed."

    def __init__(self, dependency: str | None = None, context: dict | None = None):
        cls_msg = self.__class__.message
        msg = f"Missing required dependency '{dependency}'." if dependency else cls_msg
        super().__init__(msg, context)
        self.dependency = dependency


# == Repo Domain ==


class RepoError(DepoError):
    """Base for repository errors."""

    severity = Severity.WARNING
    message = "Repository error occurred."


class NotFoundError(RepoError):
    """Repo Domain error for not found resources."""

    severity = Severity.INFO
    status = 404
    resource = "Item"

    def __init__(
        self,
        id: str,
        resource: str | None = None,
        status: int | None = None,
        context: dict | None = None,
    ):
        message = f"{resource or self.resource} with ID {id} not found."
        super().__init__(message, context, status or self.status)
        self.id = id
        self.resource = resource or self.resource


class CodeCollisionError(RepoError):
    """Repo Domain error for code collisions."""

    status = 409
    message = "Code collision error occurred."

    def __init__(
        self,
        code: str | None = None,
        hash_full: str | None = None,
        status: int | None = None,
        context: dict | None = None,
    ):
        parts = []
        if code:
            parts.append(f"code {code}")
        if hash_full:
            parts.append(f"hash {hash_full}")
        if len(parts) == 2:
            with_fragment = f" with {parts[0]} and {parts[1]}"
        elif parts:
            with_fragment = f" with {parts[0]}"
        else:
            with_fragment = ""
        message = f"Code collision{with_fragment}." if parts else self.__class__.message
        super().__init__(message, context, status or self.status)
        self.code = code
        self.hash_full = hash_full


# == Validation Domain ==


class ValidationError(DepoError):
    """Base for validation errors."""

    severity = Severity.INFO
    status = 400
    message = "Validation error occurred."


class PayloadTooLargeError(ValidationError):
    """Validation domain error for payloads being too large."""

    status = 413
    message = "Payload size exceeds maximum."

    def __init__(
        self,
        size: int,
        max_size: int,
        kind: Literal["Payload", "URL"] = "Payload",
        status: int | None = None,
        context: dict | None = None,
    ):
        message = f"{kind} of {size} bytes exceeds max size of {max_size} bytes."
        super().__init__(message, context, status or self.status)
        self.size = size
        self.max_size = max_size
        self.kind = kind


class PayloadEmptyError(ValidationError):
    """Validation domain error for empty payloads."""

    status = 400
    message = "Payload is empty."


class PayloadSourceError(ValidationError):
    """Validation domain error for invalid payload sources."""

    status = 400
    message = "Provided invalid payload sources."

    def __init__(
        self,
        sources: list[str] | None = None,
        status: int | None = None,
        context: dict | None = None,
    ):
        message = self.__class__.message
        if sources:
            message = "these sources: " + ", ".join(sources)
            message = f"Provided invalid sources, must provide one of {message}."
        super().__init__(message, context, status or self.status)
        self.sources = sources


# == Classification Domain ==


class ClassificationError(DepoError):
    """Base for classification errors."""

    severity = Severity.INFO
    status = 422
    message = "Error, content could not be classified to a supported format."


class UnknownClassificationError(ClassificationError):
    """Unknown/unexpected error in classification pipeline. Indicates a bug."""

    severity = Severity.ERROR
    status = 500
    message = "Unknown classification error, likely a bug in the pipeline."

    def __init__(self, exception: Exception | None = None, context: dict | None = None):
        msg = self.__class__.message
        if exception is not None:
            msg = f"{self.__class__.message} Error: {exception}"
        super().__init__(msg, context)
        self.exception = exception


class ImageDecodeError(ClassificationError):
    """Validation domain error for image decoding failures."""

    message = "Error while decoding image content."


class UnsupportedFormatError(ClassificationError):
    """Validation domain error for unsupported content formats."""

    message = "Classified/Requested format is unsupported by Depo."

    def __init__(self, format: str | None, context: dict | None = None):
        message = self.__class__.message
        if format:
            message = f"Format '{format}' is unsupported by Depo."
        super().__init__(message or self.__class__.message, context)
        self.format = format


# == Shortcode Domain ==
class ExtensionMismatchError(NotFoundError):
    """Raised when the extension in an extensioned URL does not match
    the item's format. The extension is a contract; mismatches are 404."""

    message = "Extension does not match item format."

    def __init__(self, code: str, expected: str, got: str, context: dict | None = None):
        message = f"Expected .{expected} for {code}, got .{got}."
        DepoError.__init__(self, message, context)
        self.code = code
        self.expected = expected
        self.got = got


class LinkRawNotSupportedError(NotFoundError):
    """Raised when raw content is requested for a LinkItem.
    Links have no payload; raw requests are 404."""

    message = "Links do not have raw content."

    def __init__(self, code: str, context: dict | None = None):
        message = f"Item {code} is a link and has no raw content."
        DepoError.__init__(self, message, context)
        self.code = code
