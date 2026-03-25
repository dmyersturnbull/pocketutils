# SPDX-FileCopyrightText: Copyright 2020-2026, Contributors to pocketutils
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/pocketutils
# SPDX-License-Identifier: Apache-2.0
"""
More convenient exception classes for `OSError` and family.
"""
import errno as _errno
import os
from typing import Self
from os import strerror as _errno_to_str


_winerror_map = {
    _errno.ENOENT: 3,  # ERROR_PATH_NOT_FOUND
    _errno.EEXIST: 80,  # ERROR_FILE_EXISTS
    _errno.EIO: 13,  # ERROR_INVALID_DATA (best guess)
    _errno.EISDIR: 183,  # ERROR_ALREADY_EXISTS
    _errno.ENOTDIR: 2,  # ERROR_FILE_NOT_FOUND
    _errno.EACCES: 5,  # ERROR_ACCESS_DENIED
    _errno.ENODEV: 55,  # ERROR_DEV_NOT_EXIST
}


def _errno_to_win(errno: int | None) -> int | None:
    return None if errno is None or os.name != "NT" else _winerror_map.get(errno)


class TypedOSError(OSError):
    def __init__(
        self: Self,
        *,
        errno: int | None = None,
        winerror: int | None = None,
        filename: str | None = None,
        filename2: str | None = None,
    ) -> None:
        if winerror is None:
            winerror = _errno_to_win(errno)
        super().__init__(errno, winerror, _errno_to_str(errno), filename, filename2)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, TypedOSError):
            # Note the subtlety here!
            return type(other) is type(self) and self.args == other.args
        return NotImplemented

    def __hash__(self) -> int:
        return hash((type(self), self.args))


class TypedIOError(OSError):
    def __init__(
        self: Self,
        *,
        filename: str | None = None,
        filename2: str | None = None,
    ) -> None:
        win = 13 if os.name == "NT" else None  # 13 is "invalid data"
        super().__init__(_errno.EIO, win, os.strerror(_errno.EIO), filename, filename2)


class PathMissingError(FileNotFoundError):
    def __init__(
        self: Self,
        *,
        filename: str | None = None,
    ) -> None:
        errno = _errno.ENOENT
        super().__init__(errno, _errno_to_win(errno), _errno_to_str(_errno.ENOENT), filename, None)


class PathExistsError(FileExistsError):
    def __init__(
        self: Self,
        *,
        filename: str | None = None,
    ) -> None:
        errno = _errno.ENOENT
        super().__init__(errno, _errno_to_win(errno), _errno_to_str(errno), filename, None)


class AccessDeniedError(PermissionError):
    def __init__(
        self: Self,
        *,
        filename: str | None = None,
    ) -> None:
        errno = _errno.EACCES
        super().__init__(errno, _errno_to_win(errno), _errno_to_str(errno), filename, None)


class TypedIsADirectoryError(IsADirectoryError):
    def __init__(
        self: Self,
        *,
        filename: str | None = None,
    ) -> None:
        errno = _errno.EISDIR
        super().__init__(errno, _errno_to_win(errno), _errno_to_str(errno), filename, None)


class TypedNotADirectoryError(NotADirectoryError):
    def __init__(
        self: Self,
        *,
        filename: str | None = None,
    ) -> None:
        errno = _errno.ENOTDIR
        super().__init__(errno, _errno_to_win(errno), _errno_to_str(errno), filename, None)


class DeviceMissingError(OSError):
    def __init__(
        self: Self,
        *,
        filename: str | None = None,
    ) -> None:
        errno = _errno.ENODEV
        super().__init__(errno, _errno_to_win(errno), _errno_to_str(errno), filename, None)
