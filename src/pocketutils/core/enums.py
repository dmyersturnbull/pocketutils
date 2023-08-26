import enum
import logging
from collections.abc import Set
from typing import Self

from pocketutils.core.exceptions import XKeyError

logger = logging.getLogger("pocketutils")


class DisjointEnum(enum.Enum):
    """
    An enum that does not have combinations.
    """

    @classmethod
    def _fix_lookup(cls: type[Self], s: str) -> str:
        return s

    @classmethod
    def or_none(cls: type[Self], s: str | Self) -> Self | None:
        """
        Returns a choice by name (or returns `s` itself).
        Returns `None` if the choice is not found.
        """
        try:
            return cls.of(s)
        except KeyError:
            return None

    @classmethod
    def of(cls: type[Self], s: str | Self) -> Self:
        """
        Returns a choice by name (or returns `s` itself).
        """
        if isinstance(s, cls):
            return s
        return cls[cls._fix_lookup(s)]


class FlagEnum(enum.Flag):
    """
    A bit flag that behaves as a set, has a null set, and auto-sets values and names.

    Example:
        ```python
        class Flavor(FlagEnum):
            NONE = ()
            BITTER = ()
            SWEET = ()
            SOUR = ()
            UMAMI = ()


        bittersweet = Flavor.BITTER | Flavor.SWEET
        print(bittersweet.value)  # 1 + 2 == 3
        print(bittersweet.name)  # "bitter|sweet"
        ```

    Note:
        The *first element* must always be the null set ("no flags")
        and should be named something like 'none', 'empty', or 'zero'
    """

    @classmethod
    def _fix_lookup(cls: type[Self], s: str) -> str:
        return s

    @classmethod
    def or_none(cls: type[Self], s: str | Self) -> Self | None:
        """
        Returns a choice by name (or returns `s` itself).

        Returns:
            `None` if the choice is not found.
        """
        try:
            return cls.of(s)
        except KeyError:
            return None

    @classmethod
    def of(cls: type[Self], s: str | Self | Set[str | Self]) -> Self:
        """
        Returns a choice by name (or `s` itself), or a set of those.
        """
        if isinstance(s, cls):
            return s
        if isinstance(s, str):
            return cls[cls._fix_lookup(s)]
        z = cls(0)
        for m in s:
            z |= cls.of(m)
        return z


@enum.unique
class TrueFalseEither(DisjointEnum):
    """
    A :class:`pocketutils.core.enums.DisjointEnum` of true, false, or unknown.
    """

    TRUE = enum.auto()
    FALSE = enum.auto()
    EITHER = enum.auto()

    @classmethod
    def _if_not_found(cls: type[Self], s: str | Self) -> Self:
        return cls.EITHER


@enum.unique
class MultiTruth(FlagEnum):
    """
    A :class:`pocketutils.core.enums.FlagEnum` for true, false, true+false, and neither.
    """

    FALSE = enum.auto()
    TRUE = enum.auto()


class CleverEnum(DisjointEnum):
    """
    An enum with a :meth:`of` method that finds values with limited string/value fixing.
    Replaces `" "` and `"-"` with `_` and ignores case in :meth:`of`.
    May support an "unmatched" type via :meth:`_if_not_found`,
    which can return a fallback value when there is no match.

    Example:
        ```python
        class Thing(CleverEnum):
            BUILDING = ()
            OFFICE_SUPPLY = ()
            POWER_OUTLET = ()


        x = Thing.of("power outlet")
        ```

    Example:
        ```python
        class Color(CleverEnum):
            RED = ()
            GREEN = ()
            BLUE = ()
            OTHER = ()

            @classmethod
            def _if_not_found(cls: type[Self], s: str) -> Self:
                # raise XValueError(f"No member for value '{s}'", value=s) from None
                #   ^
                #   the default implementation
                logger.warning(f"Color {s} unknown; using {cls.OTHER}")
                return cls.OTHER
        ```

    Note:

        If :meth:`_if_not_found` is overridden, it should return a member value.
        (In particular, it should never return `None`.)

    Note:

        To use with non-uppercase enum values (e.g. `Color.red` instead of `Color.RED`),
        override :meth:`_fix_lookup` with this::

            @classmethod
            def _fix_lookup(cls: type[Self], s: str) -> str:
                return s.strip().replace(" ", "_").replace("-", "_").lower()
                #                                                      ^
                #                                                    changed
    """

    @classmethod
    def of(cls: type[Self], s: str | Self) -> Self:
        try:
            return super().of(s)
        except KeyError:
            return cls._if_not_found(s)

    @classmethod
    def _if_not_found(cls: type[Self], s: str | Self) -> Self:
        msg = f"No member for value '{s}'"
        raise XKeyError(msg, key=s) from None

    @classmethod
    def _fix_lookup(cls: type[Self], s: str) -> str:
        return s


__all__ = ["TrueFalseEither", "DisjointEnum", "FlagEnum", "CleverEnum", "MultiTruth"]
