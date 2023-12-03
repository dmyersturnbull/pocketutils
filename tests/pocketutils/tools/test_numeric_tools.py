# SPDX-FileCopyrightText: Copyright 2020-2023, Contributors to pocketutils
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/pocketutils
# SPDX-License-Identifier: Apache-2.0
from typing import Self

import numpy as np
import pytest
from pocketutils.tools.numeric_tools import NumericTools


class TestNumericTools:
    def test_slice(self: Self) -> None:
        arr = np.arange(5)
        assert list(NumericTools.slice(arr, 0, 1)) == [0]
        assert list(NumericTools.slice(arr, 2, 4)) == [2, 3]
        assert list(NumericTools.slice(arr, 0, 8)) == list(arr)
        assert list(NumericTools.slice(arr, None, None)) == list(arr)
        # from reverse direction
        assert list(NumericTools.slice(arr, -1, 3)) == []
        assert list(NumericTools.slice(arr, 1, -2)) == [1, 2, 3, 4]

    def test_clamp(self: Self) -> None:
        arr = [-11, -10, 0, 10, 11]
        assert list(NumericTools.clamp(arr, -10, 10)) == [-10, -10, 0, 10, 10]


if __name__ == "__main__":
    pytest.main()
