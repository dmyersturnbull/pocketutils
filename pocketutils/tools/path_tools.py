import sys
from typing import Callable, Optional, Sequence

import regex

from pocketutils.core.exceptions import *
from pocketutils.tools.base_tools import BaseTools

logger = logging.getLogger("pocketutils")


class PathTools(BaseTools):
    @classmethod
    def updir(cls, n: int, *parts) -> Path:
        """
        Get an absolute path ``n`` parents from ``os.getcwd()``.
        Does not sanitize.

        Ex: In dir '/home/john/dir_a/dir_b':
            updir(2, 'dir1', 'dir2')  # returns Path('/home/john/dir1/dir2')
        """
        base = Path(os.getcwd())
        for _ in range(n):
            base = base.parent
        for part in parts:
            base = base / part
        return base.resolve()

    @classmethod
    def guess_trash(cls) -> Path:
        """
        Chooses a reasonable path for trash based on the OS.
        This is not reliable. For a more sophisticated solution,
        see https://github.com/hsoft/send2trash
        However, even that can fail.
        """
        plat = sys.platform.lower()
        if "darwin" in plat:
            return Path.home() / ".Trash"
        elif "win" in plat:
            return Path(Path.home().root) / "$Recycle.Bin"
        else:
            return Path.home() / ".trash"

    @classmethod
    def sanitize_path(
        cls,
        path: PathLike,
        *,
        is_file: Optional[bool] = None,
        fat: bool = False,
        trim: bool = False,
        warn: Union[bool, Callable[[str], Any]] = True,
    ) -> Path:
        r"""
        Sanitizes a path for major OSes and filesystems.
        Also see sanitize_path_nodes and sanitize_path_node.
        Mostly platform-independent.

        The idea is to sanitize for both Windows and Posix, regardless of the platform in use.
        The sanitization should be as uniform as possible for both platforms.
        This works for at least Windows+NTFS.
        Tilde substitution for long filenames in Windows is unsupported.

        A corner case is drive letters in Linux:
        "C:\\Users\\john" is converted to '/C:/users/john' if os.name=='posix'
        """
        w = {True: logger.warning, False: lambda _: None}.get(warn, warn)
        path = str(path)
        if path.startswith("\\\\?"):
            raise IllegalPathError(
                f"Long UNC Windows paths (\\\\? prefix) are not supported (path '{path}')"
            )
        bits = str(path).strip().replace("\\", "/").split("/")
        new_nodes = list(cls.sanitize_nodes(bits, is_file=is_file, fat=fat, trim=trim))
        # unfortunately POSIX turns Path('C:\', '5') into C:\/5
        # this isn't an ideal way to fix it, but it works
        pat = regex.compile(r"^([A-Z]:)(?:\\)?$", flags=regex.V1)
        if os.name == "posix" and len(new_nodes) > 0 and pat.fullmatch(new_nodes[0]):
            new_nodes[0] = new_nodes[0].rstrip("\\")
            new_nodes.insert(0, "/")
        new_path = Path(*new_nodes)
        if new_path != path:
            w(f"Sanitized filename {path} → {new_path}")
        return Path(new_path)

    @classmethod
    def sanitize_nodes(
        cls,
        bits: Sequence[PathLike],
        *,
        is_file: Optional[bool] = None,
        fat: bool = False,
        trim: bool = False,
    ) -> Sequence[str]:
        fixed_bits = [
            bit + os.sep
            if i == 0 and bit.strip() in ["", ".", ".."]
            else cls.sanitize_node(
                bit,
                is_file=(False if i < len(bits) - 1 else is_file),
                trim=trim,
                fat=fat,
                is_root_or_drive=(None if i == 0 else False),
            )
            for i, bit in enumerate(bits)
            if bit.strip() not in ["", "."]
            or i == 0  # ignore // (empty) just like Path does (but fail on sanitize_path_node(' '))
        ]
        return [bit for i, bit in enumerate(fixed_bits) if i == 0 or bit not in ["", "."]]

    @classmethod
    def sanitize_node(
        cls,
        bit: PathLike,
        *,
        is_file: Optional[bool] = None,
        is_root_or_drive: Optional[bool] = None,
        fat: bool = False,
        trim: bool = False,
    ) -> str:
        r"""
        Sanitizes a path node such that it will be fine for major OSes and filesystems.
        For example:
        - 'plums;and/or;apples' becomes 'plums_and_or_apples' (escaped ; and /)
        - 'null.txt' becomes '_null_.txt' ('null' is forbidden in Windows)
        - 'abc  ' becomes 'abc' (no trailing spaces)
        The behavior is platform-independent -- os, sys, and pathlib are not used.
        For ex, calling sanitize_path_node(r'C:\') returns r'C:\' on both Windows and Linux
        If you want to sanitize a whole path, see sanitize_path instead.

        Args:
            bit: The node
            is_file: False for directories, True otherwise, None if unknown
            is_root_or_drive: True if known to be the root ('/') or a drive ('C:\'), None if unknown
            fat: Also make compatible with FAT filesystems
            trim: Truncate to 254 chars (otherwise fails)

        Returns:
            A string
        """
        # since is_file and is_root_or_drive are both Optional[bool], let's be explicit and use 'is' for clarity
        if is_file is True and is_root_or_drive is True:
            raise ContradictoryRequestError("is_file and is_root_or_drive are both true")
        if is_file is True and is_root_or_drive is None:
            is_root_or_drive = False
        if is_root_or_drive is True and is_file is None:
            is_file = False
        source_bit = copy(str(bit))
        bit = str(bit).strip()
        # first, catch root or drive as long as is_root_or_drive is not false
        # if is_root_or_drive is True (which is a weird call), then fail if it's not
        # otherwise, it's not a root or drive letter, so keep going
        if is_root_or_drive is not False:
            # \ is allowed in Windows
            if bit in ["/", "\\"]:
                return bit
            m = regex.compile(r"^([A-Z]:)(?:\\)?$", flags=regex.V1).fullmatch(bit)
            # this is interesting
            # for bit=='C:' and is_root_or_drive=None,
            # it could be either a drive letter
            # or a file path that should be corrected to 'C_'
            # I guess here we're going with a drive letter
            if m is not None:
                # we need C:\ and not C: because:
                # Path('C:\\', '5').is_absolute() is True
                # but Path('C:', '5').is_absolute() is False
                # unfortunately, doing Path('C:\\', '5') on Linux gives 'C:\\/5'
                # I can't handle that here, but sanitize_path() will account for it
                return m.group(1) + "\\"
            if is_root_or_drive is True:
                raise IllegalPathError(f"Node '{bit}' is not the root or a drive letter")
        # note that we can't call WindowsPath.is_reserved because it can't be instantiated on non-Linux
        # also, these appear to be different from the ones defined there
        bad_chars = {
            "<",
            ">",
            ":",
            '"',
            "|",
            "?",
            "*",
            "\\",
            "/",
            *{chr(c) for c in range(128, 128 + 33)},
            *{chr(c) for c in range(0, 32)},
            "\t",
        }
        # don't handle Long UNC paths
        # also cannot be blank or whitespace
        # the $ suffixed ones are for FAT
        # no CLOCK$, even with an ext
        # also no SCREEN$
        bad_strs = {
            "CON",
            "PRN",
            "AUX",
            "NUL",
            "COM1",
            "COM2",
            "COM3",
            "COM4",
            "COM5",
            "COM6",
            "COM7",
            "COM8",
            "COM9",
            "LPT1",
            "LPT2",
            "LPT3",
            "LPT4",
            "LPT5",
            "LPT6",
            "LPT7",
            "LPT8",
            "LPT9",
        }
        if fat:
            bad_strs += {"$IDLE$", "CONFIG$", "KEYBD$", "SCREEN$", "CLOCK$", "LST"}
        # just dots is invalid
        if set(bit.replace(" ", "")) == "." and bit not in ["..", "."]:
            bit = "_" + bit + "_"
            # raise IllegalPathError(f"Node '{source_bit}' is invalid")
        for q in bad_chars:
            bit = bit.replace(q, "_")
        if bit.upper() in bad_strs:
            # arbitrary decision
            bit = "_" + bit + "_"
        else:
            stub, ext = os.path.splitext(bit)
            if stub.upper() in bad_strs:
                bit = "_" + stub + "_" + ext
        if bit.strip() == "":
            bit = "_" + bit + "_"
            # raise IllegalPathError(f"Node '{source_bit}' is empty or contains only whitespace")
        # "." cannot end a node
        bit = bit.rstrip()
        if is_file is not True and (bit == "." or bit == ".."):
            return bit
        # never allow '.' or ' ' to end a filename
        bit = bit.rstrip(". ")
        # do this after
        if len(bit) > 254 and trim:
            bit = bit[:254]
        elif len(bit) > 254:
            raise IllegalPathError(f"Node '{source_bit}' has more than 254 characters")
        return bit


__all__ = ["PathTools"]
