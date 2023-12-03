# SPDX-FileCopyrightText: Copyright 2020-2023, Contributors to pocketutils
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/pocketutils
# SPDX-License-Identifier: Apache-2.0
"""

"""

import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Self, SupportsFloat, SupportsInt, SupportsRound

__all__ = ["NumericUtils", "NumericTools"]


@dataclass(slots=True, frozen=True)
class NumericUtils:
    def float_opt(self: Self, f: SupportsFloat | None) -> float:
        return None if f is None else float(f)

    def round_opt(self: Self, f: SupportsRound | None) -> int:
        return None if f is None else int(round(f))

    def ceil_opt(self: Self, f: SupportsFloat | None) -> int:
        return None if f is None else int(math.ceil(f))

    def floor_opt(self: Self, f: SupportsFloat | None) -> int:
        return None if f is None else int(math.floor(f))

    def slice(
        self: Self,
        arr: Sequence[SupportsRound],
        i: SupportsInt | None,
        j: SupportsInt | None,
    ) -> Sequence[SupportsRound]:
        """
        Slices `arr[max(i,0), min(j, len(arr))`.
        Converts `i` and `j` to int.
        """
        if i is None:
            i = 0
        if j is None:
            j = len(arr)
        if i < 0:
            i = len(arr) - i
        if j < 0:
            j = len(arr) - j
        start, stop = int(max(0, i)), int(min(len(arr), j))
        return arr[start:stop]

    def clamp(
        self: Self,
        arr: Sequence[SupportsFloat],
        floor: SupportsFloat,
        ceil: SupportsFloat,
    ) -> Sequence[SupportsFloat]:
        return [max([min([float(x), float(ceil)]), float(floor)]) for x in arr]


NumericTools = NumericUtils()
