"""Unit tests for vector similarity math and normalization."""

import numpy as np
import pytest

from src.config import Config


def compute_numpy_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
    """Compute dot product similarity between two vectors."""
    return float(np.dot(v1, v2))


def normalize_vector(v: np.ndarray) -> np.ndarray:
    """L2-normalize a vector."""
    norm = np.linalg.norm(v)
    if norm == 0:
        return v
    return v / norm


def test_config_dimensions():
    """Verify configuration band count and naming."""
    assert Config.EMBEDDING_DIM == 64
    assert len(Config.EMBEDDING_BANDS) == 64
    assert Config.EMBEDDING_BANDS[0] == "A00"
    assert Config.EMBEDDING_BANDS[63] == "A63"


def test_identical_vectors_similarity():
    """Identical unit vectors must have dot product similarity of exactly 1.0."""
    np.random.seed(42)
    raw = np.random.randn(64)
    v = normalize_vector(raw)

    sim = compute_numpy_similarity(v, v)
    assert np.isclose(sim, 1.0, atol=1e-6)


def test_opposite_vectors_similarity():
    """Opposite unit vectors must have dot product similarity of -1.0."""
    np.random.seed(42)
    raw = np.random.randn(64)
    v = normalize_vector(raw)

    sim = compute_numpy_similarity(v, -v)
    assert np.isclose(sim, -1.0, atol=1e-6)


def test_orthogonal_vectors_similarity():
    """Orthogonal vectors must have dot product similarity of 0.0."""
    v1 = np.zeros(64)
    v2 = np.zeros(64)
    v1[0] = 1.0
    v2[1] = 1.0

    sim = compute_numpy_similarity(v1, v2)
    assert np.isclose(sim, 0.0, atol=1e-6)


def test_mean_pooling_linear_composability():
    """Mean pooling across N embeddings correctly averages coordinates."""
    np.random.seed(42)
    # 5 pixels in a patch
    patch_pixels = np.random.randn(5, 64)
    patch_pixels_norm = np.array([normalize_vector(p) for p in patch_pixels])

    pooled = np.mean(patch_pixels_norm, axis=0)
    assert pooled.shape == (64,)
    # Verify each dimension matches arithmetic mean
    for i in range(64):
        assert np.isclose(pooled[i], patch_pixels_norm[:, i].mean())
