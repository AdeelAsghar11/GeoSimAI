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


def test_assign_cluster_biome_names():
    """Should correctly assign environmental biome names based on optical profiles."""
    from src.core.clustering import assign_cluster_biome_names

    test_indices = {
        0: {"ndvi": 0.05, "ndbi": -0.20, "ndmi": 0.10},  # Water
        1: {"ndvi": 0.25, "ndbi": 0.05, "ndmi": -0.05},  # Urban
        2: {"ndvi": 0.65, "ndbi": -0.25, "ndmi": 0.25},  # Forest
    }

    names = assign_cluster_biome_names(test_indices, n_clusters=3)
    assert len(names) == 3
    assert "River" in names[0] or "Water" in names[0]
    assert "Urban" in names[1]
    assert "Forest" in names[2]
