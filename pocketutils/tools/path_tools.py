import re
import sys
from typing import Mapping, Optional, Sequence

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
        This is not reliable. For a more sophisticated solution, see https://github.com/hsoft/send2trash
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
    def prep_dir(cls, path: PathLike, exist_ok: bool = True) -> bool:
        """
        Prepares a directory by making it if it doesn't exist.
        If exist_ok is False, calls logger.warning it already exists
        """
        path = Path(path)
        exists = path.exists()
        # On some platforms we get generic exceptions like permissions errors,
        # so these are better
        if exists and not path.is_dir():
            raise DirDoesNotExistError(f"Path {path} exists but is not a file")
        if exists and not exist_ok:
            logger.warning(f"Directory {path} already exists")
        if not exists:
            # NOTE! exist_ok in mkdir throws an error on Windows
            path.mkdir(parents=True)
        return exists

    @classmethod
    def prep_file(cls, path: PathLike, exist_ok: bool = True) -> bool:
        """
        Prepares a file path by making its parent directory (if it doesn't exist) and checking it.
        """
        # On some platforms we get generic exceptions like permissions errors, so these are better
        path = Path(path)
        exists = path.exists()
        # check for errors first; don't make the dirs and then fail
        if exists and not exist_ok:
            raise FileExistsError(f"Path {path} already exists")
        elif exists and not path.is_file() and not path.is_symlink():  # TODO check link?
            raise FileDoesNotExistError(f"Path {path} exists but is not a file")
        # NOTE! exist_ok in mkdir throws an error on Windows
        if not path.parent.exists():
            Path(path.parent).mkdir(parents=True, exist_ok=True)
        return exists

    @classmethod
    def sanitize_path(
        cls, path: PathLike, is_file: Optional[bool] = None, show_warnings: bool = True
    ) -> Path:
        """
        Sanitizes a path for major OSes and filesystems.
        Also see sanitize_path_nodes and sanitize_path_node.
        Platform-dependent.
        A corner case is drive letters in Linux:
        "C:\\Users\\john" is converted to '/C:/users/john' if os.name=='posix'
        """
        # the idea is to sanitize for both Windows and Posix, regardless of the platform in use
        # the sanitization should be as uniform as possible for both platforms
        # this works for at least Windows+NTFS
        # tilde substitution for long filenames in Windows -- is unsupported
        if path.startswith("\\\\?"):
            logger.warning(
                f"Long UNC Windows paths (\\\\? prefix) are not supported (path '{path}')"
            )
        bits = str(path).strip().replace("\\", "/").split("/")
        new_path = cls.sanitize_path_nodes(bits, is_file=is_file)
        if new_path != path and show_warnings:
            logger.warning(f"Sanitized filename {path} → {new_path}")
        return Path(new_path)

    @classmethod
    def sanitize_path_nodes(cls, bits: Sequence[PathLike], is_file: Optional[bool] = None) -> Path:
        fixed_bits = [
            bit + os.sep
            if i == 0 and bit.strip() in ["", ".", ".."]
            else cls.sanitize_path_node(
                bit,
                is_file=(False if i < len(bits) - 1 else is_file),
                is_root_or_drive=(None if i == 0 else False),
            )
            for i, bit in enumerate(bits)
            if bit.strip() not in ["", "."]
            or i == 0  # ignore // (empty) just like Path does (but fail on sanitize_path_node(' '))
        ]
        fixed_bits = [bit for i, bit in enumerate(fixed_bits) if i == 0 or bit not in ["", "."]]
        # unfortunately POSIX turns Path('C:\', '5') into C:\/5
        # this isn't an ideal way to fix it, but it works
        if (
            os.name == "posix"
            and len(fixed_bits) > 0
            and re.compile(r"^([A-Z]:)(?:\\)?$").fullmatch(fixed_bits[0])
        ):
            fixed_bits[0] = fixed_bits[0].rstrip("\\")
            fixed_bits.insert(0, "/")
        return Path(*fixed_bits)

    @classmethod
    def sanitize_path_node(
        cls,
        bit: PathLike,
        is_file: Optional[bool] = None,
        is_root_or_drive: Optional[bool] = None,
        include_fat: bool = False,
    ) -> str:
        """
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
            include_fat: Also make compatible with FAT filesystems

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
            m = re.compile(r"^([A-Z]:)(?:\\)?$").fullmatch(bit)
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
        if include_fat:
            bad_strs += {"$IDLE$", "CONFIG$", "KEYBD$", "SCREEN$", "CLOCK$", "LST"}
        # just dots is invalid
        if set(bit.replace(" ", "")) == "." and bit not in ["..", "."]:
            raise IllegalPathError(f"Node '{source_bit}' is invalid")
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
            raise IllegalPathError(f"Node '{source_bit}' is empty or contains only whitespace")
        # do this after
        if len(bit) > 254:
            raise IllegalPathError(f"Node '{source_bit}' has more than 254 characters")
        bit = bit.strip()
        if is_file is not True and (bit == "." or bit == ".."):
            return bit
        # never allow '.' (or ' ') to end a filename
        bit = bit.rstrip(".")
        return bit

    @classmethod
    def _replace_all(cls, s: str, rep: Mapping[str, str]) -> str:
        for k, v in rep.items():
            s = s.replace(k, v)
        return s


__all__ = ["PathTools"]
