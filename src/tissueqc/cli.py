"""Command line: `tissueqc IMAGE.tif -o report.json`."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .report import run_qc


def _parse_threshold(text: str) -> tuple[int, float]:
    try:
        ch, val = text.split("=", 1)
        return int(ch), float(val)
    except ValueError:
        raise argparse.ArgumentTypeError(f"expected CHANNEL=VALUE (e.g. 0=500), got {text!r}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="tissueqc",
        description="Quantitative QC report for a multiplex fluorescence TIFF.",
    )
    p.add_argument("image", type=Path, help="input TIFF / OME-TIFF")
    p.add_argument("-o", "--output", type=Path, help="JSON report path (default: IMAGE.qc.json)")
    p.add_argument("--threshold", type=_parse_threshold, action="append", default=[],
                   metavar="CH=VALUE", help="manual tissue threshold for one channel (repeatable); others use Otsu")
    p.add_argument("--saturation-value", type=float, default=None,
                   help="pixel value treated as saturated (default: dtype max; required for float images)")
    p.add_argument("--tile-size", type=int, default=256, help="uniformity tile edge in pixels (default 256)")
    p.add_argument("--tile-size-um", type=float, default=None,
                   help="uniformity tile edge in µm; overrides --tile-size using the OME pixel size")
    p.add_argument("--min-tissue-fraction", type=float, default=0.5,
                   help="minimum tissue fraction for a tile to count (default 0.5)")
    p.add_argument("--background-image", type=Path, default=None,
                   help="optional control image (same channels) for signal-to-background")
    p.add_argument("--channel-axis", type=int, default=0, help="channel axis for 3-D TIFFs (default 0)")
    p.add_argument("--channel-names", default=None, help="comma-separated channel names")
    p.add_argument("--version", action="version", version=f"tissueqc {__version__}")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.image.exists():
        print(f"tissueqc: file not found: {args.image}", file=sys.stderr)
        return 2

    names = [n.strip() for n in args.channel_names.split(",")] if args.channel_names else None
    try:
        report = run_qc(
            args.image,
            thresholds=dict(args.threshold),
            saturation_value=args.saturation_value,
            tile_size=args.tile_size,
            min_tissue_fraction=args.min_tissue_fraction,
            background_path=args.background_image,
            channel_axis=args.channel_axis,
            channel_names=names,
            tile_size_um=args.tile_size_um,
        )
    except ValueError as e:
        print(f"tissueqc: {e}", file=sys.stderr)
        return 2

    out = args.output or args.image.with_name(args.image.name + ".qc.json")
    out.write_text(json.dumps(report, indent=2) + "\n")

    for ch in report["channels"]:
        label = ch["name"] or f"ch{ch['index']}"
        sbr = ch["signal_to_background"]["value"]
        uni = ch["tile_uniformity"]
        cv = uni["value"]
        sat = ch["saturation"]["fraction_all_pixels"]
        print(
            f"{label}: tissue={ch['tissue_mask']['tissue_fraction']:.3f} "
            f"saturated={'NA' if sat is None else f'{sat:.4f}'} "
            f"SBR={'NA' if sbr is None else f'{sbr:.2f}'} "
            f"CV={'NA' if cv is None else f'{cv:.3f}'} "
            f"({uni['n_valid_tiles']}/{uni['n_total_tiles']} tiles)",
            file=sys.stderr,
        )
    print(f"wrote {out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
