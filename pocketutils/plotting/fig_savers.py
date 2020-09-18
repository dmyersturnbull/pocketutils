from __future__ import annotations

import logging
from copy import copy
from pathlib import Path
from typing import Any, Callable, Generator, Iterator, Mapping, Optional, Sequence
from typing import Tuple as Tup
from typing import Union
from warnings import warn

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.figure import Figure

from pocketutils.core import PathLike

# these have no extra dependencies
from pocketutils.tools.common_tools import CommonTools
from pocketutils.tools.path_tools import PathTools

FigureSeqLike = Union[Figure, Iterator[Figure], Iterator[Tup[str, Figure]], Mapping[str, Figure]]
KNOWN_EXTENSIONS = ["jpg", "png", "pdf", "svg", "eps", "ps"]
logger = logging.getLogger("pocketutils")


class FigureSaver:
    """
    Offers some small, specific extensions over matplotlib's ``figure.savefig``:
    - can remove the figure from memory on each iteration
    - creates directories as needed
    - can save a multi-figure PDF
    - complains about issues
    - the ``FigureSaver.save`` function handles iterators of different types.

    See ``FigureSaver.save`` for more info.
    ``clear`` defines the behavior after saving a single figure:
        - False    ==> do nothing
        - True     ==> clear it
        - callable ==> call it with the Figure instance

    """

    def __init__(
        self,
        save_under: Optional[PathLike] = None,
        clear: Union[bool, Callable[[Figure], Any]] = False,
        warnings: bool = True,
        as_type: Optional[str] = None,
        kwargs: Mapping[str, Any] = None,
    ):
        """

        Args:
            save_under:
            clear:
            warnings:
            as_type:
            kwargs:
        """
        self._save_under = None if save_under is None else Path(save_under)
        if clear is not None and not isinstance(clear, bool) and not callable(clear):
            raise TypeError(type(clear))
        self._clear = clear
        self._warnings = warnings
        if as_type is not None and not as_type.startswith("."):
            as_type = "." + as_type
        self._as_type = as_type
        self._kwargs = {} if kwargs is None else kwargs

    def __mod__(self, tup):
        """

        Args:
            tup:
        """
        self.save_one(*tup)

    def __idiv__(self, tup):
        """

        Args:
            tup:
        """
        self.save(*tup)

    def save(
        self, figure: FigureSeqLike, path: PathLike = "", names: Optional[Iterator[str]] = None
    ) -> None:
        """
        Saves either:
            1. a single figure ``figure`` to path ``path``
            2. a bunch of figures to directory ``path`` if ``figure`` is an iterable (list, dict, etc) over figures
            3. a single PDF with multiple figures, if ``path`` ends in ``.pdf``

        If ``figure`` is iterable (case 2), it can be either:
            - an iterable over Figures
            - an iterable over (name, Figure) pairs, where `name` is a string that provides the filename
              (under the directory ``path``)

        If it's the first case and ``names`` is set, will use those to provide the filenames.
        Otherwise, falls back to numbering them (ex: ``directory/1.png``, etc)

        Args:
            figure: FigureSeqLike:
            path:
            names:

        """
        is_iterable = CommonTools.is_true_iterable(figure)
        if is_iterable and path.endswith(".pdf"):
            self.save_all_as_pdf(figure, path, names=names)
        elif is_iterable:
            self.save_all(figure, path, names=names)
        else:
            self.save_one(figure, path)

    def save_all_as_pdf(
        self, figures: FigureSeqLike, path: PathLike, names: Optional[Iterator[str]] = None
    ) -> None:
        """
        Save a single PDF with potentially many figures.

        Args:
            figures: FigureSeqLike:
            path: PathLike:
            names:

        """
        # note! this is weird
        if plt.rcParams["pdf.fonttype"] != 42:
            warn("pdf.fonttype != 42. This may cause problems.")
        cp = copy(self)
        cp._as_type = ".pdf"
        path = cp._sanitized_file(path)
        with PdfPages(str(path)) as pdf:
            for name, figure in self._enumerate(figures, names):
                pdf.savefig(figure, **self._kwargs)
                # TODO does clearing break this?
                self._clean_up(figure)

    def save_all(
        self,
        figures: FigureSeqLike,
        directory: PathLike = "",
        names: Optional[Iterator[str]] = None,
    ) -> None:
        """


        Args:
            figures:
            directory:
            names:

        """
        for name, figure in self._enumerate(figures, names):
            # DO NOT prepend self.__save_under here!! It's done in save_one.
            path = Path(directory) / PathTools.sanitize_path_node(name, is_file=True)
            self._save_one(figure, path)  # clears if needed

    def save_one(self, figure: Figure, path: PathLike) -> None:
        """


        Args:
            figure:
            path:

        """
        self._save_one(figure, path)

    def _save_one(self, figure: Figure, path: PathLike) -> None:
        """


        Args:
            figure: Figure:
            path: PathLike:

        """
        path = self._sanitized_file(path)
        figure.savefig(path, **self._kwargs)
        self._clean_up(figure)

    def _enumerate(
        self, figures, names: Optional[Sequence[str]]
    ) -> Generator[Tup[str, Figure], None, None]:
        """


        Args:
            figures:
            names:

        Yields:

        """
        if isinstance(figures, Mapping):
            figures = figures.items()
        for i, figure in enumerate(figures):
            if names is not None:
                yield next(names), figure
            elif isinstance(figure, tuple):
                yield figure[0], figure[1]
            else:
                yield str(i), figure

    def _clean_up(self, figure: Figure) -> None:
        """


        Args:
            figure: Figure:

        """
        if self._clear is None:
            pass
        elif self._clear is True:
            pass
            figure.clear()
            figure.clf()
        elif callable(self._clear):
            self._clear(figure)

    def _sanitized_file(self, path: PathLike) -> Path:
        """
        Sanitizes a file path:
            - prepends self._save_under if needed
            - warns about issues

        Args:
            path: The path, including directory, but excluding self._save_under

        Returns:
            The Path

        """
        path = Path(path)
        if self._save_under is not None and Path(path).is_absolute():
            logger.warning(f"_save_under is {self._save_under} but path {path} is absolute")
        elif self._save_under is not None:
            path = self._save_under / path
        ext_valid = any((str(path).endswith("." + s) for s in KNOWN_EXTENSIONS))
        # can't just detect no suffix, because 12.5uM will have suffix 5uM
        # also, don't use with_suffix for this same reason
        if not ext_valid:
            pt = "." + plt.rcParams["savefig.format"] if self._as_type is None else self._as_type
            path = Path(str(path) + pt)
        path = Path(path)
        path.parent.mkdir(exist_ok=True, parents=True)
        logger.debug(path)
        return path


__all__ = ["FigureSaver"]
