import enum
import logging
from typing import AbstractSet, Optional, Union

from pocketutils.core.exceptions import XKeyError, XValueError

logger = logging.getLogger("pocketutils")


class DisjointEnum(enum.Enum):
    """
    An enum that does not have combinations.
    """

    @classmethod
    def _fix_lookup(cls, s: str) -> str:
        return s

    @classmethod
    def or_none(cls, s: Union[str, __qualname__]) -> Optional[__qualname__]:
        """
        Returns a choice by name (or returns ``s`` itself).
        Returns ``None`` if the choice is not found.
        """
        try:
            return cls.of(s)
        except KeyError:
            return None

    @classmethod
    def of(cls, s: Union[str, __qualname__]) -> __qualname__:
        """
        Returns a choice by name (or returns ``s`` itself).
        """
        if isinstance(s, cls):
            return s
        return cls[cls._fix_lookup(s)]

    def __new__(cls, *args, **kwargs):
        value = len(cls.__members__) + 1
        obj = object.__new__(cls)
        obj._value_ = value
        return obj

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name


class FlagEnum(enum.Flag):
    """
    A bit flag that behaves as a set, has a null set, and auto-sets values and names.

    Example:
        .. code-block::

            class Flavor(FlagEnum):
                NONE = ()
                BITTER = ()
                SWEET = ()
                SOUR = ()
                UMAMI = ()
            bittersweet = Flavor.BITTER | Flavor.SWEET
            print(bittersweet.value)  # 1 + 2 == 3
            print(bittersweet.name)   # "bitter|sweet"

    .. important::
        The *first element* must always be the null set ("no flags")
        and should be named something like 'none', 'empty', or 'zero'
    """

    @classmethod
    def _fix_lookup(cls, s: str) -> str:
        return s

    def __new__(cls, *args, **kwargs):
        if len(cls.__members__) == 0:
            value = 0
        else:
            value = 2 ** (len(cls.__members__) - 1)
        obj = object.__new__(cls)
        obj._value_ = value
        return obj

    @classmethod
    def _create_pseudo_member_(cls, value):
        value = super()._create_pseudo_member_(value)
        members, _ = enum._decompose(cls, value)
        value._name_ = "|".join([m.name for m in members])
        return value

    @classmethod
    def or_none(cls, s: Union[str, __qualname__]) -> Optional[__qualname__]:
        """
        Returns a choice by name (or returns ``s`` itself).

        Returns:
            ``None`` if the choice is not found.
        """
        try:
            return cls.of(s)
        except KeyError:
            return None

    @classmethod
    def of(cls, s: Union[str, __qualname__, AbstractSet[Union[str, __qualname__]]]) -> __qualname__:
        """
        Returns a choice by name (or ``s`` itself), or a set of those.
        """
        if isinstance(s, cls):
            return s
        if isinstance(s, str):
            return cls[cls._fix_lookup(s)]
        z = cls(0)
        for m in s:
            z |= cls.of(m)
        return z

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name


class TrueFalseEither(DisjointEnum):
    """
    A :class:`pocketutils.core.enums.DisjointEnum` of true, false, or unknown.
    """

    TRUE = ()
    FALSE = ()
    EITHER = ()

    @classmethod
    def _if_not_found(cls, s: Union[str, __qualname__]) -> __qualname__:
        return cls.EITHER

    @classmethod
    def _fix_lookup(cls, s: str) -> str:
        return s.upper().strip()


class MultiTruth(FlagEnum):
    """
    A :class:`pocketutils.core.enums.FlagEnum` for true, false, true+false, and neither.
    """

    FALSE = ()
    TRUE = ()


class CleverEnum(DisjointEnum):
    """
    An enum with a :meth:`of` method that finds values with limited string/value fixing.
    Replaces ``" "`` and ``"-"``` with ``_`` and ignores case in :meth:`of`.
    May support an "unmatched" type via :meth:`_if_not_found`,
    which can return a fallback value when there is no match.

    Example:
        class Thing(CleverEnum):
            BUILDING = ()
            OFFICE_SUPPLY = ()
            POWER_OUTLET = ()

        x = Thing.of("power outlet")

    Example:
        class Color(CleverEnum):
            RED = ()
            GREEN = ()
            BLUE = ()
            OTHER = ()

            @classmethod
            def _if_not_found(cls, s: Union[str, __qualname__]) -> __qualname__:
                # raise XValueError(f"No member for value '{s}'", value=s) from None
                #   ^
                #   the default implementation
                logger.warning(f"Color {s} unknown; using {cls.OTHER}")
                return cls.OTHER

    .. important::

        If :meth:`_if_not_found` is overridden, it should return a member value.
        (In particular, it should never return ``None``.)

    .. important::

        To use with non-uppercase enum values (e.g. ``Color.red`` instead of ``Color.RED``),
        override :meth:`_fix_lookup` with this::

            @classmethod
            def _fix_lookup(cls, s: str) -> str:
                return s.strip().replace(" ", "_").replace("-", "_").lower()
                #                                                      ^
                #                                                    changed
    """

    @classmethod
    def of(cls, s: Union[str, __qualname__]) -> __qualname__:
        try:
            return super().of(s)
        except KeyError:
            return cls._if_not_found(s)

    @classmethod
    def _if_not_found(cls, s: Union[str, __qualname__]) -> __qualname__:
        raise XKeyError(f"No member for value '{s}'", key=s) from None

    @classmethod
    def _fix_lookup(cls, s: str) -> str:
        return s.strip().replace(" ", "_").replace("-", "_").upper()


__all__ = ["TrueFalseEither", "DisjointEnum", "FlagEnum", "CleverEnum", "MultiTruth"]
