"""Configuration and constants for GeoSimAI."""

import os
from typing import List
from dotenv import load_dotenv

# Load local environment variables from .env file if present
load_dotenv()


class Config:

    """Application configuration settings."""

    # Earth Engine Settings
    GEE_DATASET_ID: str = os.getenv(
        "GEE_DATASET_ID", "GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL"
    )
    GEE_PROJECT: str = os.getenv("GEE_PROJECT", "")

    # Embedding Properties
    EMBEDDING_DIM: int = 64
    EMBEDDING_BANDS: List[str] = [f"A{i:02d}" for i in range(EMBEDDING_DIM)]
    AVAILABLE_YEARS: List[int] = list(range(2017, 2025))  # 2017 - 2024
    DEFAULT_YEAR: int = 2023

    # Resolution & Spatial Limits
    DEFAULT_SCALE_METERS: int = 10  # AlphaEarth native resolution is 10m
    DEFAULT_SEARCH_SCALE_METERS: int = 20  # Fast search scale
    MAX_SEARCH_SAMPLES: int = 500  # Max candidate points for top-N ranking
    DEFAULT_TOP_N: int = 20

    # Benchmark Study AOI: Islamabad / Rawalpindi Twin Cities
    # Bounds: [min_lon, min_lat, max_lon, max_lat] (WGS84)
    DEFAULT_AOI_BOUNDS: List[float] = [72.80, 33.45, 73.25, 33.82]
    DEFAULT_AOI_GEOJSON: dict = {
        "type": "Polygon",
        "coordinates": [[
            [72.80, 33.45],
            [73.25, 33.45],
            [73.25, 33.82],
            [72.80, 33.82],
            [72.80, 33.45],
        ]],
    }

    # Validation Case Study Reference Points [lon, lat]
    CASE_STUDIES = {
        "A_AGRICULTURE": {
            "name": "Potohar Plateau Cropland (Chak Shahzad)",
            "coords": [73.140, 33.670],
            "year": 2023,
            "description": "Rainfed agricultural parcel vs. urban/barren land",
        },
        "B_WATER": {
            "name": "Rawal Lake Deep Water",
            "coords": [73.123, 33.702],
            "year": 2023,
            "description": "Deep freshwater reservoir vs. dry land/vegetation",
        },
        "C_VEGETATION": {
            "name": "Fatima Jinnah Park (Islamabad Urban Greenery)",
            "coords": [73.018, 33.704],
            "year": 2023,
            "description": "Urban park canopy vs. Margalla forest reserve and built-up grid",
        },
    }

    # Visualization settings
    SIMILARITY_PALETTE: List[str] = [
        "0000ff",  # Low similarity (blue)
        "00ffff",  # Cyan
        "ffff00",  # Yellow
        "ff7f00",  # Orange
        "ff0000",  # High similarity (red)
    ]

    # Server Settings
    DEBUG: bool = os.getenv("FLASK_DEBUG", "True").lower() in ("true", "1", "yes")
    PORT: int = int(os.getenv("PORT", "5000"))
    HOST: str = os.getenv("HOST", "127.0.0.1")

