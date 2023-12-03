# SPDX-FileCopyrightText: Copyright 2020-2023, Contributors to pocketutils
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/pocketutils
# SPDX-License-Identifier: Apache-2.0
"""
Metadata and environment variables.
"""

import logging
import tomllib
from importlib.metadata import PackageNotFoundError
from importlib.metadata import metadata as __load
from pathlib import Path

__all__ = ["Metadata"]

_pkg = Path(__file__).parent.name
logger = logging.getLogger(_pkg)
_metadata = {}
try:
    _metadata = __load(_pkg)
except PackageNotFoundError:  # nocov
    _pyproject = Path(__file__).parent / "pyproject.toml"
    if _pyproject.exists():
        _data = tomllib.loads(_pyproject.read_text(encoding="utf-8"))
        _metadata = {k.capitalize(): v for k, v in _data["project"]}
    else:
        logger.error(f"Could not load metadata for package {_pkg}. Is it installed?")


class Metadata:
    pkg = _pkg
    homepage = _metadata.get("Home-page")
    title = _metadata.get("Name")
    summary = _metadata.get("Summary")
    license = _metadata.get("License")
    version = _metadata.get("Version")
