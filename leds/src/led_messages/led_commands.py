from dataclasses import dataclass
from typing import Tuple, List


@dataclass
class FillAll(object):
    """
    Fill every LED with this value
    """
    payload: Tuple[int, int, int]


@dataclass
class Zipper(object):
    """
    Cycle through colors
    """
    payload: float


@dataclass
class SetPixels(object):
    """
    Supply values for each color
    """
    payload: List[Tuple[int, int, int]]
