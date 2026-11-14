"""Tile-based intensity uniformity (coefficient of variation).

Status: v0.1 DRAFT. Definition to be finalised by Suyog in docs/design.md.
"""

from __future__ import annotations

import numpy as np


def tile_uniformity_cv(
    channel: np.ndarray,
    mask: np.ndarray,
    tile_size: int = 256,
    min_tissue_fraction: float = 0.5,
) -> dict:
    """Coefficient of variation of per-tile mean tissue intensity.

    Formula
    -------
    1. Split the image into non-overlapping square tiles of `tile_size`
       pixels. Partial tiles at the right/bottom edges are excluded.
    2. A tile is VALID if the fraction of its pixels in `mask` is
       >= `min_tissue_fraction`. Non-tissue tiles are dropped, never
       counted as zero.
    3. For each valid tile i: m_i = mean(channel[tile_i AND mask]).
    4. CV = sample std(m_i, ddof=1) / mean(m_i), over valid tiles only.

    Inputs
    ------
    channel : 2-D array (y, x).
    mask : boolean tissue mask, same shape.
    tile_size : tile edge length in pixels.
    min_tissue_fraction : tile validity cut-off, in [0, 1].

    Returns
    -------
    dict with value (CV or null), n_valid_tiles, n_total_tiles and status.
    Always read the CV together with n_valid_tiles.

    Limitations
    -----------
    - Confounds technical non-uniformity (illumination, stitching, staining
      gradients) with real biological heterogeneity across the tissue.
      Interpreting it needs a reference (e.g. a uniform control) — see the
      validation plan.
    - Depends on tile size and on pixel size in microns, which v0.1 does
      not read from metadata.
    - Fewer than 2 valid tiles -> null with status "too_few_valid_tiles".
    """
    channel = np.asarray(channel)
    mask = np.asarray(mask, dtype=bool)
    if mask.shape != channel.shape:
        raise ValueError("mask and channel must have the same shape")
    if tile_size < 1:
        raise ValueError("tile_size must be >= 1")
    if not 0.0 <= min_tissue_fraction <= 1.0:
        raise ValueError("min_tissue_fraction must be in [0, 1]")

    h, w = channel.shape
    ny, nx = h // tile_size, w // tile_size
    tile_means: list[float] = []
    for iy in range(ny):
        for ix in range(nx):
            sl = (slice(iy * tile_size, (iy + 1) * tile_size), slice(ix * tile_size, (ix + 1) * tile_size))
            tm = mask[sl]
            if tm.any() and tm.mean() >= min_tissue_fraction:
                tile_means.append(float(channel[sl][tm].mean(dtype=np.float64)))

    out = {
        "value": None,
        "n_valid_tiles": len(tile_means),
        "n_total_tiles": ny * nx,
        "tile_size": tile_size,
        "min_tissue_fraction": min_tissue_fraction,
        "ddof": 1,
        "edge_pixels_excluded": int(h * w - ny * nx * tile_size * tile_size),
        "mean_of_tile_means": None,
        "status": "ok",
    }
    if ny * nx == 0:
        out["status"] = "image_smaller_than_tile"
        return out
    if len(tile_means) < 2:
        out["status"] = "too_few_valid_tiles"
        return out

    arr = np.asarray(tile_means)
    mu = float(arr.mean())
    out["mean_of_tile_means"] = mu
    if mu == 0:
        out["status"] = "mean_zero"
        return out
    out["value"] = float(arr.std(ddof=1) / mu)
    return out
