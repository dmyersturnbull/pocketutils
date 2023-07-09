from datetime import datetime

import pytest

from pocketutils.core import LazyWrap, PathLikeUtils, frozenlist
from pocketutils.core.exceptions import ImmutableError


class TestCore:
    def test_wrap(self):
        DT = LazyWrap.new_type("datetime", datetime.now)
        dt = DT()
        assert str(dt) == "datetime[⌀]"
        assert not dt.is_defined
        assert dt.raw_value is None
        v = dt.get()
        assert isinstance(v, datetime)
        assert dt.raw_value == v
        assert dt.is_defined
        a, b = DT(), DT()
        assert a == b
        a.get()
        assert a != b

    def test_pathlike(self):
        assert PathLikeUtils.isinstance("")
        assert not PathLikeUtils.isinstance(5)

    def test_opt_row(self):
        pass  # TODO


if __name__ == "__main__":
    pytest.main()
