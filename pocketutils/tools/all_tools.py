from pocketutils.tools.call_tools import CallTools
from pocketutils.tools.common_tools import CommonTools
from pocketutils.tools.console_tools import ConsoleTools
from pocketutils.tools.filesys_tools import FilesysTools
from pocketutils.tools.numeric_tools import NumericTools
from pocketutils.tools.path_tools import PathTools
from pocketutils.tools.program_tools import ProgramTools
from pocketutils.tools.string_tools import StringTools
from pocketutils.tools.unit_tools import UnitTools


class Tools(
    CallTools,
    CommonTools,
    ConsoleTools,
    NumericTools,
    PathTools,
    ProgramTools,
    StringTools,
    FilesysTools,
    UnitTools,
):
    """
    A collection of utility static functions.
    """


__all__ = ["Tools"]
