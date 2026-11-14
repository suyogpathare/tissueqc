"""Saturation fraction: known-answer and edge-case tests."""

import numpy as np
import pytest

from tissueqc.metrics import saturation_fraction
from tissueqc.synthetic import box_image


def _box_mask():
    m = np.zeros((100, 100), dtype=bool)
    m[25:75, 25:75] = True
    return m


def test_known_count_uint16():
    img = box_image(dtype=np.uint16)
    img[30, 30:40] = 65535  # 10 saturated pixels, all inside the box
    out = saturation_fraction(img, mask=_box_mask())
    assert out["saturation_value"] == 65535
    assert out["saturation_value_source"] == "dtype_max"
    assert out["n_saturated_pixels"] == 10
    assert out["fraction_all_pixels"] == pytest.approx(10 / 10_000)
    assert out["fraction_tissue_pixels"] == pytest.approx(10 / 2_500)


def test_uint8_uses_255():
    img = np.full((10, 10), 255, dtype=np.uint8)
    out = saturation_fraction(img)
    assert out["saturation_value"] == 255
    assert out["fraction_all_pixels"] == 1.0


def test_blank_image_has_zero_saturation():
    out = saturation_fraction(np.zeros((20, 20), dtype=np.uint16))
    assert out["fraction_all_pixels"] == 0.0


def test_12bit_data_in_16bit_container_needs_override():
    img = np.full((10, 10), 4095, dtype=np.uint16)
    assert saturation_fraction(img)["fraction_all_pixels"] == 0.0  # default misses it
    assert saturation_fraction(img, saturation_value=4095)["fraction_all_pixels"] == 1.0


def test_float_image_requires_explicit_value():
    out = saturation_fraction(np.ones((5, 5), dtype=np.float32))
    assert out["fraction_all_pixels"] is None
    assert out["status"] == "saturation_value_required_for_float_image"


def test_empty_mask_gives_null_tissue_fraction():
    img = box_image()
    out = saturation_fraction(img, mask=np.zeros(img.shape, dtype=bool))
    assert out["fraction_tissue_pixels"] is None
    assert out["fraction_all_pixels"] == 0.0
