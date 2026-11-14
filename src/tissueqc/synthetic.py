"""Synthetic images with known answers, for tests and for checking the metrics by hand.

Each generator returns an image whose correct metric values can be worked
out on paper, so a test failure means the code disagrees with arithmetic.
"""

from __future__ import annotations

import numpy as np


def box_image(
    shape: tuple[int, int] = (100, 100),
    background: float = 100,
    tissue: float = 1000,
    box: tuple[int, int, int, int] = (25, 75, 25, 75),
    dtype=np.uint16,
) -> np.ndarray:
    """Flat background with one flat rectangular 'tissue' region.

    box is (y0, y1, x0, x1). Known answers: tissue fraction =
    box area / image area; SBR = tissue / background.
    """
    img = np.full(shape, background, dtype=dtype)
    y0, y1, x0, x1 = box
    img[y0:y1, x0:x1] = tissue
    return img


def tiled_image(
    tile_values: np.ndarray,
    tile_size: int,
    dtype=np.uint16,
) -> np.ndarray:
    """Image made of flat tiles; tile (i, j) has value tile_values[i, j].

    Known answer: per-tile means equal tile_values, so the uniformity CV of
    the tiles above a threshold can be computed directly with numpy.
    """
    tv = np.asarray(tile_values)
    return np.kron(tv, np.ones((tile_size, tile_size))).astype(dtype)


def multichannel(*channels: np.ndarray) -> np.ndarray:
    """Stack 2-D channels into (channels, y, x)."""
    return np.stack(channels, axis=0)
