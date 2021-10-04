import logging
import math
from typing import Optional, SupportsFloat, Tuple, Union

import regex

from pocketutils.core._internal import nicesize
from pocketutils.core.exceptions import OutOfRangeError, StringPatternError
from pocketutils.tools.base_tools import BaseTools
from pocketutils.tools.string_tools import StringTools

logger = logging.getLogger("pocketutils")


class UnitTools(BaseTools):
    @classmethod
    def delta_time_to_str(cls, delta_sec: float, space: str = "") -> str:
        """
        Returns a pretty string from a difference in time in seconds.
        Rounds hours and minutes to 2 decimal places, and seconds to 1.
        Ex: delta_time_to_str(313) == 5.22min
            delta_sec: The time in seconds
            space: Space char between digits and units;
                good choices are empty, ASCII space, Chars.narrownbsp, Chars.thinspace, and Chars.nbsp.

        Returns:
            A string with units 'hr', 'min', or 's'
        """
        if abs(delta_sec) > 60 * 60 * 3:
            return (
                StringTools.strip_empty_decimal(str(round(delta_sec / 60 / 60, 2))) + space + "hr"
            )
        elif abs(delta_sec) > 180:
            return StringTools.strip_empty_decimal(str(round(delta_sec / 60, 2))) + space + "min"
        else:
            return StringTools.strip_empty_decimal(str(round(delta_sec, 1))) + space + "s"

    @classmethod
    def ms_to_minsec(cls, ms: int, space: str = "") -> str:
        """
        Converts a number of milliseconds to one of the following formats:
            - 10ms         if < 1 sec
            - 10:15        if < 1 hour
            - 10:15:33     if < 1 day
            - 5d:10:15:33  if > 1 day
        Prepends a minus sign (−) if negative.

        Args:
            ms: The milliseconds
            space: Space char between digits and 'ms' (if used);
                   good choices are empty, ASCII space, Chars.narrownbsp,
                   Chars.thinspace, and Chars.nbsp.

        Returns:
            A string of one of the formats above
        """
        ms = abs(int(ms))
        seconds = int((ms / 1000) % 60)
        minutes = int((ms / (1000 * 60)) % 60)
        hours = int((ms / (1000 * 60 * 60)) % 24)
        days = int(ms / (1000 * 60 * 60 * 24))
        z_hr = str(hours).zfill(2)
        z_min = str(minutes).zfill(2)
        z_sec = str(seconds).zfill(2)
        sgn = "−" if ms < 0 else ""
        if ms < 1000:
            return f"{sgn}{ms}{space}ms"
        elif days > 1:
            return f"{days}d:{z_hr}:{z_min}:{z_sec}"
        elif hours > 1:
            return f"{sgn}{z_hr}:{z_min}:{z_sec}"
        else:
            return f"{sgn}{z_min}:{z_sec}"

    @classmethod
    def friendly_size(cls, n_bytes: int, *, space: str = " ") -> str:
        """
        Returns a text representation of a number of bytes.
        Uses base 2 with IEC 1998, rounded to 0 decimal places, and without a space.
        """
        return nicesize(n_bytes, space=space)

    @classmethod
    def round_to_sigfigs(cls, num: SupportsFloat, sig_figs: int) -> float:
        """
        Round to specified number of sigfigs.

        Args:
            num: A Python or Numpy float or something that supports __float__
            sig_figs: The number of significant figures, non-negative

        Returns:
            A Python integer
        """
        if sig_figs < 0:
            raise OutOfRangeError(f"sig_figs {sig_figs} is negative", minimum=0)
        num = float(num)
        if num != 0:
            digits = -int(math.floor(math.log10(abs(num))) - (sig_figs - 1))
            return round(num, digits)
        else:
            return 0  # can't take the log of 0

    @classmethod
    def format_micromolar(
        cls,
        micromolar: float,
        n_sigfigs: Optional[int] = 5,
        *,
        adjust_units: bool = True,
        use_sigfigs: bool = True,
        space: str = "",
    ) -> str:
        """
        Returns a concentration with units, with the units scaled as needed.
        Can handle millimolar, micromolar, nanomolar, and picomolar.

        Args:
            micromolar: Value
            n_sigfigs: For rounding; no rounding if None
            adjust_units: If False, will always use micromolar
            use_sigfigs: If True, rounds to a number of significant figures; otherwise round to decimal places
            space: Space char between digits and units;
                   good choices are empty, ASCII space, Chars.narrownbsp, Chars.thinspace, and Chars.nbsp.

        Returns:
            The concentration with a suffix of µM, mM, nM, or mM
        """
        d = micromolar
        m = abs(d)
        unit = "µM"
        if adjust_units:
            if m < 1e-6:
                d *= 1e9
                unit = "fM"
            elif m < 1e-3:
                d *= 1e6
                unit = "pM"
            elif m < 1:
                d *= 1e3
                unit = "nM"
            elif m >= 1e6:
                d /= 1e6
                unit = "M"
            elif m >= 1e3:
                d /= 1e3
                unit = "mM"
        if n_sigfigs is None:
            pass
        elif use_sigfigs:
            d = cls.round_to_sigfigs(d, n_sigfigs)
        else:
            d = round(d, n_sigfigs)
        if round(d) == d and str(d).endswith(".0"):
            return str(d)[:-2] + space + unit
        else:
            return str(d) + space + unit

    @classmethod
    def split_species_micromolar(cls, text: str) -> Tuple[str, Optional[float]]:
        """
        Splits a name into a chemical/concentration pair, falling back with the full name.
        Ex: "abc 3.5uM" → (abc, 3.5)
        Ex: "abc 3.5 µM" → (abc, 3.5)
        Ex: "abc (3.5mM)" → (abc, 3500.0)
        Ex: "abc 3.5mM" → (abc, None)
        Ex: "3.5mM" → (3.5mM, None)  # an edge case: don't pass in only units
        Uses a moderately strict pattern for the drug and dose:
            - The dose must terminate the string, except for end parenthesis or whitespace.
            - The drug and dose must be separated by at least one non-alphanumeric, non-dot, non-hyphen character.
            - Units must follow the digits, separated by at most whitespace, and are case-sensitive.
        """
        # note the lazy ops in the first group and in the non-(alphanumeric/dot/dash) separator between the drug and dose
        pat = regex.compile(
            r"^\s*(.*?)(?:[^A-Za-z0-9.\-]+?[\s(\[{]*(\d+(?:.\d*)?)\s*([mµunpf]M)\s*[)\]}]*)?\s*$",
            flags=regex.V1,
        )
        match = pat.fullmatch(text)
        if match is None:
            raise StringPatternError(f"Text {text} couldn't be parsed", value=text, pattern=pat)
        if match.group(2) is None:
            return text.strip(), None
        else:
            drug = match.group(1).strip("([{)]}")
            dose = UnitTools.concentration_to_micromolar(float(match.group(2)), match.group(3))
            return drug, dose

    @classmethod
    def extract_micromolar(cls, text: str) -> Optional[float]:
        """
        Returns what looks like a concentration with units. Accepts one of: mM, µM, uM, nM, pM.
        Searches pretty flexibly.
        If no matches are found, returns None.
        If multiple matches are found, warns and returns None.
        """
        # we need to make sure mM ex isn't part of a larger name
        pat1 = regex.compile(r"(\d+(?:.\d*)?)\s*([mµunpf]M)\s*[)\]}]*", flags=regex.V1)

        def find(pat):
            return {
                UnitTools.concentration_to_micromolar(float(match.group(1)), match.group(2))
                for match in pat.finditer(text)
                if match is not None
            }

        matches = find(pat1)
        if len(matches) == 1:
            return next(iter(matches))
        elif len(matches) > 1:
            logger.warning(f"Found {len(matches)} potential doses: {matches} . Returning None.")
        return None

    @classmethod
    def concentration_to_micromolar(cls, digits: Union[str, float], units: str) -> float:
        """
        Ex: concentration_to_micromolar(53, 'nM')  # returns 0.053
        """
        return float(digits) * {
            "M": 1e6,
            "mM": 1e3,
            "µM": 1,
            "uM": 1,
            "nM": 1e-3,
            "pM": 1e-6,
            "fM": 1e-9,
        }[units]


__all__ = ["UnitTools"]
