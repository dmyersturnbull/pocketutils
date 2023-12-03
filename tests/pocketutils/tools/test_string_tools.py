# SPDX-FileCopyrightText: Copyright 2020-2023, Contributors to pocketutils
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/pocketutils
# SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass
from typing import Any, Self

import pytest
from pocketutils import ValueOutOfRangeError
from pocketutils.core.chars import Chars
from pocketutils.tools.string_tools import StringTools


@dataclass(frozen=True, slots=True)
class Mammal:
    species: Any


class TestStringTools:
    def test_pretty_dict(self: Self) -> None:
        f = StringTools.pretty_dict
        assert f({"☢": "☡"}) == '{\n  "☢": "☡"\n}'

    def test_truncate(self: Self) -> None:
        f = StringTools.truncate
        assert f("1234567", 3) == "12…"
        assert f("1234567", 1) == "…"
        assert f("1234567", 0) == "…"
        assert f("1234567", -1) == "…"
        assert f("1234567", 3) == "12…"
        assert f("123", 3) == "123"
        assert f("123", 6) == "123"
        assert None is f(None, 4)
        assert f(None, 4, null="xx") == "xx"

    def fix_greek(self: Self) -> None:
        f = StringTools.replace_greek_letter_names_with_chars
        assert f("beta") == "\u03B2"
        assert f("theta") == "\u03B8"
        assert f("Beta") == "\u0392"
        assert f("BETA") == "BETA"
        assert f("BETA", lowercase=True) == "BETA"
        assert f("Beta", lowercase=True) == "\u03B2"

    def test_tabs_to_list(self: Self) -> None:
        assert ["a", "b", "c\td", "e"] == StringTools.tabs_to_list('a\t"b"\t"c\td"\te')

    def test_strip_brackets(self: Self) -> None:
        f = StringTools.strip_brackets
        assert f("{{[(abcd]}}") == "(abcd"
        assert f("{[{abcd}]}") == "abcd"
        assert f("") == ""

    def test_strip_paired(self: Self) -> None:
        f = StringTools.strip_paired
        assert f("{{[(abcd]}}", [("a", "b")]) == "{{[(abcd]}}"
        assert f("abcd", [("a", "b")]) == "abcd"
        assert f("abab", [("a", "b")]) == "ba"
        assert f("aabb", [("a", "b")]) == ""
        assert f("", []) == ""

    # TODO these should pass
    """

    @given(strategies.integers())
    def test_subscript_ints(self: Self, i: int):
        assert StringTools.unsubscript(StringTools.subscript(str(i))) == str(i)

    @given(strategies.text())
    def test_subscript_strs(self: Self, s: str):
        assert StringTools.unsubscript(StringTools.subscript(s)) == s

    @given(strategies.text())
    def test_subscript_strs_rev(self: Self, s: str):
        assert StringTools.subscript(StringTools.unsubscript(s)) == s

    @given(strategies.integers())
    def test_superscript_ints(self: Self, i: int):
        assert StringTools.unsuperscript(StringTools.superscript(str(i))) == str(i)

    @given(strategies.text())
    def test_superscript_strs(self: Self, s: str):
        assert StringTools.unsuperscript(StringTools.superscript(s)) == s

    @given(strategies.text())
    def test_superscript_strs_rev(self: Self, s: str):
        assert StringTools.superscript(StringTools.unsuperscript(s)) == s

    """

    def test_pretty_float(self: Self) -> None:
        f = StringTools.pretty_float
        assert f(0.1) == "+0.1"
        assert f(-0.1) == Chars.minus + "0.1"
        assert f(0.0000001) == "+e-07"
        assert f(0.0) == "0.0"
        assert f(0.1, n_sigfigs=1) == "+0.1"
        assert f(float("NaN")) == "NaN"
        assert f(float("Inf")) == "+" + Chars.inf
        assert f(-float("Inf")) == Chars.minus + Chars.inf
        assert f(0) == "0"
        assert f(1111111) == "+111100"
        with pytest.raises(ValueOutOfRangeError):
            f(0.0, n_sigfigs=0)

    def test_pretty_repr(self: Self) -> None:
        f = StringTools.pretty_object
        assert f(lambda: None) == "⟨λ⟩"
        assert f(lambda q: None) == "⟨λ⟩"
        assert f(None) == "⌀"
        assert f(5) == "5"

        def x():
            pass

        assert f(x) == "⟨x⟩"

        class X:
            pass

        class Y:
            def __str__(self: Self) -> str:
                return "!!"

        assert f(X) == "⟨type:X⟩"
        assert f(X()) == "⟨X⟩"
        assert f(Y()) == "!!"
        assert f(Mammal("cat")) == "Mammal(species='cat')"


if __name__ == "__main__":
    pytest.main()
