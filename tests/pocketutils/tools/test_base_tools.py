import numpy as np
import pytest

from pocketutils.core.exceptions import LengthMismatchError, MultipleMatchesError
from pocketutils.core.mocks import Mammal, MockCallable, MockWritable, WritableCallable
from pocketutils.tools.base_tools import BaseTools


class TestBaseTools:
    def test_is_lambda(self):
        f = BaseTools.is_lambda
        assert f(lambda: None)
        assert f(lambda x: None)
        assert f(lambda x, y: None)
        assert not f(None)

        def yes():
            return None

        assert not f(yes)

        class X:
            pass

        assert not f(X())
        assert not f(X)
        assert not f(1)

    def test_only(self):
        only = BaseTools.only
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

    def test_zip_strict(self):
        with pytest.raises(TypeError):
            # noinspection PyTypeChecker
            list(BaseTools.zip_strict(1))
        with pytest.raises(TypeError):
            # noinspection PyTypeChecker
            len(BaseTools.zip_strict([1, 2], [3, 4]))
        assert len(BaseTools.zip_list([1, 2], [3, 4])) == 2
        assert len(BaseTools.zip_list()) == 0
        for z in (BaseTools.zip_strict, BaseTools.zip_list):
            assert list(z([1, 2], [3, 4])) == [(1, 3), (2, 4)]
            assert list(z()) == []
            assert list(z([])) == []
            with pytest.raises(LengthMismatchError):
                list(z([1], [2, 3]))
            with pytest.raises(LengthMismatchError):
                list(z([1, 2], [3]))
            with pytest.raises(LengthMismatchError):
                list(z([1], []))

    def test_to_true_iterable(self):
        f = BaseTools.to_true_iterable
        assert f(1) == [1]
        assert f("abc") == ["abc"]
        assert f(bytes(5)) == [bytes(5)]
        assert f([1, 2]) == [1, 2]
        assert f(list(np.array([1, 2]))) == list(np.array([1, 2]))

    def test_look(self):
        f = BaseTools.look
        with pytest.raises(TypeError):
            # noinspection PyTypeChecker
            f(1, 1)
        assert f(Mammal("cat"), "species") == "cat"
        assert f(Mammal("cat"), "owner") is None
        # assert f(Mammal(Mammal('cat')), 'species') == Mammal('cat')
        assert f(Mammal(Mammal("cat")), "species.species") == "cat"
        assert str(f(Mammal(Mammal("cat")), "species")) == "<cat>|"
        assert f(Mammal(Mammal("cat")), lambda m: m.species.species) == "cat"

    def test_get_log_function(self):
        from pocketutils.core import logger

        f = BaseTools.get_log_function
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
