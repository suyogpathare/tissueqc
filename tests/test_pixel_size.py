"""OME pixel size reading and µm-based tile size."""

import json

import numpy as np
import pytest
import tifffile

from tissueqc.cli import main
from tissueqc.io import read_pixel_size, tile_size_from_microns
from tissueqc.synthetic import box_image


def _ome(tmp_path, px=0.5, py=None, name="ome.ome.tif"):
    p = tmp_path / name
    meta = {"axes": "YX", "PhysicalSizeX": px, "PhysicalSizeY": py if py is not None else px}
    tifffile.imwrite(p, box_image(), ome=True, metadata=meta)
    return p


def test_reads_ome_pixel_size(tmp_path):
    ps = read_pixel_size(_ome(tmp_path, px=0.2125))
    assert ps["x"] == pytest.approx(0.2125)
    assert ps["y"] == pytest.approx(0.2125)
    assert ps["unit"] in {"µm", "um"}


def test_plain_tiff_has_no_pixel_size(tmp_path):
    p = tmp_path / "plain.tif"
    tifffile.imwrite(p, box_image())
    assert read_pixel_size(p) is None


def test_micron_conversion_known_answer():
    # 5 µm tiles at 0.5 µm/px -> 10 px
    assert tile_size_from_microns(5, {"x": 0.5, "y": 0.5, "unit": "µm"}) == 10


@pytest.mark.parametrize("ps", [
    None,
    {"x": 0.5, "y": 0.5, "unit": "nm"},
    {"x": 0.5, "y": 0.6, "unit": "µm"},
])
def test_micron_conversion_refuses_unknown_or_ambiguous(ps):
    with pytest.raises(ValueError):
        tile_size_from_microns(5, ps)


def test_cli_tile_size_um(tmp_path):
    p = _ome(tmp_path, px=0.5)
    out = tmp_path / "r.json"
    assert main([str(p), "-o", str(out), "--tile-size-um", "5"]) == 0
    rep = json.loads(out.read_text())
    assert rep["manifest"]["parameters"]["tile_size"] == 10
    assert rep["manifest"]["parameters"]["tile_size_um"] == 5
    assert rep["manifest"]["input"]["pixel_size"]["x"] == pytest.approx(0.5)
    assert rep["channels"][0]["tile_uniformity"]["n_total_tiles"] == 100


def test_cli_tile_size_um_without_metadata_fails_cleanly(tmp_path):
    p = tmp_path / "plain.tif"
    tifffile.imwrite(p, box_image())
    assert main([str(p), "--tile-size-um", "5"]) == 2
