# SPDX-FileCopyrightText: Copyright 2020-2023, Contributors to pocketutils
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/pocketutils
# SPDX-License-Identifier: Apache-2.0
"""

"""

import logging
import math
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Self, SupportsFloat

from pocketutils.core.exceptions import ValueOutOfRangeError

__all__ = ["UnitUtils", "UnitTools"]

logger = logging.getLogger("pocketutils")


class LazyPint:
    def __init__(self):
        self.__unit_reg = None
        self.__Quantity = None

    @property
    def quantity(self):
        self.__get()
        return self.__Quantity

    @property
    def unit_reg(self):
        self.__get()
        return self.__unit_reg

    def __get(self) -> None:
        if self.__Quantity is None:
            from pint import UnitRegistry

            self.__unit_reg = UnitRegistry()
            self.__Quantity = self.__unit_reg.Quantity
            # Silence NEP 18 warning
            # with warnings.catch_warnings():
            #    warnings.simplefilter("ignore")
            #    Quantity([])


_LAZY_PINT = LazyPint()


@dataclass(slots=True, frozen=True)
class UnitUtils:
    def pint_quantity(self: Self, value: SupportsFloat, unit: str):
        """
        Returns a pint `Quantity`.
        """
        return _LAZY_PINT.quantity(value, unit)

    def format_approx_big_number(self: Self, n: int) -> str:
        for k, v in {1e15: "", 1e12: "T", 1e9: "B", 1e6: "M", 1e3: "k"}.items():
            if n >= k:
                return str(n // k) + v
        return str(n)

    def approx_time_wrt(
        self: Self,
        now: date | datetime,
        then: date | datetime,
        *,
        no_date_if_today: bool = False,
        higher_unit_factor: int = 2,
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
        tot_days = delta.days + (delta.seconds / 86400) + (delta.microseconds / 86400 / 10**6)
        tot_secs = tot_days * 86400
        _today = "" if no_date_if_today and then.date() == now.date() else "%Y-%m-%d "
        if tot_days > higher_unit_factor * 365.24219:
            return str(then.year)
        elif tot_days > higher_unit_factor * 30.437:
            return then.strftime("%Y-%m")
        elif tot_days > higher_unit_factor:
            return then.strftime("%Y-%m-%d")
        elif tot_secs > higher_unit_factor * 60:
            return then.strftime(_today + "%H:%M")
        elif tot_secs > higher_unit_factor:
            return then.strftime(_today + "%H:%M:%S")
        elif tot_secs > higher_unit_factor / 1000:
            return then.strftime(_today + "%H:%M:%S") + "." + str(round(then.microsecond / 1000))
        return then.strftime(_today + "%H:%M:%S.%f")

    def pretty_timedelta(self: Self, delta: timedelta | float, *, space: str = "") -> str:
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
        if isinstance(delta, timedelta):
            delta_sec = delta.total_seconds()
        else:
            delta_sec = delta
        if abs(delta_sec) > 60 * 60 * 3:
            return str(round(delta_sec / 60 / 60, 2)).removesuffix(".0") + space + "hr"
        elif abs(delta_sec) > 180:
            return str(round(delta_sec / 60, 2)).removesuffix(".0") + space + "min"
        return str(round(delta_sec, 1)).removesuffix(".0") + space + "s"

    def milliseconds_to_min_sec(self: Self, ms: int, space: str = "", minus: str = "-") -> str:
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
                   good choices are empty, ASCII space, `Chars.narrownbsp`, `Chars.thinspace`, and `Chars.nbsp`.
            minus: Minus sign symbol

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
        sgn = minus if ms < 0 else ""
        if ms < 1000:
            return f"{sgn}{ms}{space}ms"
        elif days > 1:
            return f"{days}d:{z_hr}:{z_min}:{z_sec}"
        elif hours > 1:
            return f"{sgn}{z_hr}:{z_min}:{z_sec}"
        else:
            return f"{sgn}{z_min}:{z_sec}"

    def round_to_sigfigs(self: Self, num: SupportsFloat, n_sigfigs: int | None) -> float:
        """
        Round to specified number of sigfigs.

        Args:
            num: Floating-point number to round
            n_sigfigs: The number of significant figures, non-negative

        Returns:
            A Python integer
        """
        if n_sigfigs is None:
            return float(num)
        if n_sigfigs < 0:
            msg = f"sig_figs {n_sigfigs} is negative"
            raise ValueOutOfRangeError(msg, value=num, minimum=0)
        num = float(num)
        if num != 0:
            digits = -int(math.floor(math.log10(abs(num))) - (n_sigfigs - 1))
            return round(num, digits)
        return 0  # can't take the log of 0

    def format_pint_quantity(
        self: Self,
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
        value = self.round_to_sigfigs(value, n_sigfigs)
        dimmed = value * getattr(_LAZY_PINT.unit_reg, unit)
        return f"{dimmed:~}" + space + unit


UnitTools = UnitUtils()
