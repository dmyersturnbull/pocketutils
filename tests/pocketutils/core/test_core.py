# SPDX-FileCopyrightText: Copyright 2020-2023, Contributors to pocketutils
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/pocketutils
# SPDX-License-Identifier: Apache-2.0
from datetime import datetime
from typing import Self

import pytest
from pocketutils.core import LazyWrap


class TestCore:
    def test_wrap(self: Self):
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


if __name__ == "__main__":
    pytest.main()
