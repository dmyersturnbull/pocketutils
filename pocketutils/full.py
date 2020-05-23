import numpy as np
import pandas as pd
from littlesnippets.core.chars import *
from littlesnippets.core import frozenlist, SmartEnum
from littlesnippets.core.io import *
from littlesnippets.tools.call_tools import *
from littlesnippets.tools.common_tools import *
from littlesnippets.tools.console_tools import *
from littlesnippets.tools.loop_tools import *
from littlesnippets.tools.numeric_tools import *
from littlesnippets.tools.pandas_tools import *
from littlesnippets.tools.path_tools import *
from littlesnippets.tools.program_tools import *
from littlesnippets.tools.string_tools import *
from littlesnippets.tools.filesys_tools import *
from littlesnippets.tools.unit_tools import *
from littlesnippets.core.exceptions import *
from littlesnippets.core.iterators import *
from littlesnippets.core import SmartEnum, OptRow


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
