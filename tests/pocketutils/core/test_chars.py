import pytest
from dscience.core.chars import Chars

raises = pytest.raises


class TestChars:
    def test_range(self):
        assert Chars.range(1, 2) == "1–2"  # en dash

    def test_shelled(self):
        assert Chars.shelled("xyz") == "〔xyz〕"


if __name__ == "__main__":
    pytest.main()
