# SPDX-FileCopyrightText: Copyright 2020-2023, Contributors to pocketutils
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/pocketutils
# SPDX-License-Identifier: Apache-2.0
"""

"""

from typing import Any, Self


class Chars:
    """Unicode symbols that are useful in code and annoying to search for repeatedly."""

    # punctuation
    nbsp = "\u00A0"  # non-breaking space
    zerowidthspace = "\u200B"  # zero-width space
    thinspace = "\u2009"
    hairspace = "\u200A"
    emspace = "\u2003"
    figspace = "\u2007"
    narrownbsp = "\u202F"  # great for units
    hyphen = "-"  # proper unicode hyphen
    nbhyphen = "-"  # non-breaking hyphen
    figdash = "-"  # figure dash, ex in phone numbers
    endash = "-"  # en dash, ex in ranges
    emdash = "—"  # em dash, like a semicolon
    ellipsis = "…"  # only 1 character, which is helpful
    middots = "⋯"
    middot = "·"
    rsq, lsq, rdq, ldq = "`", "`", "”", "“"
    # math
    ell, micro, degree = "ℓ", "µ", "°"
    minus, times, plusminus = "-", "x", "±"
    inf, null = "∞", "⌀"
    # info marks
    bullet = "•"
    dagger, ddagger = "†", "‡"
    star, snowflake = "★", "⁕"
    info, caution, warning, donotenter, noentry = "🛈", "☡", "⚠", "⛔", "🚫"
    # misc / UI
    left, right = "←", "→"
    check, x = "✔", "✘"
    vline, hline = "|", "―"
    bar, pipe, brokenbar, tech, zigzag = "―", "‖", "¦", "⌇", "⦚"
    # brackets
    langle, rangle = "⟨", "⟩"
    lshell, rshell = "⦗", "⦘"
    ldbracket, rdbracket = "⟦", "〛"
    ldshell, rdshell = "〘", "〙"
    ldparen, rdparen = "⸨", "⸩"
    ldangle, rdangle = "《", "》"

    @classmethod
    def range(cls: type[Self], start: Any, end: Any) -> str:
        return str(start) + cls.endash + str(end)

    @classmethod
    def squoted(cls: type[Self], s: Any) -> str:
        """Wraps a string in singsle quotes."""
        return Chars.lsq + str(s) + Chars.rsq

    @classmethod
    def dquoted(cls: type[Self], s: Any) -> str:
        """Wraps a string in double quotes."""
        return Chars.ldq + str(s) + Chars.rdq

    @classmethod
    def angled(cls: type[Self], s: Any) -> str:
        """Wraps a string in angled brackets."""
        return Chars.langle + str(s) + Chars.rangle

    @classmethod
    def dangled(cls: type[Self], s: Any) -> str:
        """Wraps a string in double brackets."""
        return Chars.ldangle + str(s) + Chars.rdangle

    @classmethod
    def parenthesized(cls: type[Self], s: Any) -> str:
        """Wraps a string in parentheses."""
        return "(" + str(s) + ")"

    @classmethod
    def bracketed(cls: type[Self], s: Any) -> str:
        """Wraps a string in square brackets."""
        return "[" + str(s) + "]"

    @classmethod
    def braced(cls: type[Self], s: Any) -> str:
        """Wraps a string in curly braces."""
        return "{" + str(s) + "}"

    @classmethod
    def shelled(cls: type[Self], s: Any) -> str:
        """Wraps a string in tortiose shell brackets (( ))."""
        return "(" + str(s) + ")"

    @classmethod
    def dbracketed(cls: type[Self], s: Any) -> str:
        """Wraps a string in double square brackets (⟦ ⟧)."""
        return Chars.ldbracket + str(s) + Chars.rdbracket


__all__ = ["Chars"]
