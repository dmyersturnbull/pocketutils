from __future__ import annotations

import re

from pocketutils.tools.string_tools import StringTools
from pocketutils.tools.unit_tools import UnitTools


class RefDims(dict):
    """
    Reference widths and heights by name.

    Example:
        Ex::

            widths[1"]
            widths['1/3 2_col']
            widths['(2/1) 2_col']

    NOTES!!!
    If `width_pad` (`height_pad`, respectively) is set, this will be included in the calculation.
    For example, (1/3) 2_col will subtract off the appropriate padding for 3 cols (2 spaces shared between 3 columns).
    The size is then rounded to sigfigs after -- normally 6 sigfigs, but overridden with width_sigfigs / height_sigfigs.
    The sum / difference is applied after.

    """

    def __init__(self, axis: str, n_sigfigs: int = 6):
        """

        Args:
            axis:
            n_sigfigs:
        """
        super().__init__()
        self.axis = axis
        self.n_sigfigs = n_sigfigs
        self.current_text: str = ""
        self.current: float = 0.0

    def point(self, item: str) -> float:
        """
        Returns the resulting value (calling `self[item]`), also setting the text and value pointers in-place.
        It's best for this to match plt.rcParams[figure.figsize], but this is not required.

        Args:
            item: str:

        Returns:

        """
        scale = self[item]
        self.current_text = item
        self.current = scale
        return scale

    def __getitem__(self, item: str) -> float:
        """

        Args:
            item:

        Returns:

        """
        # first, match exact inches
        # If name is empty or double quote, assume it means inch (ex: '1' is 1 inch; 1/3 is 1/3 inch)
        # And in this case, ignore padding (take the size as-is, except for rounding)
        # For ex, '1/3 "' gets converted to 0.333333 if self.n_sigfigs==6
        # Whereas if the user defined 'inch', then '1/3 inch' will get padding removed, so it might be, say, round(1/3 - 2*0.1/3)
        item = str(item)
        match = re.compile(r'^ *([0-9.]+) *"? *$').fullmatch(item.lower())
        if match is not None:
            return float(match.group(1))
        # now match fancy expressions
        # they're of the form (<numerator>/<denominator>?)? <name>
        # note the lazy ?? here
        match = re.compile(r"^ *(?:([0-9]+)(?:/([0-9]+))?)?? *([0-9A-Za-z_\-/]+) *$").fullmatch(
            item.lower()
        )
        pad = self.get("pad", 0.0)
        numerator = int(match.group(1)) if match.group(1) is not None else 1
        denominator = int(match.group(2)) if match.group(2) is not None else 1
        name = match.group(3)
        name = StringTools.strip_off_start(StringTools.strip_off_start(name, "width_"), "height_")
        name_val = super().__getitem__(name)
        frac = denominator / numerator  # flip for simplicity
        # Note the math here:
        # Subtract off the padding needed
        # If it's it's 1/3 of some value, we'll need to add 2 pieces of padding shared between the three
        # This is then 2/3*padding per unit ==> so subtract it
        return UnitTools.round_to_sigfigs(name_val / frac - (frac - 1) * pad / frac, self.n_sigfigs)

    def __setitem__(self, key: str, value: float):
        """
        Args:
            key:
            value:

        """
        try:
            super().__setitem__(key, float(value))
        except Exception:
            raise TypeError(f"{value} is not a float")


__all__ = ["RefDims"]
