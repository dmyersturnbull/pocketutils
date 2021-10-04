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
from pocketutils.core.exceptions import IllegalPathError, XFileExistsError, XValueError
from pocketutils.tools.common_tools import CommonTools
from pocketutils.tools.path_tools import PathTools

FigureSeqLike = Union[Figure, Iterator[Figure], Iterator[Tup[str, Figure]], Mapping[str, Figure]]
KNOWN_EXTENSIONS = ["jpg", "png", "pdf", "svg", "eps", "ps"]
logger = logging.getLogger("pocketutils")


class FigureSaver:
    """
    Offers some small, specific extensions over matplotlib's ``figure.savefig``:
    - can remove the figure from memory each iteration
    - creates directories as needed
    - can save a multi-figure PDF
    - complains about issues
    - can auto-fix some
    - the ``FigureSaver.save`` function handles iterators of different types

    See ``FigureSaver.save`` for more info.
    ``clear`` defines the behavior after saving a single figure:
        - False    ==> do nothing
        - True     ==> clear it
        - callable ==> call it with the Figure instance

    """

    def __init__(
        self,
        save_under: Optional[PathLike] = None,
        *,
        clear: Union[bool, Callable[[Figure], Any]] = False,
        as_type: Optional[str] = None,
        check_paths: bool = True,
        sanitize_paths: bool = True,
        log: Optional[Callable[[str], None]] = None,
        kwargs: Mapping[str, Any] = None,
    ):
        """
        Constructor.

        Args:
            save_under: A parent directory assumed for all saved figures
            clear: Auto-close each figure after saving
            as_type: Force a specific filename suffix (e.g. ``as_type=".jpg")``
            check_paths: Check that paths are valid; without ``sanitize_paths``,
                         raises an error if a path is invalid
            sanitize_paths: Try to sanitize paths (implies ``check_paths``)
            log: Call this function with a message indicating that a sanitized path differs
            kwargs: Passed to ``savefig``
        """
        self._save_under = None if save_under is None else Path(save_under)
        if clear is not None and not isinstance(clear, bool) and not callable(clear):
            raise TypeError(type(clear))
        self._clear = clear
        self._log = lambda _: None if log is None else log
        self._as_type = "." + as_type.lstrip(".")
        self._check_paths = check_paths
        self._sanitize_paths = sanitize_paths
        self._kwargs = {} if kwargs is None else kwargs

    def __mod__(self, tup):
        """
        See: :meth:`save_one`.
        """
        self.save_one(*tup)

    def __idiv__(self, tup):
        """
        See: :meth:`save`.
        """
        self.save(*tup)

    def save(
        self,
        figure: FigureSeqLike,
        path: PathLike = "",
        names: Optional[Iterator[str]] = None,
        *,
        overwrite: bool = True,
        use_labels: bool = False,
    ) -> None:
        """
        Saves either:
            1. a single figure ``figure`` to path ``path``
            2. a bunch of figures to directory ``path``
               if ``figure`` is an iterable (list, dict, etc) over figures
            3. a single PDF with multiple figures, if ``path`` ends in ``.pdf``

        If ``figure`` is iterable (case 2), it can be either:
            - an iterable over Figures
            - an iterable over (name, Figure) pairs, where ``name`` provides the filename
              (under the directory ``path``)

        If it's the first case and ``names`` is set, will use those to provide the filenames.
        Otherwise, falls back to numbering them (ex: ``directory/1.png``, etc).

        If ``use_labels`` is set, tries to use each ``Figure.get_label()``.

        .. note ::
            Figure labels are not typically set by default;
            you should call ``Figure.set_label()`` when using ``use_labels``.
        """
        is_iterable = CommonTools.is_true_iterable(figure)
        if is_iterable and path.endswith(".pdf"):
            self.save_all_as_pdf(figure, path, names=names)
        elif is_iterable:
            self.save_all(figure, path, names=names, use_labels=use_labels, overwrite=overwrite)
        else:
            self.save_one(figure, path, overwrite=overwrite)

    def save_all_as_pdf(
        self,
        figures: FigureSeqLike,
        path: PathLike,
        names: Optional[Iterator[str]] = None,
        *,
        overwrite: bool = True,
        metadata: Optional[Mapping[str, str]] = None,
    ) -> None:
        """
        Save a single PDF with potentially many figures.
        See :meth:`save` for more info.
        """
        # note! this is weird
        if plt.rcParams["pdf.fonttype"] != 42:
            warn("pdf.fonttype != 42. This may cause problems.")
        cp = copy(self)
        cp._as_type = ".pdf"
        path = cp._sanitized_file(path, overwrite=overwrite)
        done_figures = []
        with PdfPages(str(path), keep_empty=False, metadata=metadata) as pdf:
            for name, figure in self._enumerate(figures, names, use_labels=False):
                pdf.savefig(figure, **self._kwargs)
                done_figures.append(figure)
        # TODO can I clear every time?
        for figure in done_figures:
            self._clean_up(figure)

    def save_all(
        self,
        figures: FigureSeqLike,
        directory: PathLike = ".",
        names: Optional[Iterator[str]] = None,
        *,
        use_labels: bool = False,
        overwrite: bool = True,
    ) -> None:
        """
        Saves potentially multiple figures into a directory.

        See :meth:`save` for more info.
        """
        for name, figure in self._enumerate(figures, names, use_labels=use_labels):
            # DO NOT prepend self.__save_under here!! It's done in save_one.
            path = Path(directory) / name
            self.save_one(figure, path, overwrite=overwrite)  # clears if needed

    def save_one(self, figure: Figure, path: PathLike, overwrite: bool) -> None:
        """
        Saves one figure to a specific path.
        This is pretty similar to ``Figure.savefig``.
        """
        path = self._sanitized_file(path, overwrite=overwrite)
        figure.savefig(path, **self._kwargs)
        self._clean_up(figure)

    def _enumerate(
        self,
        figures,
        names: Optional[Sequence[str]],
        *,
        use_labels: bool,
    ) -> Generator[Tup[str, Figure], None, None]:
        if isinstance(figures, Mapping):
            figures = figures.items()
        for i, figure in enumerate(figures):
            if names is not None:
                yield next(names), figure
            elif isinstance(figure, tuple):
                yield figure[0], figure[1]
            elif use_labels and figure.get_label() is not None:
                yield figure.get_label(), figure
            elif use_labels:
                raise ValueError("use_labels=True, but no names given and a figure has no label")
            else:
                yield str(i), figure

    def _clean_up(self, figure: Figure) -> None:
        if self._clear is None:
            pass
        elif self._clear is True:
            pass
            figure.clear()
            figure.clf()
        elif callable(self._clear):
            self._clear(figure)

    def _sanitized_file(self, path: PathLike, overwrite: bool) -> Path:
        """
        Sanitizes a file path:
            - prepends self._save_under if needed
            - warns about issues

        Args:
            path: The path, including directory, but excluding self._save_under
        """
        path = Path(path)
        if self._check_paths or self._sanitize_paths:
            new_path = PathTools.sanitize_path(path, show_warnings=False)
            if new_path != path and self._sanitize_paths:
                self._log(f"Sanitized filename {path} → {new_path}")
            elif new_path != path:
                raise IllegalPathError(
                    f"Filename {path} is not valid (could be: {new_path})", path=path
                )
        if self._save_under is not None and Path(path).is_absolute():
            raise XValueError(f"_save_under is {self._save_under} but path {path} is absolute")
        elif self._save_under is not None:
            path = self._save_under / path
        ext_valid = any((str(path).endswith("." + s) for s in KNOWN_EXTENSIONS))
        # can't just detect no suffix, because 12.5uM will have suffix 5uM
        # also, don't use with_suffix for this same reason
        if not ext_valid:
            pt = "." + plt.rcParams["savefig.format"] if self._as_type is None else self._as_type
            path = Path(str(path) + pt)
        path = Path(path)
        if path.exists() and not overwrite:
            raise XFileExistsError(f"{path} already exists", path=path)
        path.parent.mkdir(exist_ok=True, parents=True)
        logger.debug(path)
        return path


__all__ = ["FigureSaver"]
