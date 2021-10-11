import os

import pytest

from pocketutils.core.exceptions import IllegalPathError
from pocketutils.tools.path_tools import *

raises = pytest.raises


class TestPathTools:
    def test_sanitize_path_node_root(self):
        x = PathTools.sanitize_node
        for file in [None, False]:
            for root in [None, True]:
                assert x("C:", is_file=file, is_root_or_drive=root) == "C:\\"
                assert x("C:\\", is_file=file, is_root_or_drive=root) == "C:\\"
                assert x("/", is_file=file, is_root_or_drive=root) == "/"

    def test_sanitize_path_node_nonroot(self):
        x = PathTools.sanitize_node
        assert x("C:", is_root_or_drive=False) == "C_"
        assert x(" C: ", is_root_or_drive=False) == "C_"
        assert x("C:\\", is_root_or_drive=False) == "C__"
        assert x("C:/", is_root_or_drive=False) == "C__"
        assert x(".", is_root_or_drive=False) == "."
        assert x("..", is_root_or_drive=False) == ".."

    def test_sanitize_path_abs(self):
        def z(s, **kwargs):
            return str(PathTools.sanitize_path(s, **kwargs, warn=False))

        # weird case. drive letters in Linux
        if os.name == "posix":
            assert z(r"C:\abc\22") == r"/C:/abc/22"
            assert z(r"C:\abc\\22") == r"/C:/abc/22"
            assert z("C:\\abc\\./22") == r"/C:/abc/22"
        elif os.name == "nt":
            assert z(r"C:\abc\22") == r"C:\abc\22"
            assert z(r"C:\abc\\22") == r"C:\abc\22"
            assert z("C:\\abc\\./22") == r"C:\abc\22"
        else:
            assert False, "OS {} is not supported"

    def test_sanitize_path(self):
        def x(s, **kwargs):
            return str(PathTools.sanitize_path(s, **kwargs, warn=False)).replace("\\", "/")

        assert x("abc\\./22") == "abc/22"
        assert x("/abc\\./22") == "/abc/22"
        assert x("./abc\\./22") == "abc/22"
        assert str(x("abc|xyz", is_file=False)) == "abc_xyz"
        assert str(x("abc\\xyz.", is_file=False)) == "abc/xyz"
        assert str(x("..\\5")) == "../5"
        assert str(x("xyz...", is_file=False)) == "xyz"
        assert str(x("abc\\.\\xyz\\n.", is_file=False)) == "abc/xyz/n"
        with raises(IllegalPathError):
            x("x" * 255)
        assert str(x("NUL")) == "_NUL_"
        assert str(x("nul")) == "_nul_"
        assert str(x("nul.txt")) == "_nul_.txt"
        assert str(x("abc\\NUL")) == "abc/_NUL_"
        assert str(x("NUL\\abc")) == "_NUL_/abc"


if __name__ == "__main__":
    pytest.main()
