"""Unit tests for unsupervised spatial clustering configurations."""

import pytest
from src.core.clustering import CLUSTER_PALETTES, run_spatial_clustering


def test_cluster_palettes_valid():
    """Verify cluster palettes contain hex color sequences matching k."""
    for k, palette in CLUSTER_PALETTES.items():
        assert len(palette) == k
        for color in palette:
            assert len(color) == 6  # 6-character hex


def test_cluster_invalid_k_raises():
    """Clustering must reject k < 2 or k > 8."""
    with pytest.raises(ValueError, match="n_clusters must be between 2 and 8"):
        run_spatial_clustering(None, None, n_clusters=1)

    with pytest.raises(ValueError, match="n_clusters must be between 2 and 8"):
        run_spatial_clustering(None, None, n_clusters=10)
