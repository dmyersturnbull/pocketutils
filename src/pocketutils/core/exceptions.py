# SPDX-FileCopyrightText: Copyright 2020-2023, Contributors to pocketutils
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/pocketutils
# SPDX-License-Identifier: Apache-2.0
"""
The motivation here is simply that Python lacks some standard exceptions that I consider important.
Projects can/should subclass from these in addition to the normal Python ones.
"""

from __future__ import annotations

import errno as _errno
import os as _os
from typing import Any as _Any
from typing import Self
from typing import Unpack as _Unpack


class InsecureWarning(UserWarning):
    """A warning about an operation that is potentially insecure but is proceeding regardless."""


class RequestIgnoredError(UserWarning):
    """A request or passed argument was ignored."""


class RequestStrangeWarning(UserWarning):
    """A warning about a potential result being wrong because a request was strange."""


class ResultStrangeWarning(UserWarning):
    """A warning about a potential result being wrong."""


class TypedOSError(OSError):
    def __init__(
        self: Self,
        *,
        errno: int | None = None,
        winerror: int | None = None,
        strerror: str | None = None,
        filename: str | None = None,
        filename2: str | None = None,
    ) -> None:
        super().__init__(errno, winerror, strerror, filename, filename2)


class TypedIOError(OSError):
    def __init__(
        self: Self,
        *,
        errno: int | None = _errno.EIO,
        winerror: int | None = None,
        strerror: str | None = _os.strerror(_errno.EIO),
        filename: str | None = None,
        filename2: str | None = None,
    ) -> None:
        super().__init__(errno, winerror, strerror, filename, filename2)


class PathMissingError(FileNotFoundError):
    def __init__(
        self: Self,
        *,
        errno: int | None = _errno.EEXIST,
        winerror: int | None = None,
        strerror: str | None = _os.strerror(_errno.ENOENT),
        filename: str | None = None,
        filename2: str | None = None,
    ) -> None:
        super().__init__(errno, winerror, strerror, filename, filename2)


class PathExistsError(FileExistsError):
    def __init__(
        self: Self,
        *,
        errno: int | None = _errno.EEXIST,
        winerror: int | None = None,
        strerror: str | None = _os.strerror(_errno.EEXIST),
        filename: str | None = None,
        filename2: str | None = None,
    ) -> None:
        super().__init__(errno, winerror, strerror, filename, filename2)


class AccessDeniedError(PermissionError):
    def __init__(
        self: Self,
        *,
        errno: int | None = _errno.EACCES,
        winerror: int | None = None,
        strerror: str | None = _os.strerror(_errno.EACCES),
        filename: str | None = None,
        filename2: str | None = None,
    ) -> None:
        super().__init__(errno, winerror, strerror, filename, filename2)


class TypedIsADirectoryError(IsADirectoryError):
    def __init__(
        self: Self,
        *,
        errno: int | None = _errno.ENOTDIR,
        winerror: int | None = None,
        strerror: str | None = _os.strerror(_errno.ENOTDIR),
        filename: str | None = None,
        filename2: str | None = None,
    ) -> None:
        super().__init__(errno, winerror, strerror, filename, filename2)


class TypedNotADirectoryError(NotADirectoryError):
    def __init__(
        self: Self,
        *,
        errno: int | None = _errno.ENOTDIR,
        winerror: int | None = None,
        strerror: str | None = _os.strerror(_errno.ENOTDIR),
        filename: str | None = None,
        filename2: str | None = None,
    ) -> None:
        super().__init__(errno, winerror, strerror, filename, filename2)


class DeviceMissingError(OSError):
    def __init__(
        self: Self,
        *,
        errno: int | None = _errno.ENODEV,
        winerror: int | None = None,
        strerror: str | None = _os.strerror(_errno.ENODEV),
        filename: str | None = None,
        filename2: str | None = None,
    ) -> None:
        super().__init__(errno, winerror, strerror, filename, filename2)


class Error(Exception):
    """
    Abstract exception with a message.
    """

    def __init__(self: Self, message: str | None = None, **kwargs: _Unpack[str, _Any]) -> None:
        self.message = message
        super().__init__(message, list(kwargs.values()))
        self._args = list(kwargs.values())

    def __str__(self) -> str:
        return repr(self)

    def __repr__(self: Self) -> str:
        args = str(dict(zip(["message"] + self._args, self.args)))[1:-1]
        extras = ", ".join(self.args[len(self._args) + 1 :])
        return self.__class__.__qualname__ + "{" + args + (" (" + extras + ")" if len(extras) > 0 else "") + "}"


class ExpectedError(Error):
    """
    Non-specific exception to short-circuit behavior but meaning 'all ok'.
    Consider subclassing it.
    """


class UserError(Error):
    """An error caused by input from a user of an application."""


class MultipleMatchesError(Error):
    """
    Multiple records match when only 1 was expected.
    Also applies if 0 or 1 records are permitted.
    """


class NoMatchesError(Error):
    """
    No records match when at least 1 was expected.
    """


class AlgorithmError(Error):
    """
    An incompletely understood failure.
    For example, try/except around a complex algorithm and reraise as `AlgorithmError`.
    """


class StateIllegalError(Error):
    """
    A high-level assertion detected an invalid state.
    """


class OperationNotSupportedError(Error):
    """
    Used as a replacement for NotImplementedError, where the method *should not* be implemented.
    This also differs from `NotImplemented` in that is permanent
    and that it should not (usually) be raised in special methods like `__lt__`.
    """


#
# "Security" errors
#


class SecurityError(Error):
    """Security error."""


class AuthenticationError(SecurityError):
    """Authentication error."""


class AuthorizationError(SecurityError):
    """Authorization error."""


#
# "Resource" errors
#


class ResourceError(Error):
    """A problem finding or loading a resource that the application needs."""

    def __init__(
        self: Self,
        message: str | None = None,
        *,
        resource: str | None = None,
        **kwargs: _Unpack[str, _Any],
    ) -> None:
        super().__init__(message, resource=resource, **kwargs)
        self.resource = resource


class ResourceMissingError(ResourceError):
    """Could not find a resource by name (e.g., a config file)."""


class ResourceInvalidError(ResourceError):
    """Resource found but invalid; e.g., error parsing a config file."""


class ResourceIncompleteError(ResourceInvalidError):
    """Data is missing, incomplete, or invalid. More complex than a missing value."""


class ResourceLockedError(ResourceError):
    """A resource was found but is locked (ex a hardware component in use)."""


#
# "Request" errors
#


class RequestError(Error):
    """An error related to an invalid command, function, args, etc."""


class RequestRefusedError(RequestError):
    """
    Refusal to handle a request.
    """


class RequestAmbiguousError(RequestError):
    """Insufficient information was passed to resolve the operation."""


class RequestContradictoryError(RequestError):
    """Contradictory information was passed."""


#
# "Key" errors
#


class KeyReservedError(Error):
    """A key is reserved by the code and cannot be used."""

    def __init__(
        self: Self,
        message: str | None = None,
        *,
        key: str | None = None,
        keys: set[str] | frozenset[str] | None = None,
        **kwargs: _Unpack[str, _Any],
    ) -> None:
        super().__init__(message, key=key, keys=keys, **kwargs)
        self.key = key
        self.keys = keys


class KeyReusedError(Error):
    """One or more keys were specified twice."""

    def __init__(
        self: Self,
        message: str | None = None,
        *,
        key: str | None = None,
        keys: set[str] | frozenset[str] | None = None,
        original_value: _Any = None,
        **kwargs: _Unpack[str, _Any],
    ) -> None:
        super().__init__(message, key=key, keys=keys, original_value=original_value, **kwargs)
        self.key = key
        self.keys = keys
        self.original_value = original_value


#
# "Value" errors
#


class ValueIllegalError(Error):
    """A high-level error about a invalid value."""

    def __init__(
        self: Self,
        message: str | None = None,
        *,
        value: _Any = None,
        values: set[_Any] | frozenset[_Any] | None = None,
        **kwargs: _Unpack[str, _Any],
    ) -> None:
        super().__init__(message, value=value, values=values, **kwargs)
        self.value = value
        self.values = values


class LengthMismatchError(ValueIllegalError):
    """The objects (2 or more) have different lengths."""


class ValueEmptyError(ValueIllegalError):
    """The object has no elements."""


class ValueNullError(ValueIllegalError):
    """A value of None, NaN, or similar was given."""


class ValueNotNumericError(ValueIllegalError):
    """Could not convert one numeric type to another."""


class ValueNotIntegerError(ValueIllegalError):
    """A floating-point number could not be cast to an integer."""


class ValueOutOfRangeError(ValueIllegalError):
    """A numerical value is outside a required range."""

    def __init__(
        self: Self,
        message: str | None = None,
        *,
        value: _Any = None,
        values: set[_Any] | frozenset[_Any] | None = None,
        minimum: _Any = None,
        maximum: _Any = None,
        **kwargs: _Unpack[str, _Any],
    ) -> None:
        super().__init__(message, value=value, values=values, minimum=minimum, maximum=maximum, **kwargs)
        self.value = value
        self.values = values


#
# "Device" errors
#


class DeviceError(Error):
    """Error related to hardware such as a printer."""

    def __init__(
        self: Self,
        message: str | None = None,
        *,
        device: str | None = None,
        **kwargs: _Unpack[str, _Any],
    ) -> None:
        super().__init__(message, device=device, **kwargs)
        self.device = device


class DeviceConnectionFailedError(DeviceError):
    """Found a device but could not connect."""


class DeviceReadFailedError(DeviceError):
    """Failed to read from a device (IOError subclass)."""


class DeviceWriteFailedError(DeviceError):
    """Failed to write to a device (IOError subclass)."""


#
# IO-like errors
#


class NetworkError(Error):
    """
    Couldn't read or write on a network.
    """

    def __init__(
        self: Self,
        message: str | None = None,
        *,
        uri: str | None = None,
        **kwargs: _Unpack[str, _Any],
    ) -> None:
        self.uri = uri
        super().__init__(message, uri=uri, **kwargs)


class DownloadFailedError(NetworkError):
    """Failed to download a file (IOError subclass)."""


class UploadFailedError(NetworkError):
    """Failed to upload a file (IOError subclass)."""


class FilenameSuffixInvalidError(Error):
    """
    A filename extension was not recognized.

    Attributes:
        suffix: The unrecognized suffix
        filename: The bad filename
    """

    def __init__(
        self: Self,
        message: str | None = None,
        *,
        suffix: str | None = None,
        filename: str | None = None,
        **kwargs: _Unpack[str, _Any],
    ) -> None:
        super().__init__(message, suffix=suffix, filename=filename, **kwargs)
        self.message = message
        self.suffix = suffix
        self.filename = filename


class ValueNotUniqueError(Error):
    """
    There is more than 1 unique value.

    Attributes:
        message: Message
        key: The key used for lookup
        values: The set of values
    """

    def __init__(
        self: Self,
        message: str | None = None,
        *,
        key: str | None = None,
        values: set[str] | None = None,
        **kwargs: _Unpack[str, _Any],
    ) -> None:
        super().__init__(message, key=key, values=values, **kwargs)
        self.key = key
        self.values = values


class ReadFailedError(Error):
    """
    Couldn't read from a resource (file, network, database, etc.).

    Arguments:
        message: Message
        filename: The resource path, URI, etc.
    """

    def __init__(
        self: Self,
        message: str | None = None,
        *,
        filename: str | None = None,
        **kwargs: _Unpack[str, _Any],
    ) -> None:
        super().__init__(message, filename=filename, **kwargs)
        self.filename = filename


class WriteFailedError(Error):
    """
    Couldn't write to a resource (file, network, database, etc.).

    Arguments:
        message: Message
        filename: The resource path, URI, etc.
    """

    def __init__(
        self: Self,
        message: str | None = None,
        *,
        filename: str | None = None,
        **kwargs: _Unpack[str, _Any],
    ) -> None:
        super().__init__(message, filename=filename, **kwargs)
        self.filename = filename


class HashFailedError(Error):
    """
    Could not compute a hash or read/write a hash file.

    Attributes:
        message: Message
        filename: The filename
    """

    def __init__(
        self: Self,
        message: str | None = None,
        *,
        filename: str | None = None,
        **kwargs: _Unpack[str, _Any],
    ) -> None:
        super().__init__(message, filename=filename, **kwargs)
        self.filename = filename


class HashIncorrectError(Error):
    """
    The hashes did not validate (expected != actual).

    Attributes:
        filename: The hash filename
        actual: The actual hex-encoded hash
        expected: The expected hex-encoded hash
    """

    def __init__(
        self: Self,
        message: str | None = None,
        *,
        filename: str | None = None,
        actual: str | None = None,
        expected: str | None = None,
        **kwargs: _Unpack[str, _Any],
    ) -> None:
        super().__init__(message, filename=filename, actual=actual, expected=expected, **kwargs)
        self.filename = filename
        self.actual = actual
        self.expected = expected
