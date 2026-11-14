"""Per-channel tissue mask.

Status: v0.1 DRAFT. Definition to be finalised by Suyog in docs/design.md.
"""

from __future__ import annotations

import numpy as np
from skimage.filters import threshold_otsu


def tissue_mask(channel: np.ndarray, threshold: float | None = None) -> tuple[np.ndarray, dict]:
    """Boolean mask of "tissue" pixels for one channel.

    Formula
    -------
    mask = channel > t
    where t is Otsu's threshold of the channel's intensity histogram
    (skimage.filters.threshold_otsu), or a user-supplied manual threshold.
    Pixels exactly equal to t are counted as non-tissue.

    Inputs
    ------
    channel : 2-D array (y, x), any numeric dtype.
    threshold : optional manual override. When given, Otsu is not run.

    Returns
    -------
    (mask, info) where info records the method, the threshold used, the
    tissue fraction and a status string.

    Limitations
    -----------
    - Otsu assumes a roughly bimodal histogram (tissue vs. glass). Sparse
      markers, very dim channels or tissue covering most of the field can
      give a threshold that separates "bright cells" from "everything
      else" rather than tissue from background.
    - Each channel is masked independently; a consensus / nuclear-channel
      mask is a possible v0.2 option (design decision for Suyog).
    - A constant image has no Otsu threshold: an empty mask is returned
      with status "undefined_constant_image", never a guessed mask.
    - No smoothing, hole filling or small-object removal yet.
    """
    channel = np.asarray(channel)
    if channel.ndim != 2:
        raise ValueError(f"tissue_mask expects a 2-D channel, got shape {channel.shape}")

    if threshold is not None:
        method, t = "manual", float(threshold)
    else:
        method = "otsu"
        if channel.size == 0 or channel.min() == channel.max():
            mask = np.zeros(channel.shape, dtype=bool)
            return mask, {
                "method": method,
                "threshold": None,
                "tissue_fraction": 0.0,
                "n_tissue_pixels": 0,
                "status": "undefined_constant_image",
            }
        t = float(threshold_otsu(channel))

    mask = channel > t
    n = int(mask.sum())
    return mask, {
        "method": method,
        "threshold": t,
        "tissue_fraction": n / mask.size,
        "n_tissue_pixels": n,
        "status": "ok" if n > 0 else "no_tissue_detected",
    }
