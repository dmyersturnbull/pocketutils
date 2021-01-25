import enum
import logging
from pathlib import Path
from typing import Callable, Iterable, Mapping, Optional, Union

from colorama import Fore, Style

from pocketutils.core import PathLike
from pocketutils.core.exceptions import RefusingRequestError
from pocketutils.misc.messages import *
from pocketutils.tools.filesys_tools import FilesysTools

logger = logging.getLogger("pocketutils")


class ColorMessages:
    """

    Example:
        Like this::

            from pocketutils.misc.messages import MessageLevels
            from pocketutils.misc.fancy_console import ColorMessages
            import colorama
            colorama.init(autoreset=True)
            messages = ColorMessages()
            messages.thin(
    """

    @classmethod
    def default_color_map(cls):
        return {
            MsgLevel.INFO: Style.BRIGHT,
            MsgLevel.NOTICE: Fore.BLUE,
            MsgLevel.SUCCESS: Fore.GREEN,
            MsgLevel.WARNING: Fore.MAGENTA,
            MsgLevel.FAILURE: Fore.RED,
        }

    def __init__(
        self,
        color_map: Optional[Mapping[MsgLevel, int]] = None,
        log_fn: Optional[Callable[[str], None]] = None,
        **kwargs,
    ):
        """
        Constructs a new environment for colored console messages.
            color_map: A map from level to colors in colorama to override ColorMessages.DEFAULT_COLOR_MAP
            log_fn: If set, additionally logs every message with this function
            kwargs: Arguments 'top', 'bottom', 'sides', and 'line_length'
        """
        _cmap = ColorMessages.default_color_map()
        if color_map is not None:
            _cmap.update(color_map)
        # TODO
        # assert set(_cmap.keys()) == set(
        #    MsgLevel.__members__.keys()
        # ), "Color map {} must match levels {}".format(_cmap, MsgLevel.__members__)
        self._color_map, self._log_fn, self._kwargs = _cmap, log_fn, kwargs

    def line(self, level: Union[MsgLevel, str], *lines: str):
        print(self._get(level) + "\n".join(lines))

    def thin(self, level: Union[MsgLevel, str], *lines: str):
        self._print(lines, self._get(level), **self._kwargs)

    def thick(self, level: Union[MsgLevel, str], *lines: str):
        self._print(["\n", lines, "\n"], self._get(level), **self._kwargs)

    def _get(self, level: Union[MsgLevel, str]):
        if isinstance(level, str):
            level = MsgLevel[level]
        return self._color_map[level]

    def _print(
        self,
        lines: Iterable[str],
        color: int,
        top: str = "_",
        bottom: str = "_",
        sides: str = "",
        line_length: int = 100,
    ):
        def cl(text: str):
            print(str(color) + sides + text.center(line_length - 2 * len(sides)) + sides)

        print(str(color) + top * line_length)
        self._log(top * line_length)
        for line in lines:
            self._log(line)
            cl(line)
        print(str(color) + bottom * line_length)
        self._log(bottom * line_length)

    def _log(self, message):
        if self._log_fn:
            self._log_fn(message)


class Deletion(enum.Enum):
    NO = 1
    TRASH = 2
    HARD = 3


class DeletePrompter:
    CHOICES = [
        Deletion.NO.name.lower(),
        Deletion.TRASH.name.lower(),
        Deletion.HARD.name.lower(),
    ]

    def __init__(
        self,
        allow_dirs: bool = True,
        notify: bool = True,
        ignorable: bool = True,
        delete_fn: Callable[[PathLike], None] = FilesysTools.delete_surefire,
        trash_fn: Callable[[PathLike], None] = FilesysTools.trash,
        dry: bool = False,
    ):
        self.allow_dirs = allow_dirs
        self.notify, self.allow_ignore = notify, ignorable
        self.delete_fn, self.trash_fn = delete_fn, trash_fn
        self.dry = dry

    def prompt(self, path: PathLike):
        path = Path(path)
        if not self.allow_dirs and path.is_dir():
            raise RefusingRequestError(f"Cannot delete directory {path}; only files are allowed.")
        elif not path.is_dir() and not path.is_file():
            raise RefusingRequestError(
                f"Cannot delete {path}; only files and directories are allowed."
            )
        while True:
            print(
                Fore.BLUE + "Delete? [{}]".format("/".join(DeletePrompter.CHOICES)),
                end="",
            )
            cmdd = input("").strip()
            logger.debug(f"Received user input {cmdd}")
            polled = self._poll(path, cmdd)
            if polled is not None:
                return polled

    def _poll(self, path: Path, command: str) -> Optional[Deletion]:
        # HARD DELETE
        if command.lower() == Deletion.HARD.name.lower():
            if not self.dry:
                self.delete_fn(path)
            if self.notify:
                print(Style.BRIGHT + f"Permanently deleted {path}")
            return Deletion.HARD
        # MOVE TO TRASH
        elif command.lower() == Deletion.TRASH.name.lower():
            if not self.dry:
                self.trash_fn(path)
            if self.notify:
                print(Style.BRIGHT + f"Trashed {path}.")
            return Deletion.TRASH
        # IGNORE
        elif command.lower() == Deletion.NO.name.lower() or len(command) == 0 and self.allow_ignore:
            return Deletion.NO
        # INVALID
        else:
            print(Fore.RED + "Enter " + " or ".join(DeletePrompter.CHOICES))
            return None


__all__ = ["ColorMessages", "DeletePrompter"]
