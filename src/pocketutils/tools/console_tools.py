import logging
import sys
from collections.abc import Callable
from typing import Any, Self

logger = logging.getLogger("pocketutils")


class ConsoleTools:
    CURSOR_UP_ONE = "\x1b[1A"
    ERASE_LINE = "\x1b[2K"

    @classmethod
    def prompt_yes_no(cls: type[Self], msg: str, writer: Callable[[str], Any] = sys.stdout.write) -> bool:
        """
        Asks for "yes" or "no" via `input`.
        Consider using `typer.prompt` instead.
        """
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
    def confirm(
        cls: type[Self],
        msg: str = "Confirm? [yes/no]",
        *,
        input_fn: Callable[[str], str] = input,
        writer: Callable[[str], Any] = sys.stdout.write,
    ) -> bool:
        """
        Asks for a confirmation from the user using the builtin `input`.

        Consider using `typer.prompt` instead.
            msg: If None, no message is written
            input_fn: Function to get the user input (its argument is always '')
            writer: Print using this function (should not print a newline by default)

        Returns:
            True if the user answered 'yes'; False otherwise
        """
        while True:
            writer(msg + " ")
            command = input_fn("").lower()
            if command in ["yes", "y"]:
                return True
            elif command in ["no", "n"]:
                return False

    @classmethod
    def clear_line(cls: type[Self], n: int = 1, writer: Callable[[str], None] = sys.stdout.write) -> None:
        """
        Writes control characters to stdout to delete the previous line and move the cursor up.
        This only works in a shell.

        Args:
            n: The number of lines to erase
            writer: Function to call (passing the string)
        """
        for _ in range(n):
            writer(ConsoleTools.CURSOR_UP_ONE)
            writer(ConsoleTools.ERASE_LINE)


__all__ = ["ConsoleTools"]
