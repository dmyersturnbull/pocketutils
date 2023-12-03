# SPDX-FileCopyrightText: Copyright 2020-2023, Contributors to pocketutils
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/pocketutils
# SPDX-License-Identifier: Apache-2.0
from typing import Self

import pytest
from pocketutils.core.chars import Chars


class TestChars:
    def test_range(self: Self) -> None:
        assert Chars.range(1, 2) == "1-2"  # en dash

    def test_shelled(self: Self) -> None:
        assert Chars.shelled("xyz") == "(xyz)"


if __name__ == "__main__":
    pytest.main()
