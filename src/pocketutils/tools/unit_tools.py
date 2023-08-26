import logging
import math
import warnings
from datetime import date, datetime, timedelta
from typing import Self, SupportsFloat

from pint import UnitRegistry

from pocketutils.core.exceptions import OutOfRangeError
from pocketutils.tools.string_tools import StringTools

logger = logging.getLogger("pocketutils")
_UNIT_REG = UnitRegistry()
Quantity = _UNIT_REG.Quantity

# Silence NEP 18 warning
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    Quantity([])


class UnitTools:
    @classmethod
    def quantity(cls: type[Self], value: SupportsFloat, unit: str) -> Quantity:
        return Quantity(value, unit)

    @classmethod
    def format_approx_big_number(cls: type[Self], n: int) -> str:
        for k, v in {1e15: "", 1e12: "T", 1e9: "B", 1e6: "M", 1e3: "k"}.items():
            if n >= k:
                return str(n // k) + v
        return str(n)

    @classmethod
    def approx_time_wrt(
        cls: type[Self],
        now: date | datetime,
        then: date | datetime,
        *,
        skip_today: bool = False,
        sig: int = 3,
    ) -> str:
        """
        Describes `then` with higher resolution for smaller differences to `now`.

        Examples:
            - `approx_time_wrt(date(2021, 1, 12), date(1996, 10, 1))  # "1996"`
            - `approx_time_wrt(date(2021, 1, 12), date(2021, 10, 1))  # "2021-01-12"`
            - `approx_time_wrt(date(2021, 10, 1), datetime(2021, 10, 1, 11, 55))  # "2021-01-12 11:55"`
            - `approx_time_wrt(date(2021, 10, 1), datetime(2021, 10, 1, 11, 0, 0, 30, 222222))  # "2021-01-12 00:00:30"`
            - `approx_time_wrt(date(2021, 10, 1), datetime(2021, 10, 1, 11, 0, 0, 2, 222222))  # "2021-01-12 00:00:02.222"`
            - `approx_time_wrt(date(2021, 10, 1), datetime(2021, 10, 1, 11, 0, 0, 2, 22))  # "2021-01-12 00:00:02.000022"`
        """
        delta = now - then if now > then else then - now
        tot_days = (delta.days) + (delta.seconds / 86400) + (delta.microseconds / 86400 / 10**6)
        tot_secs = tot_days * 86400
        _today = "" if skip_today and then.date() == now.date() else "%Y-%m-%d "
        if tot_days > sig * 365.24219:
            return str(then.year)
        elif tot_days > sig * 30.437:
            return then.strftime("%Y-%m")
        elif tot_days > sig:
            return then.strftime("%Y-%m-%d")
        elif tot_secs > sig * 60:
            return then.strftime(_today + "%H:%M")
        elif tot_secs > sig:
            return then.strftime(_today + "%H:%M:%S")
        elif tot_secs > sig / 1000:
            return then.strftime(_today + "%H:%M:%S") + "." + str(round(then.microsecond / 1000))
        else:
            return then.strftime(_today + "%H:%M:%S.%f")

    @classmethod
    def delta_time_to_str(cls: type[Self], delta_sec: float | timedelta, *, space: str = "") -> str:
        """
        Returns a pretty string from a difference in time in seconds.
        Rounds hours and minutes to 2 decimal places, and seconds to 1.
        Ex: delta_time_to_str(313) == 5.22min
            delta_sec: The time in seconds
            space: Space char between digits and units;
                   good choices are empty, ASCII space, Chars.narrownbsp, Chars.thinspace,
                   and Chars.nbsp.

        Returns:
            A string with units 'hr', 'min', or 's'
        """
        if isinstance(delta_sec, timedelta):
            delta_sec = delta_sec.total_seconds()
        if abs(delta_sec) > 60 * 60 * 3:
            return StringTools.strip_empty_decimal(str(round(delta_sec / 60 / 60, 2))) + space + "hr"
        elif abs(delta_sec) > 180:
            return StringTools.strip_empty_decimal(str(round(delta_sec / 60, 2))) + space + "min"
        else:
            return StringTools.strip_empty_decimal(str(round(delta_sec, 1))) + space + "s"

    @classmethod
    def ms_to_minsec(cls: type[Self], ms: int, space: str = "") -> str:
        """
        Converts a number of milliseconds to one of the following formats.
        Will be one of these:
            - 10ms         if < 1 sec
            - 10:15        if < 1 hour
            - 10:15:33     if < 1 day
            - 5d:10:15:33  if > 1 day
        Prepends a minus sign (-) if negative.

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
        sgn = "-" if ms < 0 else ""
        if ms < 1000:
            return f"{sgn}{ms}{space}ms"
        elif days > 1:
            return f"{days}d:{z_hr}:{z_min}:{z_sec}"
        elif hours > 1:
            return f"{sgn}{z_hr}:{z_min}:{z_sec}"
        else:
            return f"{sgn}{z_min}:{z_sec}"

    @classmethod
    def round_to_sigfigs(cls: type[Self], num: SupportsFloat, n_sig_figs: int | None) -> float:
        """
        Round to specified number of sigfigs.

        Args:
            num: Floating-point number to round
            n_sig_figs: The number of significant figures, non-negative

        Returns:
            A Python integer
        """
        if n_sig_figs is None:
            return float(num)
        if n_sig_figs < 0:
            msg = f"sig_figs {n_sig_figs} is negative"
            raise OutOfRangeError(msg, minimum=0)
        num = float(num)
        if num != 0:
            digits = -int(math.floor(math.log10(abs(num))) - (n_sig_figs - 1))
            return round(num, digits)
        else:
            return 0  # can't take the log of 0

    @classmethod
    def format_dimensioned(
        cls: type[Self],
        value: float,
        unit: str,
        n_digits: int | None = None,
        n_sigfigs: int | None = None,
        *,
        space: str = "",
    ) -> str:
        """
        Returns a value with units, with the units scaled as needed.

        Args:
            value: Value without a prefix
            unit: Unit
            n_digits: Number of digits after the decimal point
            n_sigfigs: Rounds to a number of significant (nonzero) figures
            space: Space char between digits and units;
                   good choices are empty, ASCII space,
                   :attr:`pocketutils.core.chars.Chars.narrownbsp`,
                   :attr:`pocketutils.core.chars.Chars.thinspace`,
                   and :attr:`pocketutils.core.chars.Chars.nbsp`.

        Returns:
            The value with a suffix like `"5.2 mg"`
        """
        if n_digits is not None:
            value = round(value, n_digits)
        value = cls.round_to_sigfigs(value, n_sigfigs)
        dimmed = value * getattr(_UNIT_REG, unit)
        return f"{dimmed:~}" + space + unit


__all__ = ["UnitTools", "Quantity"]
