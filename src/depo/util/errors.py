# src/depo/util/errors.py
"""
Central error types for depo.
Author: Marcus Grant
Created: 2026-03-10
License: Apache-2.0
"""


# == Base ==


class DepoError(Exception):
    """Root exception for all depo errors."""

    status = 500
    message = "Unexpected error occurred, report to https://github.com/marcus-grant/depo/issues"

    def __init__(
        self, message: str | None = None, context: dict | None = None, status: int = 500
    ):
        if message is None:
            message = "Unexpected error occurred, contact developer."
        super().__init__(message)
        self.status = status
        self.ctx = context


# == Repo Domain ==


class RepoError(DepoError):
    """Base for repository errors."""

    message = "Repository error occurred."

    ...


class NotFoundError(RepoError):
    """Repo Domain error for not found resources."""

    status = 404
    resource = "Item"

    def __init__(
        self,
        id: str,
        resource: str | None,
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


# TODO: Needs to be validationerrror
class PayloadTooLargeError:
    """Payload exceeds maximum allowed size."""

    status = 413

    def __init__(self, *args, **kwargs):
        raise NotImplementedError(
            "PayloadTooLargeError is being reimplemented with ValidationError."
            "This class should not be used."
        )
