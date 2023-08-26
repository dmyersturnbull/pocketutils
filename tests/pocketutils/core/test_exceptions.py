from typing import Self

import pytest
from pocketutils.core.exceptions import HashValidationError

E = HashValidationError


class TestExceptions:
    def test_args(self: Self) -> None:
        assert hasattr(E(), "key")
        assert E().key is None
        assert E("abc").key is None
        assert E("abc", key=5).key == 5

    def test_str(self: Self) -> None:
        assert str(E()) == ""
        assert str(E(key=5)) == ""
        assert str(E("asdf")) == "asdf"
        assert str(E("asdf", key=5)) == "asdf"

    def test_info(self: Self) -> None:
        assert E("abc", key=5).info() == "HashValidationError:abc(actual=None,expected=None,key=5)"

    def test_equality(self: Self) -> None:
        assert E() == E()
        assert E() is not E()
        assert E() != E(key=5)
        assert E(key=5) == E(key=5)
        assert E("a", key=5) == E("a", key=5)
        assert E(key=5) != E("a", key=5)
        assert E("a", key=5) != E("a")
        assert E("a") == E("a")

    def test_doc(self: Self) -> None:
        assert E.__doc__ is not None
        e = E.__doc__.splitlines()
        assert len(e) >= 2
        assert e[-2].endswith("expected: str")
        assert e[-1].endswith("actual: str")


if __name__ == "__main__":
    pytest.main()
