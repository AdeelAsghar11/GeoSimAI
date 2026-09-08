"""Integration tests for Flask API endpoints."""

import pytest
from run import create_app


@pytest.fixture
def client():
    """Create Flask test client."""
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_index_serves_html(client):
    """GET / should return index.html."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"GeoSimAI" in response.data
    assert b"leaflet" in response.data.lower()


def test_api_health_endpoint(client):
    """GET /api/health returns status and ee_initialized flag."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "healthy"
    assert "ee_initialized" in data
    assert data["version"] == "0.1.0"


def test_api_metadata_endpoint(client):
    """GET /api/metadata returns configured years, dimensions, and presets."""
    response = client.get("/api/metadata")
    assert response.status_code == 200
    data = response.get_json()
    assert data["embedding_dim"] == 64
    assert 2023 in data["available_years"]
    assert "default_aoi" in data
    assert "A_RIVER" in data["case_studies"]
    assert "Muzaffarabad" in data["default_aoi"]["name"]
