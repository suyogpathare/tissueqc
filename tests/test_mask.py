"""Tissue mask: known-answer and edge-case tests."""

import numpy as np
import pytest

from tissueqc.metrics import tissue_mask
from tissueqc.synthetic import box_image


@pytest.mark.parametrize("dtype,bg,fg", [(np.uint8, 10, 200), (np.uint16, 100, 1000)])
def test_otsu_recovers_box_exactly(dtype, bg, fg):
    img = box_image(background=bg, tissue=fg, dtype=dtype)  # 50x50 box in 100x100
    mask, info = tissue_mask(img)
    expected = img == fg
    assert np.array_equal(mask, expected)
    assert info["method"] == "otsu"
    assert info["tissue_fraction"] == pytest.approx(0.25)
    assert info["n_tissue_pixels"] == 2500
    assert info["status"] == "ok"


def test_manual_threshold_overrides_otsu():
    img = box_image(background=100, tissue=1000)
    mask, info = tissue_mask(img, threshold=500)
    assert info["method"] == "manual"
    assert info["threshold"] == 500
    assert mask.sum() == 2500


def test_manual_threshold_equal_to_value_is_not_tissue():
    img = box_image(background=100, tissue=1000)
    mask, _ = tissue_mask(img, threshold=1000)  # strict '>' convention
    assert mask.sum() == 0


def test_manual_threshold_above_everything_reports_no_tissue():
    mask, info = tissue_mask(box_image(), threshold=5000)
    assert not mask.any()
    assert info["status"] == "no_tissue_detected"


@pytest.mark.parametrize("value", [0, 65535])
def test_constant_image_has_no_otsu_threshold(value):
    """Blank (all 0) and fully saturated (all max) images: no guessed mask."""
    img = np.full((50, 50), value, dtype=np.uint16)
    mask, info = tissue_mask(img)
    assert not mask.any()
    assert info["threshold"] is None
    assert info["status"] == "undefined_constant_image"


def test_rejects_non_2d():
    with pytest.raises(ValueError):
        tissue_mask(np.zeros((2, 10, 10)))
