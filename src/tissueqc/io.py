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


_MICRON_UNITS = {"µm", "um", "micron", "μm"}


def read_pixel_size(path: str | Path) -> dict | None:
    """Physical pixel size from OME-XML metadata, or None if absent.

    Returns {"x": float, "y": float, "unit": str} using the Pixels
    element's PhysicalSizeX/Y and PhysicalSizeXUnit (OME's default unit is
    µm when the attribute is omitted).

    Limitations
    -----------
    - Only OME-TIFF metadata is read. ImageJ or plain-TIFF resolution tags
      are ignored, so many non-OME TIFFs return None.
    - The value is whatever the writing software stored; it is not checked
      against the instrument.
    """
    import xml.etree.ElementTree as ET

    with tifffile.TiffFile(str(path)) as tif:
        xml = tif.ome_metadata
    if not xml:
        return None
    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        return None
    pixels = next((el for el in root.iter() if el.tag.endswith("}Pixels") or el.tag == "Pixels"), None)
    if pixels is None or "PhysicalSizeX" not in pixels.attrib:
        return None
    x = float(pixels.attrib["PhysicalSizeX"])
    y = float(pixels.attrib.get("PhysicalSizeY", x))
    unit = pixels.attrib.get("PhysicalSizeXUnit", "µm")
    return {"x": x, "y": y, "unit": unit}


def tile_size_from_microns(tile_um: float, pixel_size: dict | None) -> int:
    """Convert a tile edge in µm to whole pixels: round(tile_um / pixel_x).

    Raises ValueError when the pixel size is unknown, not in µm, or the
    pixels are not square (x and y differ by more than 1%).
    """
    if pixel_size is None:
        raise ValueError("--tile-size-um needs a pixel size, but the image has no OME PhysicalSizeX")
    if pixel_size["unit"] not in _MICRON_UNITS:
        raise ValueError(f"pixel size unit is {pixel_size['unit']!r}, expected µm")
    x, y = pixel_size["x"], pixel_size["y"]
    if abs(x - y) > 0.01 * x:
        raise ValueError(f"non-square pixels ({x} x {y} µm) are not supported for --tile-size-um")
    return max(1, round(tile_um / x))


def nominal_bit_depth(dtype: np.dtype) -> int:
    """Bits per pixel of the storage container (e.g. 16 for uint16).

    This is the *container* depth, not the detector depth: a 12-bit camera
    image saved as uint16 reports 16 here.
    """
    return int(np.dtype(dtype).itemsize * 8)
