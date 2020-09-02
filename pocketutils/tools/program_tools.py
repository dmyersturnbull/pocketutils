import re
import subprocess
from dataclasses import dataclass

from pocketutils.core import PathLike
from pocketutils.core.exceptions import CalledProcessError, ParsingError
from pocketutils.tools.base_tools import BaseTools


@dataclass(frozen=True)
class GitDescription:
    """
    Data collected from running `git describe --long --dirty --broken --abbrev=40 --tags`
    """

    text: str
    tag: str
    commits: str
    hash: str
    is_dirty: bool
    is_broken: bool

    def __repr__(self):
        return self.__class__.__name__ + "(" + self.text + ")"

    def __str__(self):
        return repr(self)


class ProgramTools(BaseTools):
    @classmethod
    def commit_hash(cls, git_repo_dir: str = ".") -> str:
        """
        Gets the hex of the most recent Git commit hash in git_repo_dir.
        """
        return cls.git_description(git_repo_dir).hash

    @classmethod
    def git_description(cls, git_repo_dir: PathLike = ".") -> GitDescription:
        """
        Runs ``git describe`` and parses the output.

        Args:
            git_repo_dir: Path to the repository

        Returns:
            A ``GitDescription`` instance, with fields text, tag, commits, hash, is_dirty, and is_broken

        Raises:
            CalledProcessError:
        """
        x = subprocess.run(
            "git describe --long --dirty --broken --abbrev=40 --tags".split(" "),
            cwd=str(git_repo_dir),
            capture_output=True,
            check=True,
            text=True,
            encoding="utf8",
        )
        return cls._parse(x.stdout.strip())

    @classmethod
    def _parse(cls, text: str):
        pat = re.compile(r"([\d.]+)-(\d+)-g([0-9a-h]{40})(?:-([a-z]+))?")
        # ex: 1.8.6-43-g0ceb89d3a954da84070858319f177abe3869752b-dirty
        m = pat.fullmatch(text)
        if m is None:
            raise ParsingError("Bad git describe string {}".format(text))
        # noinspection PyArgumentList
        return GitDescription(
            text,
            m.group(1),
            int(m.group(2)),
            m.group(3),
            m.group(4) == "dirty",
            m.group(4) == "broken",
        )


__all__ = ["GitDescription", "ProgramTools"]
