"""Saturation fraction.

Status: v0.1 DRAFT. Definition to be finalised by Suyog in docs/design.md.
"""

from __future__ import annotations

import numpy as np


def saturation_fraction(
    channel: np.ndarray,
    saturation_value: float | None = None,
    mask: np.ndarray | None = None,
) -> dict:
    """Fraction of pixels at or above the saturation value.

    Formula
    -------
    fraction_all_pixels    = count(channel >= s) / count(all pixels)
    fraction_tissue_pixels = count(channel >= s AND mask) / count(mask)
    where s defaults to the maximum value of the integer dtype
    (255 for uint8, 65535 for uint16).

    Inputs
    ------
    channel : 2-D array (y, x).
    saturation_value : override for s. REQUIRED for float images, and
        strongly advised when the detector depth is lower than the file's
        container depth (e.g. 12-bit data stored as uint16 saturates at
        4095, which the default of 65535 would never detect).
    mask : optional tissue mask; adds the tissue-only fraction.

    Limitations
    -----------
    - The default s is the container maximum, not the detector maximum.
    - Images that were rescaled, background-subtracted or compressed after
      acquisition may have clipped values below s that this cannot see.
    - Counts pixels, not saturated objects/cells.
    """
    channel = np.asarray(channel)
    if saturation_value is None:
        if not np.issubdtype(channel.dtype, np.integer):
            return {
                "saturation_value": None,
                "fraction_all_pixels": None,
                "fraction_tissue_pixels": None,
                "n_saturated_pixels": None,
                "status": "saturation_value_required_for_float_image",
            }
        saturation_value = int(np.iinfo(channel.dtype).max)
        source = "dtype_max"
    else:
        source = "user"

    saturated = channel >= saturation_value
    out = {
        "saturation_value": saturation_value,
        "saturation_value_source": source,
        "fraction_all_pixels": float(saturated.mean()),
        "n_saturated_pixels": int(saturated.sum()),
        "fraction_tissue_pixels": None,
        "status": "ok",
    }
    if mask is not None:
        mask = np.asarray(mask, dtype=bool)
        if mask.any():
            out["fraction_tissue_pixels"] = float(saturated[mask].mean())
        else:
            out["status"] = "ok_no_tissue_for_tissue_fraction"
    return out
