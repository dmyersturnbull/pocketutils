import enum
import logging
from typing import AbstractSet, Optional, Union

from pocketutils.core.exceptions import XValueError

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
                none = ()
                bitter = ()
                sweet = ()
                sour = ()
                umami = ()
            bittersweet = Flavor.bitter | Flavor.sweet
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
        Returns ``None`` if the choice is not found.
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
            return cls[cls._fix_lookup_(s)]
        z = cls[0]
        for m in s:
            z |= cls.of(m)
        return z

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name


class TrueFalseUnknown(DisjointEnum):
    """
    A :class:`pocketutils.core.enums.DisjointEnum` of true, false, or unknown.
    """

    true = ()
    false = ()
    unknown = ()

    @classmethod
    def _unmatched_type(cls) -> Optional[__qualname__]:
        return cls.unknown

    @classmethod
    def _fix_lookup(cls, s: str) -> str:
        s = s.lower().strip()
        return dict(t="true", false="false").get(s, s)


class MultiTruth(FlagEnum):
    """
    A :class:`pocketutils.core.enums.FlagEnum` for true, false, true+false, and neither.
    """

    false = ()
    true = ()


class CleverEnum(DisjointEnum):
    """
    An enum with a ``.of`` method that finds values with limited string/value fixing.
    Replaces ``" "``, ``"-"``, and ``"."`` with ``_`` and ignores case in :meth:`of`.
    May support an "unmatched" type -- a fallback value when there is no match.
    This is similar to the simpler :class:`pocketutils.core.SmartEnum`.
    """

    @classmethod
    def of(cls, s: Union[str, __qualname__]) -> __qualname__:
        try:
            return super().of(s)
        except KeyError:
            unknown = cls._unmatched_type()
            logger.error(f"Value {s} not found. Using {unknown}")
            if unknown is None:
                raise XValueError(f"Value {s} not found and unmatched_type is None", value=s)
            return unknown

    @classmethod
    def _unmatched_type(cls) -> Optional[__qualname__]:
        return None

    @classmethod
    def _fix_lookup(cls, s: str) -> str:
        return s.strip().replace(" ", "_").replace(".", "_").replace("-", "_").lower()


__all__ = ["TrueFalseUnknown", "DisjointEnum", "FlagEnum", "CleverEnum"]
