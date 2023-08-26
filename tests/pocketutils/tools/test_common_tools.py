from dataclasses import dataclass
from typing import Any, Self

import numpy as np
import pytest
from pocketutils.tools.common_tools import CommonTools


@dataclass(frozen=True, slots=True)
class Mammal:
    species: Any


class TestCommon:
    def test_try_none(self: Self):
        f = CommonTools.try_none

        def success():
            return None

        def fail():
            raise ValueError()

        assert f(fail) is None
        assert f(success) is None
        assert f(lambda: 5) == 5
        assert f(fail, exception=ValueError) is None
        assert f(fail, exception=Exception) is None
        with pytest.raises(ValueError):
            f(fail, exception=TypeError)
        assert f(fail, fail_val=-1) == -1

    def test_or_raise(self: Self):
        f = CommonTools.or_raise
        assert f(5) == 5
        with pytest.raises(LookupError):
            f(None)
        assert f(5, lambda s: "abc") == "abc"
        with pytest.raises(AttributeError):
            f(5, lambda s: s.dne)
        with pytest.raises(ValueError):
            f(None, or_else=ValueError)

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
        assert f([Mammal("cat"), Mammal("dog"), Mammal("cat")], "species") == "cat"
        assert f("21") == "2"
        assert f([]) is None
        with pytest.raises(TypeError):
            # noinspection PyTypeChecker
            f(None)

    def test_multidict(self: Self):
        f = CommonTools.multidict
        expected = "{'cat': [Mammal(species='cat')], 'dog': [Mammal(species='dog')]}"
        assert str(dict(f([Mammal("cat"), Mammal("dog")], "species"))) == expected


if __name__ == "__main__":
    pytest.main()
