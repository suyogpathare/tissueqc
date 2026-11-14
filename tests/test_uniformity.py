"""Tile uniformity CV: known-answer and edge-case tests."""

import numpy as np
import pytest

from tissueqc.metrics import tile_uniformity_cv
from tissueqc.synthetic import tiled_image


def test_perfectly_uniform_tissue_has_cv_zero():
    img = tiled_image(np.full((3, 3), 1000), tile_size=10)
    out = tile_uniformity_cv(img, img > 0, tile_size=10)
    assert out["value"] == pytest.approx(0.0)
    assert out["n_valid_tiles"] == 9
    assert out["n_total_tiles"] == 9


def test_known_cv_and_empty_tiles_are_excluded_not_zero_filled():
    # Tiles 100, 200, 300 are tissue; the 0 tile is glass.
    img = tiled_image(np.array([[100, 200], [300, 0]]), tile_size=10)
    out = tile_uniformity_cv(img, img > 50, tile_size=10)
    # std([100, 200, 300], ddof=1) = 100; mean = 200  ->  CV = 0.5
    assert out["value"] == pytest.approx(0.5)
    assert out["n_valid_tiles"] == 3
    assert out["n_total_tiles"] == 4
    # Had the empty tile been zero-filled the CV would be:
    zero_filled = np.std([100, 200, 300, 0], ddof=1) / np.mean([100, 200, 300, 0])
    assert out["value"] != pytest.approx(zero_filled)


def test_only_tissue_pixels_inside_a_tile_are_averaged():
    img = np.zeros((20, 20), dtype=np.uint16)
    img[:, :] = 10  # glass
    img[0:10, 0:8] = 1000  # tile (0,0): 80% tissue at 1000
    img[0:10, 10:18] = 2000  # tile (0,1): 80% tissue at 2000
    out = tile_uniformity_cv(img, img > 100, tile_size=10, min_tissue_fraction=0.5)
    assert out["n_valid_tiles"] == 2
    assert out["mean_of_tile_means"] == pytest.approx(1500)  # glass pixels not averaged in


def test_min_tissue_fraction_cutoff():
    img = np.full((10, 20), 10, dtype=np.uint16)
    img[:, 0:10] = 1000  # tile 0: 100% tissue
    img[0:3, 10:20] = 1000  # tile 1: 30% tissue
    mask = img > 100
    assert tile_uniformity_cv(img, mask, tile_size=10, min_tissue_fraction=0.5)["n_valid_tiles"] == 1
    assert tile_uniformity_cv(img, mask, tile_size=10, min_tissue_fraction=0.25)["n_valid_tiles"] == 2


def test_partial_edge_tiles_are_excluded_and_counted():
    img = np.full((25, 25), 1000, dtype=np.uint16)
    out = tile_uniformity_cv(img, img > 0, tile_size=10)
    assert out["n_total_tiles"] == 4
    assert out["edge_pixels_excluded"] == 25 * 25 - 4 * 100


def test_single_valid_tile_gives_null():
    img = tiled_image(np.array([[1000, 0], [0, 0]]), tile_size=10)
    out = tile_uniformity_cv(img, img > 0, tile_size=10)
    assert out["value"] is None
    assert out["n_valid_tiles"] == 1
    assert out["status"] == "too_few_valid_tiles"


def test_no_tissue_gives_null():
    img = np.zeros((40, 40), dtype=np.uint16)
    out = tile_uniformity_cv(img, np.zeros(img.shape, bool), tile_size=10)
    assert out["value"] is None
    assert out["n_valid_tiles"] == 0
    assert out["n_total_tiles"] == 16


def test_image_smaller_than_tile():
    img = np.ones((5, 5), dtype=np.uint16)
    out = tile_uniformity_cv(img, img > 0, tile_size=10)
    assert out["status"] == "image_smaller_than_tile"
    assert out["value"] is None
