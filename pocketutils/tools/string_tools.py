import json
import re
from copy import copy
from typing import Any, Iterable, Mapping, Optional, Sequence, Tuple, TypeVar, Union, Callable

import numpy as np

from pocketutils.core import JsonEncoder
from pocketutils.core.chars import *
from pocketutils.core.exceptions import OutOfRangeError
from pocketutils.tools.base_tools import BaseTools

T = TypeVar("T")
V = TypeVar("V")


class StringTools(BaseTools):
    @classmethod
    def pretty_dict(cls, dct: Mapping[Any, Any]) -> str:
        """
        Returns a pretty-printed dict, complete with indentation. Will fail on non-JSON-serializable datatypes.
        """
        # return Pretty.condensed(dct)
        return cls.retab(
            json.dumps(
                dct,
                default=JsonEncoder().default,
                sort_keys=True,
                indent=1,
                ensure_ascii=False,
            ),
            1,
        )

    @classmethod
    def extract_group_1(
        cls, pattern: Union[str, re.Pattern], value: Optional[str], ignore_null: bool = False
    ) -> Optional[str]:
        """
        Performs a ``fullmatch`` on a target string and returns capture group 1, or None if there was no match.

        Args:
            pattern: Regex pattern
            value: The target string
            ignore_null: If True, returns None if ``value`` is None; otherwise raises a ValueError if ``value`` is None
                         (Useful for *map*-like operations.)

        Returns The first capture group, or None
        """
        pattern = pattern if isinstance(pattern, re.Pattern) else re.compile(pattern)
        if pattern.groups != 1:
            raise ValueError(f"Pattern {pattern} has {pattern.groups} groups, not 1")
        if value is None and ignore_null:
            return None
        match = pattern.fullmatch(value)
        if match is None:
            return None
        return match.group(1)

    @classmethod
    def roman_to_arabic(
        cls, roman: str, min_val: Optional[int] = None, max_val: Optional[int] = None
    ) -> int:
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
        mp = dict(
            IV=4, IX=9, XL=40, XC=90, CD=400, CM=900, I=1, V=5, X=10, L=50, C=100, D=500, M=1000
        )
        for k, v in mp.items():
            roman = roman.replace(k, str(v))
        # it'll just error if it's empty
        try:
            value = sum((int(num) for num in roman))
        except (ValueError, StopIteration):
            raise ValueError(f"Cannot parse roman numerals '{roman}'")
        if min_val is not None and value < min_val or min_val is not None and roman > max_val:
            raise ValueError(f"Value {roman} (int={value}) is out of range ({min_val}, {max_val})")
        return value

    @classmethod
    def retab(cls, s: str, nspaces: int) -> str:
        """
        Converts indentation with spaces to tab indentation.

        Args:
            s: The string to convert
            nspaces: A tab is this number of spaces
        """

        def fix(m):
            n = len(m.group(1)) // nspaces
            return "\t" * n + " " * (len(m.group(1)) % nspaces)

        return re.sub("^( +)", fix, s, flags=re.MULTILINE)

    @classmethod
    def strip_empty_decimal(cls, num: Union[float, str]) -> str:
        """
        Replaces prefix . with 0. and strips trailing .0 and trailing .
        """
        try:
            float(num)
        except TypeError:
            if not isinstance(num, str):
                raise TypeError("Must be either str or float-like") from None
        t = str(num)
        if t.startswith("."):
            t = "0" + t
        if "." in t:
            return t.rstrip("0").rstrip(".")
        else:
            return t

    @classmethod
    def tabs_to_list(cls, s: str) -> Sequence[str]:
        """
        Splits by tabs, but preserving quoted tabs, stripping quotes.
        """
        pat = re.compile(r"""((?:[^\t"']|"[^"]*"|'[^']*')+)""")
        # Don't strip double 2x quotes: ex ""55"" should be "55", not 55
        def strip(i: str) -> str:
            if i.endswith('"') or i.endswith("'"):
                i = i[:-1]
            if i.startswith('"') or i.startswith("'"):
                i = i[1:]
            return i.strip()

        return [strip(i) for i in pat.findall(s)]

    @classmethod
    def truncate(cls, s: Optional[str], n: int, always_dots: bool = False) -> Optional[str]:
        """
        Returns a string if it has ``n`` or fewer characters;
        otherwise truncates to length ``n-1`` and appends ``…`` (UTF character).
        If ``s`` is None and ``always_dots`` is True, returns ``n`` copies of ``.`` (as a string).
        If ``s`` is None otherwise, returns None.

        Args:
            s: The string
            n: The maximum length, inclusive
            always_dots: Use dots instead of returning None; see above

        Returns:
            A string or None
        """
        if s is None and always_dots:
            return "…" * n
        if s is None:
            return None
        if len(s) > n:
            nx = max(0, n - 1)
            return s[:nx] + "…"
        return s

    # these are provided to avoid having to call with labdas or functools.partial
    @classmethod
    def truncator(cls, n: int = 40, always_dots: bool = False) -> Callable[[str], str]:
        # pretty much functools.partial
        def trunc(s: str) -> str:
            return cls.truncate(s, n, always_dots)

        trunc.__name__ = f"truncate({n},{'…' if always_dots else ''})"
        return trunc

    @classmethod
    def truncate60(cls, s: str) -> str:
        return StringTools.truncate(s, 60)

    @classmethod
    def truncate40(cls, s: str) -> str:
        return StringTools.truncate(s, 64)

    @classmethod
    def truncate30(cls, s: str) -> str:
        return StringTools.truncate(s, 30)

    @classmethod
    def truncate20(cls, s: str) -> str:
        return StringTools.truncate(s, 20)

    @classmethod
    def truncate10(cls, s: str) -> str:
        return StringTools.truncate(s, 10)

    @classmethod
    def truncate10_nodots(cls, s: str) -> str:
        return StringTools.truncate(s, 10, False)

    @classmethod
    def longest_str(cls, parts: Iterable[str]) -> str:
        """
        Returns the argmax by length.
        """
        mx = ""
        for i, x in enumerate(parts):
            if len(x) > len(mx):
                mx = x
        return mx

    @classmethod
    def strip_off_start(cls, s: str, pre: str):
        """
        Strips the full string `pre` from the start of `str`.
        See ``Tools.strip_off`` for more info.
        """
        if not isinstance(pre, str):
            raise TypeError(f"{pre} is not a string")
        if s.startswith(pre):
            s = s[len(pre) :]
        return s

    @classmethod
    def strip_off_end(cls, s: str, suf: str):
        """
        Strips the full string `suf` from the end of `str`.
        See `Tools.strip_off` for more info.
        """
        if not isinstance(suf, str):
            raise TypeError(f"{suf} is not a string")
        if s.endswith(suf):
            s = s[: -len(suf)]
        return s

    @classmethod
    def strip_off(cls, s: str, prefix_or_suffix: str) -> str:
        """
        Strip a substring from the beginning or end of a string (at most 1 occurrence).
        """
        return StringTools.strip_off_start(
            StringTools.strip_off_end(s, prefix_or_suffix), prefix_or_suffix
        )

    @classmethod
    def strip_ends(cls, s: str, prefix: str, suffix: str) -> str:
        """
        Strips a substring from the start, and another substring from the end, of a string (at most 1 occurrence each).
        """
        return StringTools.strip_off_start(StringTools.strip_off_end(s, suffix), prefix)

    @classmethod
    def strip_any_ends(
        cls,
        s: str,
        prefixes: Union[str, Sequence[str]],
        suffixes: Union[str, Sequence[str]],
    ) -> str:
        """
        Flexible variant that strips any number of prefixes and any number of suffixes.
        Also less type-safe than more specific variants.
        Note that the order of the prefixes (or suffixes) DOES matter.
        """
        prefixes = (
            [str(z) for z in prefixes]
            if StringTools.is_true_iterable(prefixes)
            else [str(prefixes)]
        )
        suffixes = (
            [str(z) for z in suffixes]
            if StringTools.is_true_iterable(suffixes)
            else [str(suffixes)]
        )
        s = str(s)
        for pre in prefixes:
            if s.startswith(pre):
                s = s[len(pre) :]
        for suf in suffixes:
            if s.endswith(suf):
                s = s[: -len(suf)]
        return s

    @classmethod
    def strip_brackets(cls, text: str) -> str:
        """
        Strips any and all pairs of brackets from start and end of a string, but only if they're paired.
        See ``strip_paired``
        """
        pieces = [
            ("(", ")"),
            ("[", "]"),
            ("[", "]"),
            ("{", "}"),
            ("<", ">"),
            (Chars.lshell, Chars.rshell),
            (Chars.langle, Chars.rangle),
            (Chars.ldparen, Chars.rdparen),
            (Chars.ldbracket, Chars.rdbracket),
            (Chars.ldangle, Chars.rdangle),
            (Chars.ldshell, Chars.rdshell),
        ]
        return StringTools.strip_paired(text, pieces)

    @classmethod
    def strip_quotes(cls, text: str) -> str:
        """
        Strips any and all pairs of quotes from start and end of a string, but only if they're paired.
        See ``strip_paired``
        """
        pieces = [
            ("`", "`"),
            (Chars.lsq, Chars.rsq),
            (Chars.ldq, Chars.rdq),
            ("'", "'"),
            ('"', '"'),
        ]
        return StringTools.strip_paired(text, pieces)

    @classmethod
    def strip_brackets_and_quotes(cls, text: str) -> str:
        """
        Strips any and all pairs of brackets and quotes from start and end of a string, but only if they're paired.
        See ``strip_paired``
        """
        pieces = [
            ("(", ")"),
            ("[", "]"),
            ("[", "]"),
            ("{", "}"),
            ("<", ">"),
            (Chars.lshell, Chars.rshell),
            (Chars.langle, Chars.rangle),
            ("`", "`"),
            (Chars.lsq, Chars.rsq),
            (Chars.ldq, Chars.rdq),
            ("'", "'"),
            ('"', '"'),
            (Chars.ldparen, Chars.rdparen),
            (Chars.ldbracket, Chars.rdbracket),
            (Chars.ldangle, Chars.rdangle),
            (Chars.ldshell, Chars.rdshell),
        ]
        return StringTools.strip_paired(text, pieces)

    @classmethod
    def strip_paired(cls, text: str, pieces: Iterable[Tuple[str, str]]) -> str:
        """
        Strips pairs of (start, end) from the ends of strings.

        Example:
            >>> StringTools.strip_paired('[(abc]', ['()', '[]'])  # returns '(abc'

        Also see ``strip_brackets``
        """
        if any([a for a in pieces if len(a) != 2]):
            raise ValueError(f"Each item must be a string of length 2: (stard, end); got {pieces}")
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

    @classmethod
    def replace_all(cls, s: str, rep: Mapping[str, str]) -> str:
        """
        Simply replace multiple things in a string.
        """
        for k, v in rep.items():
            s = s.replace(k, v)
        return s

    @classmethod
    def superscript(cls, s: Union[str, float]) -> str:
        """
        Replaces digits, +, =, (, and ) with equivalent Unicode superscript chars (ex ¹).
        """
        return "".join(dict(zip("0123456789-+=()", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺⁼⁽⁾")).get(c, c) for c in s)

    @classmethod
    def subscript(cls, s: Union[str, float]) -> str:
        """
        Replaces digits, +, =, (, and ) with equivalent Unicode subscript chars (ex ₁).
        """
        return "".join(dict(zip("0123456789+-=()", "₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎")).get(c, c) for c in s)

    @classmethod
    def unsuperscript(cls, s: Union[str, float]) -> str:
        """
        Replaces Unicode superscript digits, +, =, (, and ) with normal chars.
        """
        return "".join(dict(zip("⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺⁼⁽⁾", "0123456789-+=()")).get(c, c) for c in s)

    @classmethod
    def unsubscript(cls, s: Union[str, float]) -> str:
        """
        Replaces Unicode superscript digits, +, =, (, and ) with normal chars.
        """
        return "".join(dict(zip("₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎", "0123456789+-=()")).get(c, c) for c in s)

    @classmethod
    def dashes_to_hm(cls, s: str) -> str:
        """
        Replaces most Latin-alphabet dash-like and hyphen-like characters with a hyphen-minus.
        """
        smallem = "﹘"
        smallhm = "﹣"
        fullhm = "－"
        for c in [
            Chars.em,
            Chars.en,
            Chars.fig,
            Chars.minus,
            Chars.hyphen,
            Chars.nbhyphen,
            smallem,
            smallhm,
            fullhm,
        ]:
            s = str(s).replace(c, "-")
        return s

    @classmethod
    def pretty_float(cls, v: Union[float, int], n_sigfigs: Optional[int] = 5) -> str:
        """
        Represents a float as a string, with symbols for NaN and infinity.
        The returned string always has a minus or + prepended. Strip off the plus with .lstrip('+').
        If v is an integer (by isinstance), makes sure to display without a decimal point.
        If n_sigfigs < 2, will never have a
        For ex:
            - StringTools.pretty_float(.2222222)       # '+0.22222'
            - StringTools.pretty_float(-.2222222)      # '−0.22222' (Unicode minus)
            - StringTools.pretty_float(-float('inf'))  # '−∞'
            - StringTools.pretty_float(np.NaN)         # '⌀'
        """
        # TODO this seems absurdly long for what it does
        if n_sigfigs is None or n_sigfigs < 1:
            raise OutOfRangeError(
                f"Sigfigs of {n_sigfigs} is nonpositive",
                value=n_sigfigs,
                minimum=1,
            )
        # first, handle NaN and infinities
        if np.isneginf(v):
            return Chars.minus + Chars.inf
        elif np.isposinf(v):
            return "+" + Chars.inf
        elif np.isnan(v):
            return Chars.null
        # sweet. it's a regular float or int.
        if n_sigfigs is None:
            s = StringTools.strip_empty_decimal(str(v))
        else:
            # yes, this is weird. we need to convert from str to float then back to str
            s = str(float(str(("%." + str(n_sigfigs) + "g") % v)))
        # remove the .0 if the precision doesn't support it
        # if v >= 1 and n_sigfigs<2, it couldn't have a decimal
        # and if n_sigfigs<1, it definitely can't
        # and ... %g does this.
        if isinstance(v, int) or n_sigfigs is not None and n_sigfigs < 2:
            s = StringTools.strip_empty_decimal(s)
        # prepend + or - (unless 0)
        if float(s) == 0.0:
            return s
        s = s.replace("-", Chars.minus)
        if not s.startswith(Chars.minus):
            s = "+" + s[1:]
        if len(s) > 1 and s[1] == ".":
            s = s[0] + "0." + s[2:]
        return s

    @classmethod
    def pretty_function(
        cls, function, with_address: bool = False, prefix: str = "⟨", suffix: str = "⟩"
    ) -> str:
        """
        Get a better and shorter name for a function than str(function).
        Ex: pprint_function(lambda s: s)  == '<λ>'
        - Instead of '<bound method ...', you'll get '<name(nargs)>'
        - Instead of 'lambda ...', you'll get '<λ(nargs)>'
        - etc.
        NOTE 1: If function is None, returns '⌀'
        NOTE 2: If function does not have __name__, returns prefix + type(function) + <address> + suffix
        NOTE 3: If it's a primitive, returns str(function)

        Args:
            function: Can be anything, but especially useful for functions
            with_address: Include `@ hex-mem-addr` in the name
            prefix: Prefix to the whole string
            suffix: Suffix to the whole string
        """
        if function is None:
            return Chars.null
        n_args = str(function.__code__.co_argcount) if hasattr(function, "__code__") else "?"
        boundmatch = re.compile(r"^<bound method [^ .]+\.([^ ]+) of (.+)>$").fullmatch(
            str(function)
        )
        objmatch = re.compile(r"<([A-Za-z0-9_.<>]+)[ ']*object").search(
            str(function)
        )  # instance of global or local class
        addr = " @ " + hex(id(function)) if with_address else ""
        if cls.is_lambda(function):
            # simplify lambda functions!
            return prefix + "λ(" + n_args + ")" + addr + suffix
        elif boundmatch is not None:
            # it's a method (bound function)
            # don't show the address of the instance AND its method
            s = re.compile(r"@ ?0x[0-9a-hA-H]+\)?$").sub("", boundmatch.group(2)).strip()
            return (
                prefix + "`" + s + "`." + boundmatch.group(1) + "(" + n_args + ")" + addr + suffix
            )
        elif isinstance(function, type):
            # it's a class
            return prefix + "type:" + function.__name__ + suffix
        elif callable(function):
            # it's an actual function
            return prefix + function.__name__ + addr + suffix
        elif hasattr(function, "__dict__") and len(function.__dict__) > 0:
            # it's a member with attributes
            # it's interesting enough that it may have a good __str__
            s = StringTools.strip_off_end(
                StringTools.strip_off_start(str(function), prefix), suffix
            )
            return prefix + s + addr + suffix
        elif objmatch is not None:
            # it's an instance without attributes
            s = objmatch.group(1)
            if "." in s:
                s = s[s.rindex(".") + 1 :]
            return prefix + s + addr + suffix
        else:
            # it's a primitive, etc
            s = StringTools.strip_off_end(
                StringTools.strip_off_start(str(function), prefix), suffix
            )
            return s

    @classmethod
    def greek_to_name(cls) -> Mapping[str, str]:
        """
        Returns a dict from Greek lowercase+uppercase Unicode chars to their full names
        @return A defensive copy
        """
        return copy(StringTools._greek_alphabet)

    @classmethod
    def name_to_greek(cls) -> Mapping[str, str]:
        """
        Returns a dict from Greek lowercase+uppercase letter names to their Unicode chars
        @return A defensive copy
        """
        return {v: k for k, v in StringTools._greek_alphabet.items()}

    @classmethod
    def fix_greek(cls, s: str, lowercase: bool = False) -> str:
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
            if lowercase:
                s = re.compile(k, re.IGNORECASE).sub(v, s)
            else:
                s = s.replace(k, v)
        return s

    @classmethod
    def join(
        cls,
        seq: Iterable[T],
        sep: str = "\t",
        attr: Optional[str] = None,
        prefix: str = "",
        suffix: str = "",
    ) -> str:
        """
        Join elements into a str more easily than ''.join. Just simplifies potentially long expressions.
        Won't break with ValueError if the elements aren't strs.
        Ex:
            - StringTools.join([1,2,3])  # "1    2    3"
            - StringTools.join(cars, sep=',', attr='make', prefix="(", suffix=")")`  # "(Ford),(Ford),(BMW)"

            seq: Sequence of elements
            sep: Delimiter
            attr: Get this attribute from each element (in `seq`), or use the element itself if None
            prefix: Prefix before each item
            suffix: Suffix after each item

        Returns:
            A string
        """
        if attr is None:
            return sep.join([prefix + str(s) + suffix for s in seq])
        else:
            return sep.join([prefix + str(getattr(s, attr)) + suffix for s in seq])

    @classmethod
    def join_kv(
        cls,
        seq: Mapping[T, V],
        sep: str = "\t",
        eq: str = "=",
        prefix: str = "",
        suffix: str = "",
    ) -> str:
        """
        Joins dict elements into a str like 'a=1, b=2, c=3`.
        Won't break with ValueError if the keys or values aren't strs.

        Args:
            seq: Dict-like, with ``items()``
            sep: Delimiter
            eq: Separates a key with its value
            prefix: Prepend before every key
            suffix: Append after every value

        Returns:
            A string
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


__all__ = ["StringTools"]
