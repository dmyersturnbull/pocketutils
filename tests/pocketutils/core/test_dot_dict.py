import pytest

from pocketutils.core.dot_dict import *


class TestDotDict:
    def test(self):
        t = NestedDotDict({"a": "0", "b": 1, "c": {"c1": 8, "c2": ["abc", "xyz"]}})
        assert list(t.keys()) == ["a", "b", "c"]


if __name__ == "__main__":
    pytest.main()
