import typing
from dataclasses import dataclass
from typing import Optional

import numpy as np
from matplotlib.axes import Axes


def _oround(x: float, digits: Optional[int] = None) -> float:
    return x if digits is None else round(x, digits)


@dataclass(frozen=True, repr=True, order=True)
class AxisTicks:
    """
    Calculates new bounds for an axis based on the ticks.

    Attributes:
         floor: If None, sets the minimum bound based on the data
         ceiling: If None, sets the maximum bound based on the data
         rounding_digits: Minor argument that rounds the final bounds to some number of digits
    """

    floor: Optional[float] = None
    ceiling: Optional[float] = None
    rounding_digits: Optional[float] = None

    def __str__(self) -> str:
        return "ticks({}, {})".format(
            "min" if self.floor is None else round(self.floor, 5),
            "max" if self.ceiling is None else round(self.ceiling, 5),
        )

    def adjusted(self, ticks: np.array, bottom: float, top: float) -> typing.Tuple[float, float]:
        if len(ticks) < 2:
            return bottom, top
        floor = ticks[0] if self.floor is None else self.floor
        ceiling = ticks[-1] if self.ceiling is None else self.ceiling
        return (
            _oround(floor, self.rounding_digits),
            _oround(ceiling, self.rounding_digits),
        )


@dataclass(frozen=True, repr=True, order=True)
class TickBounder:
    """
    Forces the limits of a Matplotlib Axes to end at major or minor ticks.
    Pass AxisTicks as the x_ticks and y_ticks constructor arguments to perform this.

    This example will bound maximum width and height of the Axes to the smallest tick that fits the data,
    and will set the minimum width and height to 0.

    Example:
        For example::

            ticker = TickBounder(x_ticks = AxisTicks(floor=0), y_ticks = AxisTicks(floor=0))
            ticker.adjust(ax)

        You can see the proposed new bound without changing the Axes using::

            ticker.adjusted(ax)  # returns a ((x0, x1), (y0, y1)) tuple
    """

    x_ticks: Optional[AxisTicks] = None
    y_ticks: Optional[AxisTicks] = None
    use_major_ticks: bool = True

    def adjust(self, ax: Axes) -> Axes:
        x_adj, y_adj = self.adjusted(ax)
        ax.set_xlim(*x_adj)
        ax.set_ylim(*y_adj)
        return ax

    def adjusted(
        self, ax: Axes
    ) -> typing.Tuple[typing.Tuple[float, float], typing.Tuple[float, float]]:
        xmin, xmax, ymin, ymax = (
            list(ax.get_xlim())[0],
            list(ax.get_xlim())[1],
            list(ax.get_ylim())[0],
            list(ax.get_ylim())[1],
        )
        xs = ax.xaxis.get_majorticklocs() if self.use_major_ticks else ax.get_xticks()
        ys = ax.yaxis.get_majorticklocs() if self.use_major_ticks else ax.get_yticks()
        return (
            (xmin, xmax) if self.x_ticks is None else self.x_ticks.adjusted(xs, xmin, xmax),
            (ymin, ymax) if self.y_ticks is None else self.y_ticks.adjusted(ys, ymin, ymax),
        )


__all__ = ["AxisTicks", "TickBounder"]
