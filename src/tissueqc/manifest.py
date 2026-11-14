"""Reproducibility manifest attached to every QC report."""

from __future__ import annotations

import hashlib
import platform
import sys
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import numpy as np

from . import __version__
from .io import nominal_bit_depth


def sha256_file(path: str | Path, chunk_size: int = 1 << 20) -> str:
    """SHA-256 hex digest of the file's bytes (read in 1 MiB chunks)."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(chunk_size), b""):
            h.update(block)
    return h.hexdigest()


def _pkg_version(name: str) -> str | None:
    try:
        return version(name)
    except PackageNotFoundError:
        return None


def build_manifest(path: str | Path, image: np.ndarray, parameters: dict) -> dict:
    """Everything needed to re-run and verify a QC result.

    Contents
    --------
    - input: file name (not the full path, so reports can be shared without
      leaking local directory names), SHA-256 of the file bytes, file size,
      array shape as (channels, y, x), dtype and nominal bit depth.
    - software: tissueqc, Python, numpy, tifffile, scikit-image versions
      and the OS platform string.
    - parameters: every user-settable parameter as actually used.
    - timestamp_utc: ISO-8601 time the report was generated.

    Limitations
    -----------
    - The hash identifies the exact file, not the biological sample: a
      re-export of the same acquisition gets a different hash.
    - Acquisition metadata (exposure, objective, pixel size) is not yet
      read from OME-XML.
    """
    path = Path(path)
    return {
        "input": {
            "file_name": path.name,
            "sha256": sha256_file(path),
            "size_bytes": path.stat().st_size,
            "shape_cyx": list(image.shape),
            "n_channels": int(image.shape[0]),
            "dtype": str(image.dtype),
            "nominal_bit_depth": nominal_bit_depth(image.dtype),
        },
        "software": {
            "tissueqc": __version__,
            "python": sys.version.split()[0],
            "numpy": np.__version__,
            "tifffile": _pkg_version("tifffile"),
            "scikit-image": _pkg_version("scikit-image"),
            "platform": platform.platform(),
        },
        "parameters": parameters,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
