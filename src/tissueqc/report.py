"""Run all v0.1 metrics on one image and assemble the JSON-ready report."""

from __future__ import annotations

from pathlib import Path

from .io import load_image
from .manifest import build_manifest, sha256_file
from .metrics import saturation_fraction, signal_to_background, tile_uniformity_cv, tissue_mask

REPORT_SCHEMA_VERSION = "0.1"


def run_qc(
    image_path: str | Path,
    thresholds: dict[int, float] | None = None,
    saturation_value: float | None = None,
    tile_size: int = 256,
    min_tissue_fraction: float = 0.5,
    background_path: str | Path | None = None,
    channel_axis: int = 0,
    channel_names: list[str] | None = None,
) -> dict:
    """Compute every metric for every channel of `image_path`.

    thresholds maps channel index -> manual mask threshold; channels not
    listed use Otsu. background_path is an optional control image with the
    same number of channels, used for signal-to-background.
    """
    thresholds = thresholds or {}
    image = load_image(image_path, channel_axis=channel_axis)
    n_ch = image.shape[0]

    background = None
    if background_path is not None:
        background = load_image(background_path, channel_axis=channel_axis)
        if background.shape[0] != n_ch:
            raise ValueError(
                f"Control image has {background.shape[0]} channels, image has {n_ch}"
            )

    if channel_names is not None and len(channel_names) != n_ch:
        raise ValueError(f"Got {len(channel_names)} channel names for {n_ch} channels")

    bad = [c for c in thresholds if not 0 <= c < n_ch]
    if bad:
        raise ValueError(f"Threshold given for non-existent channel(s) {bad}; image has {n_ch}")

    channels = []
    for c in range(n_ch):
        ch = image[c]
        mask, mask_info = tissue_mask(ch, threshold=thresholds.get(c))
        channels.append({
            "index": c,
            "name": channel_names[c] if channel_names else None,
            "tissue_mask": mask_info,
            "saturation": saturation_fraction(ch, saturation_value=saturation_value, mask=mask),
            "signal_to_background": signal_to_background(
                ch, mask, background=None if background is None else background[c]
            ),
            "tile_uniformity": tile_uniformity_cv(
                ch, mask, tile_size=tile_size, min_tissue_fraction=min_tissue_fraction
            ),
        })

    parameters = {
        "thresholds": {str(k): v for k, v in sorted(thresholds.items())},
        "saturation_value": saturation_value,
        "tile_size": tile_size,
        "min_tissue_fraction": min_tissue_fraction,
        "background_image": Path(background_path).name if background_path else None,
        "channel_axis": channel_axis,
    }
    manifest = build_manifest(image_path, image, parameters)
    if background_path is not None:
        manifest["background_input"] = {
            "file_name": Path(background_path).name,
            "sha256": sha256_file(background_path),
        }

    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "status_note": "v0.1 draft metrics; definitions not yet validated (see docs/design.md)",
        "manifest": manifest,
        "channels": channels,
    }
