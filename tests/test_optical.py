"""Unit tests for optical spectral index analysis and plain-language descriptions."""

import pytest
from src.config import Config
from src.core.optical import generate_similarity_description


def test_similarity_description_all_three_similar():
    """When NDVI, NDBI, and NDMI are all within threshold, all three should be listed."""
    ref = {"ndvi": 0.45, "ndbi": -0.15, "ndmi": 0.25}
    match = {"ndvi": 0.48, "ndbi": -0.12, "ndmi": 0.22}  # All deltas <= 0.03 <= 0.12

    res = generate_similarity_description(ref, match, threshold=0.12)
    assert len(res["similar_traits"]) == 3
    assert "vegetation" in res["similar_traits"]
    assert "built_up" in res["similar_traits"]
    assert "moisture" in res["similar_traits"]
    assert "comparable vegetation density" in res["text"]
    assert "similar built-up density" in res["text"]
    assert "comparable seasonal moisture" in res["text"]


def test_similarity_description_two_similar():
    """When two indices match within threshold, sentence should join them with 'and'."""
    ref = {"ndvi": 0.50, "ndbi": -0.20, "ndmi": 0.30}
    match = {"ndvi": 0.52, "ndbi": 0.10, "ndmi": 0.31}  # ndvi & ndmi match, ndbi diff is 0.30

    res = generate_similarity_description(ref, match, threshold=0.12)
    assert len(res["similar_traits"]) == 2
    assert "vegetation" in res["similar_traits"]
    assert "moisture" in res["similar_traits"]
    assert "built_up" not in res["similar_traits"]
    assert "Both areas exhibit comparable vegetation density and comparable seasonal moisture." == res["text"]


def test_similarity_description_one_similar():
    """When only one index matches, sentence should mention only that trait."""
    ref = {"ndvi": 0.60, "ndbi": -0.30, "ndmi": 0.40}
    match = {"ndvi": 0.61, "ndbi": 0.10, "ndmi": 0.10}  # only ndvi matches

    res = generate_similarity_description(ref, match, threshold=0.12)
    assert len(res["similar_traits"]) == 1
    assert "vegetation" in res["similar_traits"]
    assert "Both areas exhibit comparable vegetation density." == res["text"]


def test_similarity_description_none_similar_fallback():
    """When no index clears threshold, sentence should fall back to safe latent space description."""
    ref = {"ndvi": 0.80, "ndbi": -0.40, "ndmi": 0.50}
    match = {"ndvi": 0.20, "ndbi": 0.20, "ndmi": -0.10}  # all diffs > 0.40

    res = generate_similarity_description(ref, match, threshold=0.12)
    assert len(res["similar_traits"]) == 0
    assert "Both areas share latent structural characteristics in the 64-D embedding space." == res["text"]


def test_optical_dataset_config():
    """Configuration should specify Harmonized Sentinel-2 and valid threshold."""
    assert Config.OPTICAL_DATASET_ID == "COPERNICUS/S2_SR_HARMONIZED"
    assert Config.INDEX_SIMILARITY_THRESHOLD == 0.12
