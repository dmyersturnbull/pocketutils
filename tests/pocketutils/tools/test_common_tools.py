# SPDX-FileCopyrightText: Copyright 2020-2023, Contributors to pocketutils
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/pocketutils
# SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass
from typing import Any, Self

import numpy as np
import pytest
from pocketutils.core.exceptions import MultipleMatchesError, NoMatchesError
from pocketutils.core.mocks import MockCallable, MockWritable, WritableCallable
from pocketutils.tools.common_tools import CommonTools


@dataclass(frozen=True, slots=True)
class Mammal:
    species: Any


outside_lambda_1 = lambda: True
outside_lambda_2 = lambda x: x


def non_lambda():
    pass


class TestCommon:
    def test_only(self: Self) -> None:
        only = CommonTools.only
        with pytest.raises(TypeError):
            # noinspection PyTypeChecker
            only(1)
        assert only("a") == "a"
        assert only(["a"]) == "a"
        assert only({"ab"}) == "ab"
        with pytest.raises(MultipleMatchesError):
            only(["a", "b"])
        with pytest.raises(NoMatchesError):
            only([])

    def test_look(self: Self) -> None:
        f = CommonTools.look
        with pytest.raises(TypeError):
            # noinspection PyTypeChecker
            f(1, 1)
        assert f(Mammal("cat"), "species") == "cat"
        assert f(Mammal("cat"), "owner") is None
        # assert f(Mammal(Mammal('cat')), 'species') == Mammal('cat')
        assert f(Mammal(Mammal("cat")), "species.species") == "cat"
        assert str(f(Mammal(Mammal("cat")), "species")) == "Mammal(species='cat')"
        assert f(Mammal(Mammal("cat")), lambda m: m.species.species) == "cat"

    def test_get_log_function(self: Self) -> None:
        from pocketutils.core import logger

        f = CommonTools.get_log_fn
        assert f("INFO") == logger.info
        assert f("WARNING") == logger.warning
        assert f(30) == logger.warning
        w = MockWritable()
        f(w)("testing")
        assert w.data == "write:testing"
        w = MockCallable()
        f(w)("testing")
        assert w.data == "call:testing"
        w = WritableCallable()
        f(w)("testing")
        assert w.data == "call:testing"

    def test_iterator_has_elements(self: Self):
        f = CommonTools.iterator_has_elements
        assert not f(iter([]))
        assert f(iter([1]))
        with pytest.raises(TypeError):
            # noinspection PyTypeChecker
            f(None)
        with pytest.raises(TypeError):
            # noinspection PyTypeChecker
            f([1])

    def test_is_null(self: Self):
        is_null = CommonTools.is_null
        assert not is_null("a")
        assert not is_null([])
        assert not is_null("None")
        assert not is_null([])
        assert is_null(None)
        assert not is_null("")
        assert not is_null(0.0)
        assert not is_null(np.inf)
        assert is_null(np.nan)

    def test_is_empty(self: Self):
        f = CommonTools.is_empty
        assert not f("a")
        assert f([])
        assert not f("None")
        assert f(None)
        assert f("")
        assert f([])
        assert f({})
        assert f(())
        assert not f((5,))
        assert not f(0.0)
        assert not f(np.inf)
        assert f(np.nan)

    def test_is_probable_null(self: Self):
        f = CommonTools.is_probable_null
        assert f(None)
        assert not f(0)
        assert f("nan")
        assert f("none")
        assert f("NoNe")
        assert f(np.NaN)
        assert not f(np.Inf)

    def test_unique(self: Self):
        f = CommonTools.unique
        assert f([1, 1, 2, 1, 3, 2]) == [1, 2, 3]
        assert f([]) == []
        with pytest.raises(TypeError):
            # noinspection PyTypeChecker
            f(None)

    def test_first(self: Self):
        f = CommonTools.first
        assert f([2, 1]) == 2
        assert f([Mammal("cat"), Mammal("dog"), Mammal("cat")]) == Mammal("cat")
        assert f("21") == "2"
        assert f([]) is None
        with pytest.raises(TypeError):
            # noinspection PyTypeChecker
            f(None)

    def test_multidict(self: Self):
        f = CommonTools.multidict
        expected = "{'cat': [Mammal(species='cat')], 'dog': [Mammal(species='dog')]}"
        assert str(dict(f([Mammal("cat"), Mammal("dog")], "species"))) == expected

    def test_longest(self: Self) -> None:
        f = CommonTools.longest
        assert f(["1", "abc", "xyz", "2"]) == "abc"


if __name__ == "__main__":
    pytest.main()
