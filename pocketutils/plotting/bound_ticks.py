from dataclasses import dataclass
from typing import Union

from matplotlib.axes import Axes
from matplotlib.axis import Axis


@dataclass(frozen=True, repr=True, order=True)
class Coords:
    x0: float
    x1: float
    y0: float
    y1: float


@dataclass(frozen=True, repr=True, order=True)
class TickBounder:
    """
    Forces Axes limits to start and/or end at major or minor ticks.

    Each argument in the constructor can be:
    - ``True`` -- set the bound according to the ticks
    - ``False`` -- do not change the bound
    - a ``float`` - set to this

    Args:
        x0: left bound (``.getxlim()[0]``)
        y0: bottom bound (``.getylim()[0]``)
        x1: right bound (``.getxlim()[1]``)
        y1: top bound (``.getylim()[1]``)
        major: Use major tick marks rather than minor

    Example:
        This example will bound maximum width and height of the Axes
        to the smallest tick that fits the data,
        and will set the minimum width and height to 0::

            ticker = TickBounder(x=0, y0=0, x1=True, y1=True)
            ticker.adjust(ax)
    """

    x0: Union[bool, float] = True
    y0: Union[bool, float] = True
    x1: Union[bool, float] = True
    y1: Union[bool, float] = True
    major: bool = True

    def adjust(self, ax: Axes) -> Axes:
        coords = self.adjusted(ax)
        ax.set_xlim(coords.x0, coords.x1)
        ax.set_ylim(coords.y0, coords.y1)
        return ax

    def adjusted(self, ax: Axes) -> Coords:
        return Coords(
            x0=self._adjust(ax.xaxis, self.x0, ax.get_xlim()[0], 0),
            x1=self._adjust(ax.xaxis, self.x0, ax.get_xlim()[1], 1),
            y0=self._adjust(ax.yaxis, self.y0, ax.get_ylim()[0], 0),
            y1=self._adjust(ax.yaxis, self.y0, ax.get_ylim()[1], 1),
        )

    def _adjust(self, ax: Axis, to: Union[bool, float], default: float, side: int) -> float:
        if to is False:
            return default
        try:
            return float(to)
        except ValueError:
            pass
        vals = ax.get_majorticklocs() if self.major else ax.get_minorticklocs()
        return vals[side]


__all__ = ["TickBounder", "Coords"]
