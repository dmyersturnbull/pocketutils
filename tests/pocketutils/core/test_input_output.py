# SPDX-FileCopyrightText: Copyright 2020-2023, Contributors to pocketutils
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/pocketutils
# SPDX-License-Identifier: Apache-2.0
from io import StringIO
from typing import Self

import pytest
from pocketutils.core.input_output import Capture, DelegatingWriter, OpenMode
from pocketutils.core.mocks import MockWritable


class TestIo:
    def test_delegating(self: Self) -> None:
        a, b = MockWritable(), MockWritable()
        d = DelegatingWriter(a, b)
        d.write("abc")
        assert a.data == "write:abc"
        assert b.data == "write:abc"
        d.flush()
        assert a.data == "write:abcflush"
        assert b.data == "write:abcflush"
        d.close()
        assert a.data == "write:abcflushclose"
        assert b.data == "write:abcflushclose"
        a.write("00")
        assert a.data == "write:00"
        assert b.data == "write:abcflushclose"

    def test_capture(self: Self) -> None:
        w = StringIO("abc")
        c = Capture(w)
        assert c.value == "abc"

    def test_open_mode_normalize(self: Self) -> None:
        o = OpenMode
        assert str(o("").normalize()) == "rt"
        assert str(o("r").normalize()) == "rt"
        assert str(o("wU").normalize()) == "wt"
        assert str(o("a").normalize()) == "at"
        assert str(o("w+").normalize()) == "wt+"
        assert str(o("wt+").normalize()) == "wt+"
        assert str(o("wb+").normalize()) == "wb+"
        assert str(o("Ux").normalize()) == "xt"
        assert str(o("Uxb").normalize()) == "xb"


if __name__ == "__main__":
    pytest.main()
