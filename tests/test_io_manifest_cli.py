"""Image loading, reproducibility manifest and the end-to-end CLI."""

import hashlib
import json
from datetime import datetime

import numpy as np
import pytest
import tifffile

from tissueqc import __version__
from tissueqc.cli import main
from tissueqc.io import as_cyx, load_image
from tissueqc.synthetic import box_image, multichannel


# ---------- io ----------

def test_2d_becomes_single_channel():
    assert as_cyx(np.zeros((8, 9))).shape == (1, 8, 9)


def test_channel_axis_last_is_moved_first():
    assert as_cyx(np.zeros((8, 9, 3)), channel_axis=2).shape == (3, 8, 9)


def test_4d_rejected():
    with pytest.raises(ValueError):
        as_cyx(np.zeros((2, 3, 8, 9)))


def test_singleton_axes_are_squeezed(tmp_path):
    p = tmp_path / "z1.tif"
    tifffile.imwrite(p, np.zeros((1, 2, 16, 16), dtype=np.uint16))
    assert load_image(p).shape == (2, 16, 16)


# ---------- manifest + CLI ----------

def _write(tmp_path, name, arr):
    p = tmp_path / name
    tifffile.imwrite(p, arr)
    return p


def _run(tmp_path, img_path, *extra):
    out = tmp_path / "report.json"
    code = main([str(img_path), "-o", str(out), "--tile-size", "10", *extra])
    return code, (json.loads(out.read_text()) if out.exists() else None)


@pytest.mark.parametrize("dtype,bits", [(np.uint8, 8), (np.uint16, 16)])
def test_single_channel_report_and_manifest(tmp_path, dtype, bits):
    img = box_image(background=10, tissue=200, dtype=dtype)
    p = _write(tmp_path, "single.tif", img)
    code, rep = _run(tmp_path, p)
    assert code == 0
    m = rep["manifest"]
    assert m["input"]["sha256"] == hashlib.sha256(p.read_bytes()).hexdigest()
    assert m["input"]["shape_cyx"] == [1, 100, 100]
    assert m["input"]["nominal_bit_depth"] == bits
    assert m["input"]["file_name"] == "single.tif"  # name only, no local path
    assert m["software"]["tissueqc"] == __version__
    assert m["parameters"]["tile_size"] == 10
    datetime.fromisoformat(m["timestamp_utc"])
    ch = rep["channels"][0]
    assert ch["signal_to_background"]["value"] == pytest.approx(20.0)
    # Box spans px 25-75, so along each axis tiles 2..7 touch it: tiles 3-6 are
    # fully inside, tiles 2 and 7 are half inside (0.5 >= cut-off, kept).
    # 6x6 = 36, minus 4 corner tiles at 0.25 tissue -> 32 valid of 100.
    assert ch["tile_uniformity"]["n_valid_tiles"] == 32
    assert ch["tile_uniformity"]["n_total_tiles"] == 100


def test_multichannel_with_names_and_manual_threshold(tmp_path):
    a = box_image(background=100, tissue=1000)
    b = box_image(background=50, tissue=500)
    p = _write(tmp_path, "multi.tif", multichannel(a, b))
    code, rep = _run(tmp_path, p, "--threshold", "1=300", "--channel-names", "DAPI,CD3")
    assert code == 0
    assert [c["name"] for c in rep["channels"]] == ["DAPI", "CD3"]
    assert rep["channels"][0]["tissue_mask"]["method"] == "otsu"
    assert rep["channels"][1]["tissue_mask"]["method"] == "manual"
    assert rep["channels"][1]["signal_to_background"]["value"] == pytest.approx(10.0)
    assert rep["manifest"]["parameters"]["thresholds"] == {"1": 300.0}


@pytest.mark.parametrize("value", [0, 65535])
def test_blank_and_fully_saturated_images_do_not_crash(tmp_path, value):
    p = _write(tmp_path, "flat.tif", np.full((40, 40), value, dtype=np.uint16))
    code, rep = _run(tmp_path, p)
    assert code == 0
    ch = rep["channels"][0]
    assert ch["tissue_mask"]["status"] == "undefined_constant_image"
    assert ch["signal_to_background"]["value"] is None
    assert ch["tile_uniformity"]["value"] is None
    assert ch["saturation"]["fraction_all_pixels"] == (1.0 if value == 65535 else 0.0)


def test_control_background_image(tmp_path):
    p = _write(tmp_path, "img.tif", box_image(background=100, tissue=1000))
    c = _write(tmp_path, "ctrl.tif", np.full((100, 100), 25, dtype=np.uint16))
    code, rep = _run(tmp_path, p, "--background-image", str(c))
    assert code == 0
    assert rep["channels"][0]["signal_to_background"]["value"] == pytest.approx(40.0)
    assert rep["manifest"]["background_input"]["sha256"] == hashlib.sha256(c.read_bytes()).hexdigest()


def test_report_is_strict_json(tmp_path):
    """No NaN/Infinity tokens, which many JSON readers reject."""
    p = _write(tmp_path, "zero_bg.tif", box_image(background=0, tissue=1000))
    out = tmp_path / "r.json"
    assert main([str(p), "-o", str(out)]) == 0
    json.loads(out.read_text(), parse_constant=lambda c: pytest.fail(f"non-strict JSON: {c}"))


def test_missing_file_and_bad_threshold_channel(tmp_path):
    assert main([str(tmp_path / "nope.tif")]) == 2
    p = _write(tmp_path, "img.tif", box_image())
    assert main([str(p), "--threshold", "5=100"]) == 2


def test_default_output_path(tmp_path):
    p = _write(tmp_path, "img.tif", box_image())
    assert main([str(p)]) == 0
    assert (tmp_path / "img.tif.qc.json").exists()
