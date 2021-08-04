from __future__ import annotations

import logging
from contextlib import contextmanager
from copy import copy
from pathlib import Path
from typing import Callable, Generator, Iterator, Mapping, Optional, Sequence, Iterable
from typing import Tuple as Tup
from typing import Union

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import colors as mcolors
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from pocketutils.plotting.corners import Corner
from pocketutils.tools.common_tools import CommonTools

FigureSeqLike = Union[Figure, Iterator[Figure], Iterator[Tup[str, Figure]], Mapping[str, Figure]]
KNOWN_EXTENSIONS = ["jpg", "png", "pdf", "svg", "eps", "ps"]
logger = logging.getLogger("pocketutils")


class FigureTools:
    @classmethod
    def cm2in(cls, tup: Union[float, Iterable[float]]):
        """
        Just converts centimeters to inches.

        Args:
            tup: A float or sequence of floats (determines the return type)
        """
        if CommonTools.is_true_iterable(tup):
            return [x / 2.54 for x in tup]
        else:
            return float(tup) / 2.54

    @classmethod
    def in2cm(cls, tup: Union[float, Iterable[float]]):
        """
        Just converts inches to centimeters.

        Args:
            tup: A float or sequence of floats (determines the return type)
        """
        if CommonTools.is_true_iterable(tup):
            return [x * 2.54 for x in tup]
        else:
            return float(tup) * 2.54

    @classmethod
    def open_figs(cls) -> Sequence[Figure]:
        """
        Returns all currently open figures.
        """
        return [plt.figure(num=i) for i in plt.get_fignums()]

    @classmethod
    def open_fig_map(cls) -> Mapping[str, Figure]:
        """
        Returns all currently open figures as a dict mapping their labels `Figure.label` to their instances.
        Note that `Figure.label` is often empty in practice.

        Args:

        Returns:

        """
        return {label: plt.figure(label=label) for label in plt.get_figlabels()}

    @classmethod
    @contextmanager
    def clearing(cls, yes: bool = True) -> Generator[None, None, None]:
        """
        Context manager to clear and close all figures created during its lifespan.
        When the context manager exits, calls `clf` and `close` on all figures created under it.

        Args:
            yes: If False, does nothing

        Yields:

        """
        oldfigs = copy(plt.get_fignums())
        yield
        if yes:
            for fig in [plt.figure(num=i) for i in plt.get_fignums() if i not in oldfigs]:
                fig.clf()
                plt.close(fig)

    @classmethod
    @contextmanager
    def hiding(cls, yes: bool = True) -> Generator[None, None, None]:
        """
        Context manager to hide figure display by setting `plt.interactive(False)`.

        Args:
            yes: If False, does nothing

        Yields:

        """
        isint = plt.isinteractive()
        if yes:
            plt.interactive(False)
        yield
        if yes:
            plt.interactive(isint)

    @classmethod
    def plot1d(
        cls,
        values: np.array,
        figsize: Optional[Tup[float, float]] = None,
        x0=None,
        y0=None,
        x1=None,
        y1=None,
        **kwargs,
    ) -> Axes:
        """
        Plots a 1D array and returns the axes.
        kwargs are passed to `Axes.plot`.

        Args:
            values: np.array:
            figsize:
            x0:  (Default value = None)
            y0:  (Default value = None)
            x1:  (Default value = None)
            y1:  (Default value = None)
            **kwargs:

        Returns:

        """
        figure = plt.figure(figsize=figsize)
        ax = figure.add_subplot(1, 1, 1)  # Axes
        ax.plot(values, **kwargs)
        ax.set_xlim((x0, x1))
        ax.set_ylim((y0, y1))
        return ax

    @classmethod
    def despine(cls, ax: Axes) -> Axes:
        """
        Removes all spines and ticks on an Axes.

        Args:
            ax: Axes:

        Returns:

        """
        ax.set_yticks([])
        ax.set_yticks([])
        ax.set_xticklabels([])
        ax.set_yticklabels([])
        ax.spines["top"].set_visible(False)
        ax.spines["bottom"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_visible(False)
        ax.get_xaxis().set_ticks([])
        ax.get_yaxis().set_ticks([])
        return ax

    @classmethod
    def clear(cls) -> int:
        """
        Removes all matplotlib figures from memory.
        Here because it's confusing to remember.
        Logs an error if not all figures were closed.

        Returns:
            The number of closed figures

        """
        n = len(plt.get_fignums())
        plt.clf()
        plt.close("all")
        m = len(plt.get_fignums())
        if m == 0:
            logger.debug(f"Cleared {n} figure{'s' if n>1 else ''}.")
        else:
            logger.error(f"Failed to close figures. Cleared {n - m}; {m} remain.")
        return n

    @classmethod
    def font_paths(cls) -> Sequence[Path]:
        """
        Returns the paths of system fonts.
        """
        # noinspection PyUnresolvedReferences
        return [Path(p) for p in matplotlib.font_manager.findSystemFonts(fontpaths=None)]

    @classmethod
    def text_matrix(
        cls,
        ax: Axes,
        data: pd.DataFrame,
        color_fn: Optional[Callable[[str], str]] = None,
        adjust_x: float = 0,
        adjust_y: float = 0,
        **kwargs,
    ) -> None:
        """
        Adds a matrix of text.

        Args:
            ax: Axes
            data: The matrix of any text values; will be converted to strings and empty strings will be ignored
            color_fn: An optional function mapping (pre-conversion-to-str) values to colors
            adjust_x: Add this value to the x coordinates
            adjust_y: Add this value to the y coordinates
            **kwargs: Passed to `ax.text`

        """
        for r, row in enumerate(data.index):
            for c, col in enumerate(data.columns):
                value = data.iat[r, c]
                if str(value) != "":
                    ax.text(
                        r + adjust_x,
                        c + adjust_y,
                        str(value),
                        color=None if color_fn is None else color_fn(value),
                        **kwargs,
                    )

    @classmethod
    def add_note_01_coords(cls, ax: Axes, x: float, y: float, s: str, **kwargs) -> Axes:
        """
        Adds text without a box, using chemfish_rc['general_note_font_size'] (unless overridden in kwargs).
        ``x`` and ``y`` are in coordinates (0, 1).

        Args:
            ax: Axes:
            x: float:
            y: float:
            s: str:
            **kwargs:

        Returns:

        """
        t = ax.text(x, y, s=s, transform=ax.transAxes, **kwargs)
        t.set_bbox(dict(alpha=0.0))
        return ax

    @classmethod
    def add_note_data_coords(cls, ax: Axes, x: float, y: float, s: str, **kwargs) -> Axes:
        """
        Adds text without a box, using chemfish_rc['general_note_font_size'] (unless overridden in kwargs).
        ``x`` and ``y`` are in data coordinates.

        Args:
            ax: Axes:
            x: float:
            y: float:
            s: str:
            **kwargs:

        Returns:

        """
        t = ax.text(x, y, s=s, **kwargs)
        t.set_bbox(dict(alpha=0.0))
        return ax

    @classmethod
    def stamp(cls, ax: Axes, text: str, corner: Corner, **kwargs) -> Axes:
        """
        Adds a "stamp" in the corner.

        Example:
            Stamping::

                FigureTools.stamp(ax, 'hello', Corners.TOP_RIGHT)

        Args:
            ax: Axes:
            text: str:
            corner: Corner:
            **kwargs:

        Returns:

        """
        return cls._text(ax, text, corner, **kwargs)

    @classmethod
    def _text(cls, ax: Axes, text: str, corner: Corner, **kwargs) -> Axes:
        """


        Args:
            ax: Axes:
            text: str:
            corner: Corner:
            **kwargs:

        Returns:

        """
        t = ax.text(s=text, **corner.params(), transform=ax.transAxes, **kwargs)
        t.set_bbox(dict(alpha=0.0))
        return ax

    @classmethod
    def plot_palette(cls, values: Union[Sequence[str], str]) -> Figure:
        """
        Plots a color palette.

        Args:
            values: A string of a color (starting with #), a sequence of colors (each starting with #)

        Returns:

        """
        n = len(values)
        figure = plt.figure(figsize=(8.0, 2.0))
        ax = figure.add_subplot(1, 1, 1)
        ax.imshow(
            np.arange(n).reshape(1, n),
            cmap=mcolors.ListedColormap(values),
            interpolation="none",
            aspect="auto",
        )
        cls.despine(ax)
        return figure


__all__ = ["FigureTools"]
