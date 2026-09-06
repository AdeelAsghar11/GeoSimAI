"""Unit tests for empirical evaluation data structures and metric computation."""

import pytest
from src.config import Config
from src.core.evaluation import GROUND_TRUTH_SITES


def test_ground_truth_categories():
    """Verify all 6 land-cover categories are present in benchmark sites."""
    expected_categories = [
        "WATER",
        "URBAN_GREENERY",
        "NATURAL_FOREST",
        "AGRICULTURE",
        "DENSE_URBAN",
        "BARREN_SOIL",
    ]
    for cat in expected_categories:
        assert cat in GROUND_TRUTH_SITES
        assert len(GROUND_TRUTH_SITES[cat]) >= 2


def test_ground_truth_coordinates_within_aoi():
    """Verify all ground-truth verification coordinates are within benchmark AOI."""
    bounds = Config.DEFAULT_AOI_BOUNDS  # [min_lon, min_lat, max_lon, max_lat]
    for cat, sites in GROUND_TRUTH_SITES.items():
        for site in sites:
            lon, lat = site["coords"]
            assert bounds[0] <= lon <= bounds[2], f"{site['name']} lon {lon} out of bounds"
            assert bounds[1] <= lat <= bounds[3], f"{site['name']} lat {lat} out of bounds"
