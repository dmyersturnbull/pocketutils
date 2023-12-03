# SPDX-FileCopyrightText: Copyright 2020-2023, Contributors to pocketutils
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/pocketutils
# SPDX-License-Identifier: Apache-2.0
from typing import Self

import pytest
from pocketutils.tools.sys_tools import SystemTools


class TestSysTools:
    def test_get_env_info(self: Self) -> None:
        data = SystemTools.get_env_info()
        assert len(data) > 20
        assert "pid" not in data
        assert "disk_used" not in data
        assert "hostname" not in data
        assert "lang_code" in data

    def test_get_env_info_extended(self: Self) -> None:
        data = SystemTools.get_env_info(extended=True)
        assert len(data) > 20
        assert "pid" not in data
        assert "disk_used" in data
        assert "hostname" not in data
        assert "lang_code" in data

    def test_get_env_info_insecure(self: Self) -> None:
        data = SystemTools.get_env_info(insecure=True)
        assert len(data) > 20
        assert "pid" in data
        assert "disk_used" not in data
        assert "hostname" in data
        assert "lang_code" in data

    def test_list_imports(self: Self) -> None:
        data = SystemTools.list_package_versions()
        assert len(data) > 5
        assert "orjson" in data
        assert data["orjson"].startswith("3.")  # change when updated


if __name__ == "__main__":
    pytest.main()
