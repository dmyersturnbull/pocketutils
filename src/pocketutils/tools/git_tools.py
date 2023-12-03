# SPDX-FileCopyrightText: Copyright 2020-2023, Contributors to pocketutils
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/pocketutils
# SPDX-License-Identifier: Apache-2.0
"""

"""

import re
import subprocess  # nosec
from dataclasses import dataclass
from pathlib import Path, PurePath
from typing import Self

from pocketutils import ValueIllegalError

__all__ = ["GitDescription", "GitUtils", "GitTools"]

# ex: 1.8.6-43-g0ceb89d3a954da84070858319f177abe3869752b-dirty
_GIT_DESC_PATTERN = re.compile(r"([\d.]+)-(\d+)-g([0-9a-h]{40})(?:-([a-z]+))?")


def _call(cmd: list[str], cwd: Path = Path.cwd()) -> str:
    return subprocess.check_output(cmd, cwd=cwd, encoding="utf-8").strip()  # noqa: S603,S607


@dataclass(frozen=True, order=True, slots=True)
class GitDescription:
    """
    Data collected from running `git describe --long --dirty --broken --abbrev=40 --tags`.
    """

    tag: str
    commits: str
    hash: str
    is_dirty: bool
    is_broken: bool


@dataclass(frozen=True, order=True, slots=True)
class GitConfig:
    user: str
    email: str
    autocrlf: str
    gpgsign: bool
    rebase: bool


@dataclass(frozen=True, order=True, slots=True)
class GitClone:
    repo_url: str
    repo_path: Path


@dataclass(frozen=True, slots=True, kw_only=True)
class GitDescription:
    """
    Data collected from running `git describe --long --dirty --broken --abbrev=40 --tags`.
    """

    text: str
    tag: str
    commits: str
    hash: str
    is_dirty: bool
    is_broken: bool

    def __str__(self: Self) -> str:
        return self.__class__.__name__ + "(" + self.text + ")"


@dataclass(slots=True, frozen=True)
class GitUtils:
    """
    Tools for external programs.

    Warning:
        Please note that these tools execute external code
        through the `subprocess` module.
        These calls are additionally made on partial executable paths,
        such as `git` rather than `/usr/bin/git`.
        This is an additional security consideration.
    """

    def clone(self: Self, repo: str, path: PurePath | str | None = Path.cwd()) -> None:
        _call(["git", "clone", repo], cwd=Path(path))

    def config(self: Self) -> GitConfig:
        return GitConfig(
            _call(["git", "config", "user.name"]),
            _call(["git", "config", "user.email"]),
            _call(["git", "config", "core.autocrlf"]),
            _call(["git", "config", "commit.gpgsign"]) == "true",
            _call(["git", "config", "pull.rebase"]) == "true",
        )

    def git_description(self: Self, git_repo_dir: PurePath | str = Path.cwd()) -> GitDescription:
        """
        Runs `git describe` and parses the output.

        Args:
            git_repo_dir: Path to the repository

        Returns:
            A `pocketutils.tools.program_tools.GitDescription` instance

        Raises:
            CalledProcessError:
        """
        cmd_args = {
            "cwd": str(git_repo_dir),
            "capture_output": True,
            "check": True,
            "text": True,
            "encoding": "utf-8",
        }
        cmd = "git describe --long --dirty --broken --abbrev=40 --tags".split(" ")
        # ignoring bandit security warning because we explain the security concerns
        # in the class docstring
        x = subprocess.run(cmd, **cmd_args)  # nosec
        return self._parse(x.stdout.strip())

    def _parse(self: Self, text: str):
        m = _GIT_DESC_PATTERN.fullmatch(text)
        if m is None:
            msg = f"Bad git describe string {text}"
            raise ValueIllegalError(msg, value=text)
        # noinspection PyArgumentList
        return GitDescription(
            text=text,
            tag=m.group(1),
            commits=m.group(2),
            hash=m.group(3),
            is_dirty=m.group(4) == "dirty",
            is_broken=m.group(4) == "broken",
        )


GitTools = GitUtils()
