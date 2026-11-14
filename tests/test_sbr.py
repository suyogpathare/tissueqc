"""Signal-to-background: known-answer and edge-case tests."""

import numpy as np
import pytest

from tissueqc.metrics import signal_to_background
from tissueqc.synthetic import box_image


def _mask(img, fg):
    return img == fg


def test_known_ratio_same_image_background():
    img = box_image(background=100, tissue=1000)
    out = signal_to_background(img, _mask(img, 1000))
    assert out["value"] == pytest.approx(10.0)
    assert out["mean_tissue"] == pytest.approx(1000)
    assert out["median_background"] == pytest.approx(100)
    assert out["background_source"] == "non_tissue_pixels"
    assert out["label"] == "descriptive"
    assert out["n_background_pixels"] == 7500


def test_median_not_mean_for_background():
    img = box_image(background=100, tissue=1000)
    img[0, 0:10] = 60000  # a few bright debris pixels in the background
    out = signal_to_background(img, img == 1000)
    assert out["median_background"] == pytest.approx(100)  # median ignores them
    assert out["value"] == pytest.approx(10.0)


def test_control_image_background():
    img = box_image(background=100, tissue=1000)
    control = np.full((100, 100), 50, dtype=np.uint16)
    out = signal_to_background(img, img == 1000, background=control)
    assert out["background_source"] == "control_image"
    assert out["value"] == pytest.approx(20.0)


def test_zero_background_is_null_not_infinite():
    img = box_image(background=0, tissue=1000)
    out = signal_to_background(img, img == 1000)
    assert out["value"] is None
    assert out["status"] == "background_median_zero"


def test_no_tissue():
    img = box_image()
    out = signal_to_background(img, np.zeros(img.shape, dtype=bool))
    assert out["value"] is None
    assert out["status"] == "no_tissue_pixels"


def test_all_tissue_has_no_background():
    img = box_image()
    out = signal_to_background(img, np.ones(img.shape, dtype=bool))
    assert out["value"] is None
    assert out["status"] == "no_background_pixels"


def test_uint16_mean_does_not_overflow():
    img = np.full((200, 200), 65000, dtype=np.uint16)
    img[:, :100] = 10
    out = signal_to_background(img, img == 65000)
    assert out["mean_tissue"] == pytest.approx(65000)
