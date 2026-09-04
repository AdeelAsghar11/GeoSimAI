"""Google Earth Engine initialization and image collection loader."""

import os
from typing import Optional
import ee

from src.config import Config


def initialize_earth_engine(project: Optional[str] = None) -> bool:
    """Initialize Google Earth Engine client with project or credentials.

    Args:
        project: Optional Google Cloud Project ID. If not provided,
                 uses Config.GEE_PROJECT or environment variables.

    Returns:
        True if initialization succeeded.

    Raises:
        ee.EEException: If authentication or initialization fails.
    """
    project_id = (
        project
        or Config.GEE_PROJECT
        or os.getenv("GEE_PROJECT")
        or os.getenv("GOOGLE_CLOUD_PROJECT")
        or None
    )

    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if credentials_path and os.path.exists(credentials_path):
        service_account_email = os.getenv("GEE_SERVICE_ACCOUNT")
        if service_account_email:
            credentials = ee.ServiceAccountCredentials(
                service_account_email, credentials_path
            )
            ee.Initialize(credentials, project=project_id)
            return True

    if project_id:
        ee.Initialize(project=project_id)
    else:
        ee.Initialize()

    return True


def load_embedding_image(
    year: int = Config.DEFAULT_YEAR,
    aoi: Optional[ee.Geometry] = None,
) -> ee.Image:
    """Load and mosaic the 64-band AlphaEarth embedding image for a given year and AOI.

    AlphaEarth embeddings are stored in UTM projection tiles (~163.8 km x 163.8 km).
    Mosaicking across bounds ensures gap-free coverage across tile seams.

    Args:
        year: Calendar year between 2017 and 2024.
        aoi: Optional ee.Geometry defining the Area of Interest for spatial filtering.

    Returns:
        ee.Image containing the 64 latent bands (A00 to A63).

    Raises:
        ValueError: If year is outside the available range (2017-2024).
    """
    if year not in Config.AVAILABLE_YEARS:
        raise ValueError(
            f"Year {year} is outside available range ({min(Config.AVAILABLE_YEARS)} - {max(Config.AVAILABLE_YEARS)})"
        )

    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"

    collection = ee.ImageCollection(Config.GEE_DATASET_ID).filterDate(
        start_date, end_date
    )

    if aoi is not None:
        collection = collection.filterBounds(aoi)

    # Mosaic tiles across AOI and select 64 embedding bands
    image = collection.mosaic().select(Config.EMBEDDING_BANDS)
    return image
