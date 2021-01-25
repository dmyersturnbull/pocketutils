import logging
import sys
import time
from typing import Callable, Union

from pocketutils.tools.base_tools import BaseTools
from pocketutils.tools.filesys_tools import FilesysTools

logger = logging.getLogger("pocketutils")


class ConsoleTools(BaseTools):

    CURSOR_UP_ONE = "\x1b[1A"
    ERASE_LINE = "\x1b[2K"

    @classmethod
    def prompt_yes_no(cls, msg: str, writer: Callable[[str], None] = sys.stdout.write) -> bool:
        while True:
            writer(msg + " ")
            command = input("")
            if command.lower() == "yes":
                return True
            elif command.lower() == "no":
                return False
            else:
                writer("Enter 'yes' or 'no'.\n")

    @classmethod
    def slow_delete(
        cls,
        path: str,
        wait: int = 5,
        delete_fn: Callable[[str], None] = FilesysTools.delete_surefire,
        writer: Callable[[str], None] = sys.stdout.write,
    ):
        logger.debug(f"Deleting directory tree {path} ...")
        writer(f"Waiting for {wait}s before deleting {path}: ")
        for i in range(0, wait):
            time.sleep(1)
            writer(str(wait - i) + " ")
        time.sleep(1)
        writer("...")
        delete_fn(path)
        writer(" deleted.\n")
        logger.debug(f"Deleted directory tree {path}")

    @classmethod
    def confirm(
        cls,
        msg: Union[None, str, Callable[[], None]] = None,
        input_fn: Callable[[str], str] = input,
        writer: Callable[[str], None] = sys.stdout.write,
    ) -> bool:
        """
        Asks for a confirmation from the user using the bulletin input().
            msg: If None defaults to 'Confirm? [yes/no]'
            input_fn: Function to get the user input (its argument is always '')
            writer: Print using this function (should not print a newline by default)

        Returns:
            True if the user answered 'yes'; False otherwise
        """
        if msg is None:
            msg = "Confirm? [yes/no]"
        if isinstance(msg, str):

            def msg():
                writer(msg + " ")

        while True:
            msg()
            command = input_fn("")
            if command.lower() == "/exit":
                break
            if command.lower() in ["yes", "y"]:
                return True
            elif command.lower() in ["no", "n"]:
                return False

    @classmethod
    def clear_line(cls, n: int = 1, writer: Callable[[str], None] = sys.stdout.write) -> None:
        """
        Writes control characters to stdout to delete the previous line and move the curser up.
        This only works in a shell.
            n: The number of lines to erase
            writer Write here
        """
        for _ in range(n):
            writer(ConsoleTools.CURSOR_UP_ONE)
            writer(ConsoleTools.ERASE_LINE)


__all__ = ["ConsoleTools"]
