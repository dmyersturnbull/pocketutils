# SPDX-FileCopyrightText: Copyright 2020-2023, Contributors to pocketutils
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/pocketutils
# SPDX-License-Identifier: Apache-2.0
from typing import Self

import pytest
from pocketutils.core.iterators import SeqIterator, TieredIterator


class TestIterators:
    def test_seq_iterator(self: Self) -> None:
        seq = SeqIterator([1, 2, 3])
        assert seq.position == 0
        assert seq.remaining == 3
        assert seq.total == len(seq) == 3
        assert seq.remaining == 3
        for i in range(3):
            assert seq.has_next
            # next
            assert next(seq) == i + 1
            assert len(seq) == seq.total == 3
            assert seq.position == i + 1
            assert seq.remaining == 2 - i
        # next
        assert not seq.has_next
        with pytest.raises(StopIteration):
            next(seq)

    def test_tiered_iterator_0(self: Self) -> None:
        it = TieredIterator([])
        assert len(it) == 0
        assert list(it) == []

    def test_tiered_iterator_1_empty(self: Self) -> None:
        it = TieredIterator([[]])
        assert len(it) == 0
        assert list(it) == []

    def test_tiered_iterator_2_empty(self: Self) -> None:
        it = TieredIterator([[], [1]])
        assert len(it) == 0
        assert list(it) == []

    def test_tiered_iterator_1(self: Self) -> None:
        it = TieredIterator([[1, 2, 3]])
        assert len(it) == 3
        assert list(it) == [(1,), (2,), (3,)]

    def test_tiered_iterator_2(self: Self) -> None:
        it = TieredIterator([[1, 2], [5, 6, 7]])
        assert len(it) == 2 * 3
        assert list(it) == [(1, 5), (1, 6), (1, 7), (2, 5), (2, 6), (2, 7)]

    def test_tiered_iterator_3(self: Self) -> None:
        it = TieredIterator([[1, 2], [5], ["a", "b"]])
        assert len(it) == 2 * 1 * 2
        assert list(it) == [(1, 5, "a"), (1, 5, "b"), (2, 5, "a"), (2, 5, "b")]


if __name__ == "__main__":
    pytest.main()
