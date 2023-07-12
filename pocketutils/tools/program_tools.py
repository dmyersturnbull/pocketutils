import subprocess  # nosec
from pathlib import PurePath

import regex

from pocketutils.core.exceptions import ParsingError
from pocketutils.tools.git_description import GitDescription


class ProgramTools:
    """
    Tools for external programs.

    .. caution::
        Please note that these tools execute external code
        through the ``subprocess`` module.
        These calls are additionally made on partial executable paths,
        such as ``git`` rather than ``/usr/bin/git``.
        This is an additional security consideration.
    """

    @classmethod
    def git_description(cls, git_repo_dir: PurePath | str = ".") -> GitDescription:
        """
        Runs ``git describe`` and parses the output.

        Args:
            git_repo_dir: Path to the repository

        Returns:
            A :class:`pocketutils.tools.program_tools.GitDescription` instance

        Raises:
            CalledProcessError:
        """
        cmd_args = dict(
            cwd=str(git_repo_dir),
            capture_output=True,
            check=True,
            text=True,
            encoding="utf-8",
        )
        cmd = "git describe --long --dirty --broken --abbrev=40 --tags".split(" ")
        # ignoring bandit security warning because we explain the security concerns
        # in the class docstring
        x = subprocess.run(cmd, **cmd_args)  # nosec
        return cls._parse(x.stdout.decode(encoding="utf-8").strip())

    @classmethod
    def _parse(cls, text: str):
        pat = regex.compile(r"([\d.]+)-(\d+)-g([0-9a-h]{40})(?:-([a-z]+))?", flags=regex.V1)
        # ex: 1.8.6-43-g0ceb89d3a954da84070858319f177abe3869752b-dirty
        m = pat.fullmatch(text)
        if m is None:
            raise ParsingError(f"Bad git describe string {text}")
        # noinspection PyArgumentList
        return GitDescription(
            text,
            m.group(1),
            m.group(2),
            m.group(3),
            m.group(4) == "dirty",
            m.group(4) == "broken",
        )


__all__ = ["GitDescription", "ProgramTools"]
