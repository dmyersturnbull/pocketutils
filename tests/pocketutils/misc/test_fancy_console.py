import pytest

from pocketutils.misc.fancy_console import ColorMessages
from pocketutils.misc.messages import MsgLevel

raises = pytest.raises


class TestColorMessages:
    def test(self):
        messages = ColorMessages(ColorMessages.default_color_map())
        messages.thin(MsgLevel.INFO, "test")
        messages.thin("INFO", "test")


if __name__ == "__main__":
    pytest.main()
