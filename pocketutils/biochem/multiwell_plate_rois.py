import typing
from dataclasses import dataclass
from enum import Enum
from typing import Dict

from pocketutils.core.exceptions import OutOfRangeError, ErrorUtils


class Edge(Enum):
    left = 1
    right = 2
    top = 3
    bottom = 4


class Axis(Enum):
    horizontal = 1
    vertical = 2


@ErrorUtils.args(edge=Edge, axis=Axis)
class RoiError(OutOfRangeError):
    """The ROI is invalid."""


@dataclass(frozen=True, order=True)
class WellRoi:
    row: int
    column: int
    x0: int
    y0: int
    x1: int
    y1: int

    def __post_init__(self):
        if self.row < 0:
            raise OutOfRangeError(f"Row ({self.row}) < 0", value=self.row)
        if self.column < 0:
            raise OutOfRangeError(f"Column ({self.column}) < 0", value=self.column)
        if self.x0 < 0:
            raise RoiError(f"x0 ({self.x0}) < 0", edge=Edge.left)
        if self.y0 < 0:
            raise RoiError(f"y0 ({self.y0}) < 0", edge=Edge.top)
        if self.x0 >= self.x1:
            raise RoiError(f"x0 ({self.x0}) >= x1 ({self.x1})", axis=Axis.horizontal)
        if self.y0 >= self.y1:
            raise RoiError(f"y0 ({self.y0}) >= y1 ({self.y1})", axis=Axis.vertical)

    def __repr__(self) -> str:
        return f"{self.row},{self.column}=({self.x0},{self.y0})→({self.x1},{self.y1})"

    def __str__(self):
        return repr(self)


@dataclass(frozen=True, repr=True, order=True)
class PlateRois:
    n_rows: int
    n_columns: int
    image_roi: WellRoi
    top_left_roi: WellRoi
    padx: float
    pady: float

    @property
    def well_rois(self):
        return self._get_roi_coordinates(self.top_left_roi, self.padx, self.pady)

    def __iter__(self):
        return iter(self.well_rois.keys())

    def __len__(self):
        return len(self.well_rois)

    def __getitem__(self, item):
        try:
            return self.well_rois[item[0], item[1]]
        except (IndexError, AttributeError):
            raise TypeError("Must look up well ROIs by (row, column) tuple indices.")

    def _get_roi_coordinates(
        self, top_left_roi: WellRoi, padx: float, pady: float
    ) -> Dict[typing.Tuple[int, int], WellRoi]:
        tl = top_left_roi
        width = top_left_roi.x1 - top_left_roi.x0
        height = top_left_roi.y1 - top_left_roi.y0
        wells_x_edge = tl.x0 + self.n_columns * width + (self.n_columns - 1) * padx
        wells_y_edge = tl.y0 + self.n_rows * height + (self.n_rows - 1) * pady
        # make sure the wells don't extend outside the image bounds
        if tl.x0 < self.image_roi.x0:
            raise RoiError(f"{tl.x0} < {self.image_roi.x0}", edge=Edge.left)
        if wells_x_edge > self.image_roi.x1:
            raise RoiError(f"{wells_x_edge} < {self.image_roi.x1}", edge=Edge.right)
        if tl.y0 < self.image_roi.y0:
            raise RoiError(f"{tl.y0} < {self.image_roi.y0}", edge=Edge.top)
        if wells_y_edge > self.image_roi.y1:
            raise RoiError(f"{wells_y_edge} > {self.image_roi.y1}", edge=Edge.bottom)
        # now build
        rois = {}
        x = tl.x0
        y = tl.y0
        for row in range(0, self.n_rows):
            for column in range(0, self.n_columns):
                rois[(row, column)] = WellRoi(row, column, x, y, x + width, y + height)
                x += width + padx
            y += height + pady
            x = tl.x0
        return rois


__all__ = ["WellRoi", "PlateRois"]
