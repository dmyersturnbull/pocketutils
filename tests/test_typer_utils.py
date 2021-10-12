import pytest
from typer.models import ArgumentInfo, OptionInfo

from pocketutils.misc.typer_utils import Arg, Opt, TyperUtils


class TestTyperUtils:
    def test_arg_opt(self):
        x = Arg.val("hello")
        assert isinstance(x, ArgumentInfo)
        x = Opt.val("hello")
        assert isinstance(x, OptionInfo)
        x = Opt.val("hello", default=...)
        assert isinstance(x, OptionInfo)


if __name__ == "__main__":
    pytest.main()
