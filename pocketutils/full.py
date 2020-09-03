import numpy as np
import pandas as pd

from pocketutils.core import OptRow, SmartEnum, frozenlist
from pocketutils.core.chars import *
from pocketutils.core.exceptions import *
from pocketutils.core.input_output import *
from pocketutils.core.iterators import *
from pocketutils.tools.call_tools import *
from pocketutils.tools.common_tools import *
from pocketutils.tools.console_tools import *
from pocketutils.tools.filesys_tools import *
from pocketutils.tools.loop_tools import *
from pocketutils.tools.numeric_tools import *
from pocketutils.tools.pandas_tools import *
from pocketutils.tools.path_tools import *
from pocketutils.tools.program_tools import *
from pocketutils.tools.string_tools import *
from pocketutils.tools.unit_tools import *


class Tools(
    CallTools,
    CommonTools,
    ConsoleTools,
    LoopTools,
    NumericTools,
    PandasTools,
    PathTools,
    ProgramTools,
    StringTools,
    FilesysTools,
    UnitTools,
):
    """
    A collection of utility static functions.
    Mostly provided for use outside of Kale, but can also be used by Kale code.
    """
