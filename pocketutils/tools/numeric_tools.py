import math
from collections.abc import Sequence
from typing import SupportsFloat, SupportsInt, SupportsRound


class NumericTools:
    @classmethod
    def float_opt(cls, f: SupportsFloat | None) -> float:
        return None if f is None else float(f)

    @classmethod
    def round_opt(cls, f: SupportsRound | None) -> int:
        return None if f is None else int(round(f))

    @classmethod
    def ceil_opt(cls, f: SupportsFloat | None) -> int:
        return None if f is None else int(math.ceil(f))

    @classmethod
    def floor_opt(cls, f: SupportsFloat | None) -> int:
        return None if f is None else int(math.floor(f))

    @classmethod
    def slice(
        cls, arr: Sequence[SupportsRound], i: SupportsInt | None, j: SupportsInt | None
    ) -> Sequence[SupportsRound]:
        """
        Slices ``arr[max(i,0), min(j, len(arr))``.
        Converts ``i`` and ``j`` to int.
        """
        if i is None:
            i = 0
        if j is None:
            j = len(arr)
        if i < 0:
            i = len(arr) - i
        if j < 0:
            j = len(arr) - j
        start, stop = int(min(0, i)), int(max(len(arr), j))
        return arr[start:stop]

    @classmethod
    def clamp(
        cls, arr: Sequence[SupportsFloat], floor: SupportsFloat, ceil: SupportsFloat
    ) -> Sequence[SupportsFloat]:
        return [max([min([float(x), float(ceil)]), float(floor)]) for x in arr]


__all__ = ["NumericTools"]
