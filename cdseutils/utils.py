"""Utility functions and classes."""

from typing import NamedTuple


class BBox(NamedTuple):
    """Bounding box."""

    left: float = -180
    bottom: float = -90
    right: float = +180
    top: float = +90


def deg2dms(value: float) -> tuple[int, int, float]:
    """Convert angles from decimal degrees to (deg, min, sec) format."""
    sign = -1 if value < 0 else 1
    minutes, seconds = divmod(abs(value) * 3600, 60)
    degrees, minutes = divmod(minutes, 60)
    return sign * int(degrees), int(minutes), seconds


def dms2deg(deg: int, minutes: int, seconds: float):
    """Convert angles from (deg, min, sec) to decimal degree format."""
    return deg + minutes / 60 + seconds / 3600
