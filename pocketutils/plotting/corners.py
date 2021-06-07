from typing import Any, Mapping


class Corner:
    """
    Just used for text alignment.
    I hate it, but at least I won't keep getting the wrong params.
    """

    def __init__(self, bottom: bool, left: bool):
        """

        Args:
            bottom:
            left:
        """
        self.name = ("bottom" if bottom else "top") + " " + "left" if left else "right"
        self.x = 0.0 if left else 1.0
        self.y = 0.0 if bottom else 1.0
        self.horizontalalignment = "left" if left else "right"
        # yes, these should be reversed: we want them above or below the figures
        self.verticalalignment = "top" if bottom else "bottom"

    def params(self) -> Mapping[str, Any]:
        """

        Returns:

        """
        return {
            "x": self.x,
            "y": self.y,
            "horizontalalignment": self.horizontalalignment,
            "verticalalignment": self.verticalalignment,
        }

    def __eq__(self, other):
        return type(self) == type(other) and self.x == other.x and self.y == other.y

    def __repr__(self):
        return "Corner(" + self.name + ")"

    def __str__(self):
        return repr(self)


class Corners:
    """The four corners of a Matplotlib axes with arguments for adding a text box."""

    BOTTOM_LEFT = Corner(True, True)
    TOP_LEFT = Corner(False, True)
    BOTTOM_RIGHT = Corner(True, False)
    TOP_RIGHT = Corner(False, False)


__all__ = ["Corner", "Corners"]
