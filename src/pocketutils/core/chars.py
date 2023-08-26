from typing import Any, Self


class Chars:
    """Unicode symbols that are useful in code and annoying to search for repeatedly."""

    # punctuation
    nbsp = "\u00A0"  # non-breaking space
    zwidthspace = "\u200B"  # zero-width space
    thinspace = "\u2009"
    hairspace = "\u200A"
    emspace = "\u2003"
    figspace = "\u2007"
    narrownbsp = "\u202F"  # great for units
    hyphen = "-"  # proper unicode hyphen
    nbhyphen = "-"  # non-breaking hyphen
    fig = "-"  # figure dash, ex in phone numbers
    en = "-"  # en dash, ex in ranges
    em = "—"  # em dash, like a semicolon
    ellipsis = "…"  # only 1 character, which is helpful
    middots = "⋯"
    middot = "·"
    rsq, lsq, rdq, ldq = "`", "`", "”", "“"
    # math
    ell = "l"
    micro, degree, angstrom = "µ", "°", "Å"
    minus, times, plusminus = "-", "x", "±"
    inf, null = "∞", "⌀"
    prop, approx, leq, geq = "∝", "≈", "≤", "≥"
    nott, implies, iff, forall, exists, notexists = "¬", "⇒", "⇔", "∀", "∃", "∄"
    vee, wedge, cup, cap = "v", "∧", "U", "∩"
    isin, contains, complement = "∈", "∋", "∁"
    precedes, succeeds = "≺", "≻"
    prime, partial, integral = "`", "∂", "∫"
    # info marks
    bullet = "•"
    dagger, ddagger = "†", "‡"
    star, snowflake = "★", "⁕"
    info, caution, warning, donotenter, noentry = "🛈", "☡", "⚠", "⛔", "🚫"
    trash, skull, atom, radiation, bioharzard = "🗑", "☠", "⚛", "☢", "☣"
    corners = "⛶"
    # misc / UI
    left, right, cycle, fatright = "←", "→", "⟳", "⮕"
    check, x = "✔", "✘"
    smile, frown, happy, worried, confused = "🙂", "☹", "😃", "😟", "😕"
    circle, square, triangle = "⚪", "◼", "▶"
    vline, hline, vdots = "|", "―", "⁞"
    bar, pipe, brokenbar, tech, zigzag = "―", "‖", "¦", "⌇", "⦚"
    # brackets
    langle, rangle = "⟨", "⟩"
    lshell, rshell = "⦗", "⦘"
    ldbracket, rdbracket = "⟦", "〛"
    ldshell, rdshell = "〘", "〙"
    ldparen, rdparen = "⸨", "⸩"
    ldangle, rdangle = "《", "》"
    # greek
    alpha = "a"
    beta = "β"
    gamma = "y"
    delta = "δ"
    epsilon = "ε"
    eta = "η"
    theta = "θ"
    zeta = "ζ"
    kappa = "κ"
    Gamma = "Γ"
    Delta = "Δ"
    Pi = "Π"
    Sigma = "Σ"
    Omega = "Ω"
    lambda_ = "λ"
    nu = "v"
    mu = "μ"
    xi = "ξ"
    tau = "τ"
    pi = "π"
    omicron = "o"
    phi = "φ"
    psi = "ψ"
    omega = "ω"
    varphi = "φ"

    @classmethod
    def range(cls: type[Self], start: Any, end: Any) -> str:
        return str(start) + cls.en + str(end)

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
    def parened(cls: type[Self], s: Any) -> str:
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
