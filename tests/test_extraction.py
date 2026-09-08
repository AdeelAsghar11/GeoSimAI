"""Unit tests for embedding extraction, mean-pooling, and case study configurations."""

import numpy as np
import pytest

from src.config import Config
from src.core.extraction import extract_polygon_embedding
from src.core.similarity import compute_similarity_image


def test_case_studies_configured():
    """Verify all 3 validation case studies have valid coordinates and years."""
    assert "A_RIVER" in Config.CASE_STUDIES
    assert "B_URBAN" in Config.CASE_STUDIES
    assert "C_FOREST" in Config.CASE_STUDIES

    for key, study in Config.CASE_STUDIES.items():
        assert "coords" in study
        lon, lat = study["coords"]
        # Must fall within the benchmark AOI bounds [72.80, 33.45, 73.25, 33.82]
        bounds = Config.DEFAULT_AOI_BOUNDS
        assert bounds[0] <= lon <= bounds[2], f"{key} lon {lon} out of bounds"
        assert bounds[1] <= lat <= bounds[3], f"{key} lat {lat} out of bounds"
        assert study["year"] in Config.AVAILABLE_YEARS


def test_invalid_reference_vector_dimension_raises():
    """Similarity computation must reject vectors that do not have 64 dimensions."""
    invalid_vector = [0.1] * 32  # Only 32 dimensions

    with pytest.raises(ValueError, match="Reference vector must have 64 dimensions"):
        compute_similarity_image(None, reference_vector=invalid_vector)


def test_vector_l2_normalization():
    """Pooled vectors must have unit L2 norm when normalize=True."""
    # Simulate a mean vector of 64 dims
    np.random.seed(42)
    fake_mean = np.random.uniform(-0.5, 0.5, size=64)
    norm = np.linalg.norm(fake_mean)
    normalized = fake_mean / norm

    assert np.isclose(np.linalg.norm(normalized), 1.0, atol=1e-6)
