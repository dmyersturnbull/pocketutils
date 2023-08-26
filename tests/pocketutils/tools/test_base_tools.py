from dataclasses import dataclass
from typing import Any, Self

import numpy as np
import pytest
from pocketutils.core.exceptions import MultipleMatchesError
from pocketutils.core.mocks import MockCallable, MockWritable, WritableCallable
from pocketutils.tools.common_tools import CommonTools


@dataclass(frozen=True, slots=True)
class Mammal:
    species: Any


def outside_lambda(x):
    return x


def non_lambda():
    pass


class TestCommonTools:
    def test_is_lambda(self: Self) -> None:
        f = CommonTools.is_lambda
        assert f(lambda: None)
        assert f(lambda x: None)
        assert f(lambda x, y: None)
        assert f(outside_lambda)
        assert not f(None)
        assert not f(non_lambda)

        def yes():
            return None

        assert not f(yes)

        class X:
            pass

        assert not f(X())
        assert not f(X)
        assert not f(1)

    def test_only(self: Self) -> None:
        only = CommonTools.only
        with pytest.raises(TypeError):
            # noinspection PyTypeChecker
            only(1)
        assert only(["a"]) == "a"
        assert only("a") == "a"
        assert only({"ab"}) == "ab"
        with pytest.raises(MultipleMatchesError):
            only(["a", "b"])
        with pytest.raises(MultipleMatchesError):
            only("ab")
        with pytest.raises(LookupError):
            only([])
        with pytest.raises(LookupError):
            only("")

    def test_to_true_iterable(self: Self) -> None:
        f = CommonTools.to_true_iterable
        assert f(1) == [1]
        assert f("abc") == ["abc"]
        assert f(bytes(5)) == [bytes(5)]
        assert f([1, 2]) == [1, 2]
        assert f(list(np.array([1, 2]))) == list(np.array([1, 2]))

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

        f = CommonTools.get_log_function
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


if __name__ == "__main__":
    pytest.main()
