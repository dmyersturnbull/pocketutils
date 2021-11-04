import pytest

from pocketutils.tools.sys_tools import SystemTools


class TestSysTools:
    def test_add_signals(self):
        pass

    def test_get_env_info(self):
        data = SystemTools.get_env_info(include_insecure=True)
        assert len(data) > 20
        assert "pid" in data
        assert "disk_used" in data
        assert "hostname" in data
        assert "lang_code" in data

    def test_list_imports(self):
        data = SystemTools.list_package_versions()
        assert len(data) > 5
        assert "orjson" in data
        assert data["orjson"].startswith("3.")  # change when updated


if __name__ == "__main__":
    pytest.main()
