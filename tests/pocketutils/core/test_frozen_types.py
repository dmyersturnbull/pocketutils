# SPDX-FileCopyrightText: Copyright 2020-2023, Contributors to pocketutils
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/pocketutils
# SPDX-License-Identifier: Apache-2.0
import pytest
from pocketutils.core.frozen_types import FrozeDict, FrozeList, FrozeSet
from pocketutils.tools.common_tools import CommonTools


class TestFrozen:
    def test_list(self):
        x: FrozeList = CommonTools.freeze([1, 2, 3])
        assert isinstance(x, FrozeList)
        assert x.to_list() == [1, 2, 3]
        assert str(x) == str(x.to_list())
        assert repr(x) == repr(x.to_list())
        y: FrozeList = CommonTools.freeze([1, 2, 1])
        assert x == x and y == y
        assert not x < x and not y < y
        assert x > y
        assert hash(x) == hash(x)
        assert hash(x) != hash(y)
        assert x.get(1) == 1
        assert x.req(1) == 1
        assert x[1] == 2
        assert x[0:2] == [1, 2]
        assert x.get(5) is None
        assert x.get(5, 100) == 100
        assert x.get(5, 100) == 100
        with pytest.raises(KeyError):
            x.req(5)
        with pytest.raises(TypeError):
            del x[1]
        with pytest.raises(AttributeError):
            x.remove(1)

    def unhashable_list(self):
        x: FrozeList = CommonTools.freeze([[1]])
        y: FrozeList = CommonTools.freeze([[1]])
        assert hash(x) == 1
        assert {x} != {y}

    def test_set(self):
        x: FrozeSet = CommonTools.freeze({1, 2, 3})
        assert isinstance(x, FrozeSet)
        assert x.to_set() == {1, 2, 3}
        assert str(x) == str(x.to_set())
        assert repr(x) == repr(x.to_set())
        assert x.to_frozenset() == frozenset({1, 2, 3})
        y: FrozeSet = CommonTools.freeze({1, 2, 1})
        assert x == x and y == y
        assert not x < x and not y < y
        assert x > y
        assert hash(x) == hash(x)
        assert hash(x) != hash(y)
        assert not x.isdisjoint(y)
        assert x.get(1) == 1
        assert x.get(5) is None
        assert x.get(5, 100) == 100
        assert x.req(1) == 1
        assert x.get(5, 100) == 100
        x.req(5)
        with pytest.raises(AttributeError):
            x.remove(1)

    def test_dict(self):
        x: FrozeDict = CommonTools.freeze({1: "cat", 2: "dog"})
        assert isinstance(x, FrozeDict)
        assert str(x) == str(x.to_dict())
        assert repr(x) == repr(x.to_dict())
        y: FrozeDict = CommonTools.freeze({1: "cat", 2: "zebra"})
        z: FrozeDict = CommonTools.freeze({2: "cat", 3: "aardvark"})
        assert x == x and y == y and z == z
        assert x != y and x != z and y != z
        assert x < z
        assert x < y
        assert y < z
        assert not x < x
        assert not y < y
        assert not z < z
        assert hash(x) == hash(x) and hash(y) == hash(y) and hash(z) == hash(z)
        assert hash(x) != hash(y)
        assert x.get(1) == "cat"
        assert x.get(5) is None
        assert x.get(5, "elephant") == "elephant"
        assert x.req(1) == "cat"
        assert x.get(5, "elephant") == "elephant"
        with pytest.raises(KeyError):
            x.req(5)
        with pytest.raises(AttributeError):
            x.remove(1)
        with pytest.raises(TypeError):
            x[1] = 2


if __name__ == "__main__":
    pytest.main()
