# SPDX-FileCopyrightText: Copyright 2020-2023, Contributors to pocketutils
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/pocketutils
# SPDX-License-Identifier: Apache-2.0
"""

"""

import re
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Self, TypeVar

import orjson
import regex

from pocketutils.core.exceptions import ValueIllegalError, ValueOutOfRangeError

__all__ = ["StringUtils", "StringTools"]

K_contra = TypeVar("K_contra", contravariant=True)
V_co = TypeVar("V_co", covariant=True)
_control_chars = regex.compile(r"\p{C}", flags=regex.VERSION1)


def is_true_iterable(s: Any) -> bool:
    return (
        s is not None
        and isinstance(s, Iterable)
        and not isinstance(s, str)
        and not isinstance(s, bytes | bytearray | memoryview)
    )


@dataclass(slots=True, frozen=True)
class StringUtils:
    def pretty_dict(self: Self, dct: Mapping[Any, Any]) -> str:
        """
        Returns a pretty-printed dict, complete with indentation. Will fail on non-JSON-serializable datatypes.
        """
        # return Pretty.condensed(dct)
        return orjson.dumps(dct, option=orjson.OPT_INDENT_2).decode(encoding="utf-8")

    def join_to_str(self: Self, *items: Any, last: str, sep: str = ", ") -> str:
        """
        Joins items to something like "cat, dog, and pigeon" or "cat, dog, or pigeon".

        Args:
            *items: Items to join; `str(item) for item in items` will be used
            last: Probably "and", "or", "and/or", or ""
                    Spaces are added/removed as needed if `suffix` is alphanumeric
                    or "and/or", after stripping whitespace off the ends.
            sep: Used to separate all words; include spaces as desired

        Examples:
            - `join_to_str(["cat", "dog", "elephant"], last="and")  # cat, dog, and elephant`
            - `join_to_str(["cat", "dog"], last="and")  # cat and dog`
            - `join_to_str(["cat", "dog", "elephant"], last="", sep="/")  # cat/dog/elephant`
        """

    def strip_control_chars(self: Self, s: str) -> str:
        """
        Strips all characters under the Unicode 'Cc' category.
        """
        return _control_chars.sub("", s)

    def roman_to_arabic(self: Self, roman: str, min_val: int | None = None, max_val: int | None = None) -> int:
        """
        Converts roman numerals to an integer.

        Args:
            roman: A string like "MCIV"
            min_val: Raise a ValueError if the parsed value is less than this
            max_val: Raise a ValueError if the parsed value is more than this

        Returns:
            The arabic numeral as a Python int
        """
        # this order is IMPORTANT!
        mp = {
            "IV": 4,
            "IX": 9,
            "XL": 40,
            "XC": 90,
            "CD": 400,
            "CM": 900,
            "I": 1,
            "V": 5,
            "X": 10,
            "L": 50,
            "C": 100,
            "D": 500,
            "M": 1000,
        }
        for k, v in mp.items():
            roman = roman.replace(k, str(v))
        # it'll just error if it's empty
        try:
            value = sum(int(num) for num in roman)
        except (ValueError, StopIteration):
            msg = f"Cannot parse roman numerals '{roman}'"
            raise ValueIllegalError(msg, value=roman)
        if min_val is not None and value < min_val or max_val is not None and value > max_val:
            msg = f"Value {roman} (int={value}) is out of range ({min_val}, {max_val})"
            raise ValueIllegalError(msg, value=roman)
        return value

    def tabs_to_list(self: Self, s: str) -> Sequence[str]:
        """
        Splits by tabs, but preserving quoted tabs, stripping quotes.
        In other words, will not split within a quoted substring.
        Double and single quotes are handled.
        """
        pat = re.compile(r"""((?:[^\t"']|"[^"]*"|'[^']*')+)""")

        # Don't strip double 2x quotes: ex ""55"" should be "55", not 55
        def strip(i: str) -> str:
            if i.endswith(('"', "'")):
                i = i[:-1]
            if i.startswith(('"', "'")):
                i = i[1:]
            return i.strip()

        return [strip(i) for i in pat.findall(s)]

    def truncate(self: Self, s: str | None, n: int = 40, *, null: str | None = None) -> str | None:
        """
        Truncates a string and adds ellipses, if needed.

        Returns a string if it has `n` or fewer characters;
        otherwise truncates to length `n-1` and appends `…` (UTF character).
        If `s` is None and `always_dots` is True, returns `n` copies of `.` (as a string).
        If `s` is None otherwise, returns None.

        Args:
            s: The string
            n: The maximum length, inclusive
            null: Replace `None` with this string

        Returns:
            A string or None
        """
        if s is None:
            return null
        if len(s) > n:
            nx = max(0, n - 1)
            return s[:nx] + "…"
        return s

    def strip_any_ends(self: Self, s: str, prefixes: str | Sequence[str], suffixes: str | Sequence[str]) -> str:
        """
        Flexible variant that strips any number of prefixes and any number of suffixes.
        Also less type-safe than more specific variants.
        Note that the order of the prefixes (or suffixes) DOES matter.
        """
        prefixes = [str(z) for z in prefixes] if is_true_iterable(prefixes) else [str(prefixes)]
        suffixes = [str(z) for z in suffixes] if is_true_iterable(suffixes) else [str(suffixes)]
        s = str(s)
        for pre in prefixes:
            if s.startswith(pre):
                s = s[len(pre) :]
        for suf in suffixes:
            if s.endswith(suf):
                s = s[: -len(suf)]
        return s

    def strip_brackets(self: Self, text: str) -> str:
        """
        Strips any and all pairs of brackets from start and end of a string, but only if they're paired.

        See Also:
             strip_paired
        """
        pieces = [
            "()",
            "[]",
            "[]",
            "{}",
            "<>",
            "⦗⦘",
            "⟨⟩",
            "⸨⸩",
            "⟦〛",
            "《》",
            "〘〙",
        ]
        return StringTools.strip_paired(text, pieces)

    def strip_quotes(self: Self, text: str) -> str:
        """
        Strips any and all pairs of quotes from start and end of a string, but only if they're paired.

        See Also:
            strip_paired
        """
        pieces = [
            "`",
            "`",
            "”“",
            "''",
            '""',
        ]
        return StringTools.strip_paired(text, pieces)

    def strip_brackets_and_quotes(self: Self, text: str) -> str:
        """
        Strips any and all pairs of brackets and quotes from start and end of a string, but only if they're paired.

        See Also:
            strip_paired
        """
        pieces = [
            "()",
            "[]",
            "[]",
            "{}",
            "<>",
            "⦗⦘",
            "⟨⟩",
            "⸨⸩",
            "⟦〛",
            "《》",
            "〘〙",
            "`",
            "`",
            "”“",
            "''",
            '""',
        ]
        return StringTools.strip_paired(text, pieces)

    def strip_paired(self: Self, text: str, pieces: Iterable[tuple[str, str] | str]) -> str:
        """
        Strips pairs of (start, end) from the ends of strings.

        Example:

            StringTools.strip_paired("[(abc]", [("()"), ("[]"))  # returns "(abc"

        See Also:
            [`strip_brackets`](pocketutils.tools.string_tools.StringUtils.strip_brackets)
        """
        if any(a for a in pieces if len(a) != 2):
            msg = f"Each item must be a string of length 2: (stard, end); got {pieces}"
            raise ValueIllegalError(msg, value=str(pieces))
        text = str(text)
        while len(text) > 0:
            yes = False
            for a, b in pieces:
                while text.startswith(a) and text.endswith(b):
                    text = text[1:-1]
                    yes = True
            if not yes:
                break
        return text

    def replace_digits_with_superscript_chars(self: Self, s: str | float) -> str:
        """
        Replaces digits, +, =, (, and ) with equivalent Unicode superscript chars (ex ¹).
        """
        return "".join(dict(zip("0123456789-+=()", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺⁼⁽⁾")).get(c, c) for c in s)

    def replace_digits_with_subscript_chars(self: Self, s: str | float) -> str:
        """
        Replaces digits, +, =, (, and ) with equivalent Unicode subscript chars (ex ₁).
        """
        return "".join(dict(zip("0123456789+-=()", "₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎")).get(c, c) for c in s)

    def replace_superscript_chars_with_digits(self: Self, s: str | float) -> str:
        """
        Replaces Unicode superscript digits, +, =, (, and ) with normal chars.
        """
        return "".join(dict(zip("⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺⁼⁽⁾", "0123456789-+=()")).get(c, c) for c in s)

    def replace_subscript_chars_with_digits(self: Self, s: str | float) -> str:
        """
        Replaces Unicode superscript digits, +, =, (, and ) with normal chars.
        """
        return "".join(dict(zip("₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎", "0123456789+-=()")).get(c, c) for c in s)

    def pretty_float(self: Self, v: float | int, n_sigfigs: int | None = 5) -> str:
        """
        Represents a float as a string, with symbols for NaN and infinity.
        The returned string always has a minus or + prepended. Strip off the plus with `.lstrip('+')`.
        If v is an integer (by isinstance), makes sure to display without a decimal point.
        If `n_sigfigs < 2`, will never have a

        For example:
            - StringTools.pretty_float(.2222222)       # '+0.22222'
            - StringTools.pretty_float(-.2222222)      # '-0.22222' (Unicode minus)
            - StringTools.pretty_float(-float('inf'))  # '-∞'
            - StringTools.pretty_float(np.NaN)         # 'NaN'
        """
        # TODO this seems absurdly long for what it does
        if n_sigfigs is None or n_sigfigs < 1:
            msg = f"Sigfigs of {n_sigfigs} is nonpositive"
            raise ValueOutOfRangeError(
                msg,
                value=n_sigfigs,
                minimum=1,
            )
        # first, handle NaN and infinities
        if v == float("-Inf"):
            return "-∞"
        if v == float("Inf"):
            return "+∞"
        elif not isinstance(v, str) and str(v) in ["nan", "na", "NaN"]:
            return "NaN"
        elif not isinstance(v, str) and str(v) == "NaT":
            return "NaT"
        # sweet. it's a regular float or int.
        if n_sigfigs is None:
            s = str(v).removesuffix(".0")
        else:
            # yes, this is weird. we need to convert from str to float then back to str
            s = str(float(str(("%." + str(n_sigfigs) + "g") % v)))
        # remove the .0 if the precision doesn't support it
        # if v >= 1 and n_sigfigs<2, it couldn't have a decimal
        # and if n_sigfigs<1, it definitely can't
        # and ... %g does this.
        if isinstance(v, int) or n_sigfigs is not None and n_sigfigs < 2:
            s = s.removesuffix(".0")
        # prepend + or - (unless 0)
        if float(s) == 0.0:
            return s
        s = s.replace("-", "-")
        if not s.startswith("-"):
            s = "+" + s[1:]
        if len(s) > 1 and s[1] == ".":
            s = s[0] + "0." + s[2:]
        return s

    def pretty_function(self: Self, function: Callable, *, with_addr: bool = False) -> str:
        n_args = str(function.__code__.co_argcount) if hasattr(function, "__code__") else "?"
        pat = re.compile(r"^<bound method [^ .]+\.([^ ]+) of (.+)>$")
        boundmatch = pat.fullmatch(str(function))
        addr = " @ " + hex(id(function)) if with_addr else ""
        # if isinstance(function, FunctionType):
        #    # simplify lambda functions!
        #    return "⟨" + "λ(" + n_args + ")" + addr + "⟩"
        if boundmatch is not None:
            # it's a method (bound function)
            # don't show the address of the instance AND its method
            pat = re.compile(r"@ ?0x[0-9a-hA-H]+\)?$")
            s = pat.sub("", boundmatch.group(2)).strip()
            return "⟨" + "`" + s + "`." + boundmatch.group(1) + "(" + n_args + ")" + addr + "⟩"
        elif callable(function):
            # it's an actual function
            name = function.__name__
            if name is None:
                return "⟨<fn>" + addr + "⟩"
            if name == "<lambda>":
                return "⟨λ" + addr + "⟩"
            return "⟨" + function.__name__ + addr + "⟩"
        msg = f"Wrong type {type(function)} for '{function}"
        raise ValueIllegalError(msg, value=type(function).__name__)

    def pretty_object(self: Self, thing: Any, *, with_addr: bool = False) -> str:
        """
        Get a better and shorter name for a function than str(function).
        Ex: `pprint_function(lambda s: s)  == '<λ>'`

        - Instead of '<bound method ...', you'll get '<name(nargs)>'
        - Instead of 'lambda ...', you'll get '<λ(nargs)>'
        - etc.

        Note:
          - If function is None, returns '⌀'
          - If function does not have __name__, returns prefix + type(function) + <address> + suffix
          - If it's a primitive, returns str(function)

        Args:
            thing: Can be anything, but especially useful for functions
            with_addr: Include `@ hex-mem-addr` in the name
        """
        addr = " @ " + hex(id(thing)) if with_addr else ""
        pat = re.compile(r"<([A-Za-z0-9_.<>]+)[ ']*object")
        objmatch = pat.search(str(thing))  # instance of global or local class
        if thing is None:
            return "⌀"
        if isinstance(thing, type):
            # it's a class
            return "⟨" + "type:" + thing.__name__ + "⟩"
        elif callable(thing):
            return self.pretty_function(thing, with_addr=with_addr)
        elif hasattr(thing, "__dict__") and len(thing.__dict__) > 0:
            # it's a member with attributes
            # it's interesting enough that it may have a good __str__
            # strip prefix and suffix because we'll re-add it
            s = str(thing).removeprefix("⟨").removesuffix("⟩")
            return "⟨" + s + addr + "⟩"
        elif objmatch is not None:
            # it's an instance without attributes
            s = objmatch.group(1)
            if "." in s:
                s = s[s.rindex(".") + 1 :]
            return "⟨" + s + addr + "⟩"
        # it's a primitive, etc
        return str(thing)

    def greek_chars_to_letter_names(self: Self) -> Mapping[str, str]:
        """
        Returns a dict from Greek lowercase+uppercase Unicode chars to their full names.
        """
        return dict(StringTools._greek_alphabet)

    def greek_letter_names_to_chars(self: Self) -> Mapping[str, str]:
        """
        Returns a dict from Greek lowercase+uppercase letter names to their Unicode chars.
        """
        return {v: k for k, v in StringTools._greek_alphabet.items()}

    def replace_greek_letter_names_with_chars(self: Self, s: str, lowercase: bool = False) -> str:
        """
        Replaces Greek letter names with their Unicode equivalents.
        Does this correctly by replacing superstrings before substrings.
        Ex: '1-beta' is '1-β' rather than '1-bη'
        If lowercase is True: Replaces Beta, BeTa, and BETA with β
        Else: Replaces Beta with a capital Greek Beta and ignores BETA and BeTa.
        """
        # Clever if I may say so:
        # If we just sort from longest to shortest, we can't replace substrings by accident
        # For example we'll replace 'beta' before 'eta', so '1-beta' won't become '1-bη'
        greek = sorted(
            [(v, k) for k, v in StringTools._greek_alphabet.items()],
            key=lambda t: -len(t[1]),
        )
        for k, v in greek:
            if k[0].isupper() and lowercase:
                continue
            s = re.compile(k | regex.IGNORECASE).sub(v, s) if lowercase else s.replace(k, v)
        return s

    def dict_to_compact_str(self: Self, seq: Mapping[K_contra, V_co], *, eq: str = "=", sep: str = ", ") -> str:
        return self.dict_to_str(seq, sep=sep, eq=eq)

    def dict_to_quote_str(self: Self, seq: Mapping[K_contra, V_co], *, eq: str = ": ", sep: str = "; ") -> str:
        return self.dict_to_str(seq, sep=sep, eq=eq, prefix="'", suffix="'")

    def dict_to_str(
        self: Self,
        seq: Mapping[K_contra, V_co],
        *,
        sep: str = "\t",
        eq: str = "=",
        prefix: str = "",
        suffix: str = "",
    ) -> str:
        """
        Joins dict elements into a str like 'a=1, b=2, c=3`.
        Won't break with ValueError if the keys or values aren't strs.

        Args:
            seq: Dict-like, with `items()`
            sep: Delimiter
            eq: Separates a key with its value
            prefix: Prepend before every key
            suffix: Append after every value
        """
        return sep.join([prefix + str(k) + eq + str(v) + suffix for k, v in seq.items()])

    _greek_alphabet = {
        "\u0391": "Alpha",
        "\u0392": "Beta",
        "\u0393": "Gamma",
        "\u0394": "Delta",
        "\u0395": "Epsilon",
        "\u0396": "Zeta",
        "\u0397": "Eta",
        "\u0398": "Theta",
        "\u0399": "Iota",
        "\u039A": "Kappa",
        "\u039B": "Lambda",
        "\u039C": "Mu",
        "\u039D": "Nu",
        "\u039E": "Xi",
        "\u039F": "Omicron",
        "\u03A0": "Pi",
        "\u03A1": "Rho",
        "\u03A3": "Sigma",
        "\u03A4": "Tau",
        "\u03A5": "Upsilon",
        "\u03A6": "Phi",
        "\u03A7": "Chi",
        "\u03A8": "Psi",
        "\u03A9": "Omega",
        "\u03B1": "alpha",
        "\u03B2": "beta",
        "\u03B3": "gamma",
        "\u03B4": "delta",
        "\u03B5": "epsilon",
        "\u03B6": "zeta",
        "\u03B7": "eta",
        "\u03B8": "theta",
        "\u03B9": "iota",
        "\u03BA": "kappa",
        "\u03BB": "lambda",
        "\u03BC": "mu",
        "\u03BD": "nu",
        "\u03BE": "xi",
        "\u03BF": "omicron",
        "\u03C0": "pi",
        "\u03C1": "rho",
        "\u03C3": "sigma",
        "\u03C4": "tau",
        "\u03C5": "upsilon",
        "\u03C6": "phi",
        "\u03C7": "chi",
        "\u03C8": "psi",
        "\u03C9": "omega",
    }


StringTools = StringUtils()
