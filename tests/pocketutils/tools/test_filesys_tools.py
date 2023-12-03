# SPDX-FileCopyrightText: Copyright 2020-2023, Contributors to pocketutils
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/pocketutils
# SPDX-License-Identifier: Apache-2.0
from pathlib import Path
from typing import Self

import pytest
from pocketutils.tools.filesys_tools import FilesysTools


def load(parts: str) -> Path:
    if isinstance(parts, str):
        parts = [parts]
    return Path(Path(__file__).parent.parent.parent / "resources" / "core", *parts)


class TestFilesysTools:
    def test_get_info(self: Self) -> None:
        file = load("lines.lines")
        info = FilesysTools.get_info(file)
        assert info.is_file
        assert info.mod_or_create_dt is not None
        info = FilesysTools.get_info(".")
        assert info.is_dir
        assert not info.is_file
        assert info.mod_or_create_dt is not None


if __name__ == "__main__":
    pytest.main()
