from dataclasses import dataclass


@dataclass(frozen=True, eq=True)
class GitDescription:
    """
    Data collected from running ``git describe --long --dirty --broken --abbrev=40 --tags``.
    """

    text: str
    tag: str
    commits: str
    hash: str
    is_dirty: bool
    is_broken: bool

    def __repr__(self):
        return self.__class__.__name__ + "(" + self.text + ")"

    def __str__(self):
        return repr(self)


__all__ = ["GitDescription"]
