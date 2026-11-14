"""Reading TIFF images into a standard (channels, y, x) array."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import tifffile


def load_image(path: str | Path, channel_axis: int = 0) -> np.ndarray:
    """Read a TIFF and return an array shaped (n_channels, height, width).

    Inputs
    ------
    path : TIFF / OME-TIFF file. Only the first series at full resolution is
        read (for pyramidal OME-TIFFs, that is level 0).
    channel_axis : which axis holds channels when the image is 3-D.
        Ignored for 2-D images, which are treated as a single channel.

    Limitations
    -----------
    - Singleton axes (e.g. a Z or T of length 1) are squeezed away first.
      Real Z-stacks or time series (>3 non-singleton axes) are rejected,
      not projected.
    - The whole image is loaded into memory. Large whole-slide images may
      need tiled/lazy reading in a later version.
    """
    arr = np.squeeze(tifffile.imread(str(path)))
    return as_cyx(arr, channel_axis=channel_axis)


def as_cyx(arr: np.ndarray, channel_axis: int = 0) -> np.ndarray:
    """Coerce a 2-D or 3-D array to (channels, y, x)."""
    arr = np.asarray(arr)
    if arr.ndim == 2:
        return arr[np.newaxis, ...]
    if arr.ndim == 3:
        return np.moveaxis(arr, channel_axis, 0)
    raise ValueError(
        f"Expected a 2-D or 3-D image after squeezing, got shape {arr.shape}. "
        "Z-stacks and time series are not supported in v0.1."
    )


def nominal_bit_depth(dtype: np.dtype) -> int:
    """Bits per pixel of the storage container (e.g. 16 for uint16).

    This is the *container* depth, not the detector depth: a 12-bit camera
    image saved as uint16 reports 16 here.
    """
    return int(np.dtype(dtype).itemsize * 8)
