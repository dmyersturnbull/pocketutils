# SPDX-FileCopyrightText: Copyright 2020-2023, Contributors to pocketutils
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/pocketutils
# SPDX-License-Identifier: Apache-2.0
"""

"""

from typing import Any, Self


class MockWritable:
    def __init__(self: Self) -> None:
        self.data = None

    def write(self, data: Any) -> int:
        self.data = "write:" + str(data)
        return len(data)

    def flush(self: Self) -> None:
        self.data += "flush"

    def close(self: Self) -> None:
        self.data += "close"


class MockCallable:
    def __init__(self: Self) -> None:
        self.data = None

    def __call__(self, data: Self) -> None:
        self.data = "call:" + data


class WritableCallable(MockWritable, MockCallable):
    pass
