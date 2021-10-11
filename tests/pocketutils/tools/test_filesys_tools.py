from pathlib import Path

import pytest

from pocketutils.core.exceptions import ParsingError
from pocketutils.tools.filesys_tools import FilesysTools


def load(parts):
    if isinstance(parts, str):
        parts = [parts]
    return Path(Path(__file__).parent.parent.parent / "resources" / "core", *parts)


class TestFilesysTools:
    def test_read_lines(self):
        assert list(FilesysTools.read_lines_file(load("lines.lines"))) == [
            "line1 = 5",
            "line2=5",
            "",
            "#line3",
            "line4 = a",
        ]
        assert list(FilesysTools.read_lines_file(load("lines.lines"), ignore_comments=True)) == [
            "line1 = 5",
            "line2=5",
            "line4 = a",
        ]

    def test_read_properties(self):
        f = FilesysTools.read_properties_file
        expected = {"line1": "5", "line2": "5", "line4": "a"}
        assert dict(f(load("lines.lines"))) == expected
        with pytest.raises(ParsingError):
            f(load("bad1.properties"))
        with pytest.raises(ParsingError):
            f(load("bad2.properties"))

    def test_get_info(self):
        file = load("lines.lines")
        info = FilesysTools.get_info(file)
        assert info.is_file
        assert info.mod_or_create_dt is not None
        info = FilesysTools.get_info(".")
        assert info.is_dir
        assert not info.is_file
        assert info.mod_or_create_dt is not None

    def test_get_env_info(self):
        data = FilesysTools.get_env_info(include_insecure=True)
        assert len(data) > 20
        assert "pid" in data
        assert "disk_used" in data
        assert "hostname" in data
        assert "locale" in data

    def test_list_imports(self):
        data = FilesysTools.list_package_versions()
        assert len(data) > 5
        assert "orjson" in data
        assert data["orjson"].startswith("3.")  # change when updated


if __name__ == "__main__":
    pytest.main()
