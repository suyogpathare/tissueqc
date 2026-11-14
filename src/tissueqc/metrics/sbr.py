"""Signal-to-background ratio (descriptive).

Status: v0.1 DRAFT. Definition to be finalised by Suyog in docs/design.md.
"""

from __future__ import annotations

import numpy as np


def signal_to_background(
    channel: np.ndarray,
    mask: np.ndarray,
    background: np.ndarray | None = None,
) -> dict:
    """Descriptive signal-to-background ratio for one channel.

    Formula
    -------
    SBR = mean(channel[mask]) / median(B)
    where B is either
      - the non-tissue pixels of the same image, channel[~mask] (default), or
      - all pixels of a matching channel from a separate control image
        (e.g. no-primary or unstained section), when `background` is given.

    This is labelled DESCRIPTIVE: it is not a specificity measure, and it
    is not comparable across instruments, exposures or markers without
    the validation described in docs/design.md.

    Inputs
    ------
    channel : 2-D array (y, x).
    mask : boolean tissue mask, same shape as `channel`.
    background : optional 2-D control-image channel.

    Limitations
    -----------
    - Depends entirely on the mask: a poor mask leaks tissue into B or
      glass into the signal.
    - Same-image background is glass/mounting medium, not tissue
      autofluorescence. A control image is closer to "non-specific"
      background but must be acquired with matched settings.
    - If median(B) is 0 (common after background subtraction or for
      clipped dark offsets) the ratio is undefined; the value is reported
      as null with status "background_median_zero", never as infinity.
    - Mean signal is sensitive to a few very bright pixels (e.g. debris).
    - Which pixels of a control image to use (whole field vs. its own
      tissue mask) is an open design decision for Suyog.
    """
    channel = np.asarray(channel)
    mask = np.asarray(mask, dtype=bool)
    if mask.shape != channel.shape:
        raise ValueError("mask and channel must have the same shape")

    out = {
        "value": None,
        "label": "descriptive",
        "mean_tissue": None,
        "median_background": None,
        "background_source": "control_image" if background is not None else "non_tissue_pixels",
        "n_tissue_pixels": int(mask.sum()),
        "n_background_pixels": None,
        "status": "ok",
    }

    if not mask.any():
        out["status"] = "no_tissue_pixels"
        return out

    bg = np.asarray(background).ravel() if background is not None else channel[~mask]
    out["n_background_pixels"] = int(bg.size)
    if bg.size == 0:
        out["status"] = "no_background_pixels"
        return out

    mean_tissue = float(channel[mask].mean(dtype=np.float64))
    median_bg = float(np.median(bg))
    out["mean_tissue"] = mean_tissue
    out["median_background"] = median_bg
    if median_bg == 0:
        out["status"] = "background_median_zero"
        return out

    out["value"] = mean_tissue / median_bg
    return out
