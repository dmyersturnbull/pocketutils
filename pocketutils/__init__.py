"""
Metadata for this project.
"""

import logging
from importlib.metadata import PackageNotFoundError
from importlib.metadata import metadata as __load
from pathlib import Path

from pocketutils.core import *
from pocketutils.core.chars import *
from pocketutils.core.decorators import *
from pocketutils.core.dot_dict import *
from pocketutils.core.enums import *
from pocketutils.core.exceptions import *
from pocketutils.core.frozen_types import *
from pocketutils.core.input_output import *
from pocketutils.core.iterators import *
from pocketutils.core.smartio import SmartIo
from pocketutils.tools.call_tools import *
from pocketutils.tools.common_tools import *
from pocketutils.tools.console_tools import *
from pocketutils.tools.filesys_tools import *
from pocketutils.tools.io_tools import *
from pocketutils.tools.json_tools import JsonTools
from pocketutils.tools.numeric_tools import *
from pocketutils.tools.parse_tools import ParseTools
from pocketutils.tools.path_tools import *
from pocketutils.tools.program_tools import *
from pocketutils.tools.reflection_tools import *
from pocketutils.tools.string_tools import *
from pocketutils.tools.sys_tools import *
from pocketutils.tools.unit_tools import *

pkg = Path(__file__).absolute().parent.name
logger = logging.getLogger(pkg)
metadata = None
try:
    metadata = __load(pkg)
    __status__ = "Development"
    __copyright__ = "Copyright 2016–2023"
    __date__ = "2020-09-01"
    __uri__ = metadata["home-page"]
    __title__ = metadata["name"]
    __summary__ = metadata["summary"]
    __license__ = metadata["license"]
    __version__ = metadata["version"]
    __author__ = metadata["author"]
    __maintainer__ = metadata["maintainer"]
    __contact__ = metadata["maintainer"]
except PackageNotFoundError:  # pragma: no cover
    logger.error(f"Could not load package metadata for {pkg}. Is it installed?")


class Tools(
    CallTools,
    CommonTools,
    ConsoleTools,
    FilesysTools,
    IoTools,
    JsonTools,
    NumericTools,
    PathTools,
    ParseTools,
    ProgramTools,
    ReflectionTools,
    StringTools,
    SystemTools,
    UnitTools,
):
    """
    A collection of utility static functions.
    """
