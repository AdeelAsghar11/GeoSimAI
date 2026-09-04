"""Embedding extraction and mean-pooling aggregation routines."""

from typing import List, Union, Dict, Any
import ee
import numpy as np

from src.config import Config


def extract_point_embedding(
    image: ee.Image,
    lon: float,
    lat: float,
    scale: int = Config.DEFAULT_SCALE_METERS,
) -> List[float]:
    """Extract 64-D embedding vector for a single geographic coordinate.

    Args:
        image: 64-band AlphaEarth embedding ee.Image.
        lon: Longitude in WGS84 decimal degrees.
        lat: Latitude in WGS84 decimal degrees.
        scale: Resolution scale in meters (default 10m).

    Returns:
        List of 64 floating point values representing the latent embedding vector.

    Raises:
        ValueError: If extraction returns empty/no-data values.
    """
    point = ee.Geometry.Point([lon, lat])
    reducer = ee.Reducer.first()

    values_dict = image.reduceRegion(
        reducer=reducer,
        geometry=point,
        scale=scale,
        bestEffort=True,
    ).getInfo()

    if not values_dict or any(v is None for v in values_dict.values()):
        raise ValueError(
            f"No valid embedding values found at coordinates ({lon}, {lat})."
        )

    # Order by band sequence A00 to A63
    vector = [float(values_dict[band]) for band in Config.EMBEDDING_BANDS]
    return vector


def extract_polygon_embedding(
    image: ee.Image,
    geometry: Union[ee.Geometry, Dict[str, Any]],
    scale: int = Config.DEFAULT_SCALE_METERS,
    normalize: bool = True,
) -> List[float]:
    """Extract and mean-pool the 64-D embedding vector across a spatial polygon/patch.

    Since AlphaEarth embeddings are linearly composable, spatial mean-pooling
    across constituent pixels accurately preserves latent environmental relationships.

    Args:
        image: 64-band AlphaEarth embedding ee.Image.
        geometry: ee.Geometry or GeoJSON geometry dictionary.
        scale: Resolution scale in meters (default 10m).
        normalize: If True, re-normalizes the mean-pooled vector to unit L2 norm.

    Returns:
        List of 64 floating point values representing the pooled embedding vector.

    Raises:
        ValueError: If extraction returns empty or uncomputable values.
    """
    if isinstance(geometry, dict):
        ee_geom = ee.Geometry(geometry)
    else:
        ee_geom = geometry

    reducer = ee.Reducer.mean()
    values_dict = image.reduceRegion(
        reducer=reducer,
        geometry=ee_geom,
        scale=scale,
        maxPixels=1e8,
        bestEffort=True,
    ).getInfo()

    if not values_dict or any(v is None for v in values_dict.values()):
        raise ValueError("Could not compute mean embedding over the provided geometry.")

    vector = np.array(
        [float(values_dict[band]) for band in Config.EMBEDDING_BANDS], dtype=np.float64
    )

    if normalize:
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm

    return [float(x) for x in vector]
