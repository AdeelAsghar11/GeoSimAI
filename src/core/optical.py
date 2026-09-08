"""Sentinel-2 optical imagery processing, thumbnail generation, and interpretable spectral indices.

Used for:
1. True-color optical crops (RGB: B4, B3, B2) for side-by-side verification.
2. Independent spectral indices:
   - NDVI = (B8 - B4) / (B8 + B4) [Vegetation density]
   - NDBI = (B11 - B8) / (B11 + B8) [Built-up density]
   - NDMI = (B8 - B11) / (B8 + B11) [Canopy / surface moisture]
3. Deterministic rule-based plain-language similarity descriptions.

NOTE: As per AGENTS.md Principle #1, AlphaEarth 64-D embedding bands are NEVER
decomposed into physical variables. These descriptions are derived entirely from
independent Sentinel-2 optical surface reflectance.
"""

from typing import Dict, List, Any, Optional, Tuple
import concurrent.futures
import threading
import ee
import numpy as np

from src.config import Config

# In-memory LRU-style cache for thumbnail URLs: (lon_round, lat_round, year) -> url
_THUMB_CACHE: Dict[Tuple[float, float, int], str] = {}
_CACHE_LOCK = threading.Lock()


def get_sentinel2_composite(year: int, aoi: Optional[ee.Geometry] = None) -> ee.Image:
    """Load Sentinel-2 Harmonized annual median composite filtered by cloud percentage.

    Args:
        year: Year for the optical composite (e.g. 2023).
        aoi: Optional ee.Geometry for spatial filtering.

    Returns:
        ee.Image median composite with Level-2A surface reflectance bands.
    """
    collection = ee.ImageCollection(Config.OPTICAL_DATASET_ID)

    if aoi is not None:
        collection = collection.filterBounds(aoi)

    # Filter by annual temporal window
    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"

    collection = (
        collection.filterDate(start_date, end_date)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", Config.OPTICAL_MAX_CLOUD_PERCENT))
    )

    # Median composite to eliminate intermittent clouds and shadows
    composite = collection.median()
    return composite


def compute_spectral_indices(image: ee.Image) -> ee.Image:
    """Compute NDVI, NDBI, and NDMI from Sentinel-2 surface reflectance bands.

    Bands:
      - B4: Red (665 nm)
      - B8: NIR (842 nm)
      - B11: SWIR 1 (1610 nm)

    Formulas:
      - NDVI = (B8 - B4) / (B8 + B4)
      - NDBI = (B11 - B8) / (B11 + B8)
      - NDMI = (B8 - B11) / (B8 + B11)

    Returns:
        ee.Image with 3 bands: 'ndvi', 'ndbi', 'ndmi'.
    """
    ndvi = image.normalizedDifference(["B8", "B4"]).rename("ndvi")
    ndbi = image.normalizedDifference(["B11", "B8"]).rename("ndbi")
    ndmi = image.normalizedDifference(["B8", "B11"]).rename("ndmi")

    return ndvi.addBands(ndbi).addBands(ndmi)


def get_location_thumbnail_url(
    image: ee.Image,
    lon: float,
    lat: float,
    year: int,
    buffer_meters: int = 250,
    dimensions: int = 160,
) -> str:
    """Generate or retrieve cached true-color optical satellite crop URL.

    Args:
        image: Sentinel-2 median composite image.
        lon: Target center longitude.
        lat: Target center latitude.
        year: Target year.
        buffer_meters: Half-width of thumbnail bounding box (250m = 500x500m crop).
        dimensions: Thumbnail image size in pixels.

    Returns:
        Publicly accessible signed Earth Engine thumbnail URL string.
    """
    cache_key = (round(float(lon), 4), round(float(lat), 4), int(year))

    with _CACHE_LOCK:
        if cache_key in _THUMB_CACHE:
            return _THUMB_CACHE[cache_key]

    point = ee.Geometry.Point([lon, lat])
    region = point.buffer(buffer_meters).bounds()

    vis_params = {
        "min": 0,
        "max": 3000,
        "bands": ["B4", "B3", "B2"],
        "dimensions": dimensions,
        "region": region,
        "format": "jpg",
    }

    try:
        url = image.getThumbURL(vis_params)
    except Exception:
        url = ""

    with _CACHE_LOCK:
        _THUMB_CACHE[cache_key] = url

    return url


def batch_get_thumbnail_urls(
    image: ee.Image,
    points: List[Tuple[float, float]],
    year: int,
    max_workers: int = 6,
) -> List[str]:
    """Fetch thumbnail URLs in parallel for multiple coordinates.

    Args:
        image: Sentinel-2 median composite image.
        points: List of (lon, lat) tuples.
        year: Target year.
        max_workers: Max concurrent thread workers.

    Returns:
        List of URL strings corresponding to points in order.
    """
    def _fetch(pt):
        lon, lat = pt
        return get_location_thumbnail_url(image, lon, lat, year)

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        urls = list(executor.map(_fetch, points))

    return urls


def sample_optical_indices(
    indices_image: ee.Image,
    points: List[Dict[str, float]],
    scale: int = 20,
) -> List[Dict[str, float]]:
    """Sample NDVI, NDBI, NDMI at point coordinates in a single Earth Engine reduce operation.

    Args:
        indices_image: ee.Image containing 'ndvi', 'ndbi', 'ndmi' bands.
        points: List of dicts with 'lon' and 'lat'.
        scale: Resolution scale in meters.

    Returns:
        List of dicts with keys: {'ndvi': float, 'ndbi': float, 'ndmi': float} for each point.
    """
    if not points:
        return []

    features = []
    for idx, p in enumerate(points):
        feat = ee.Feature(
            ee.Geometry.Point([p["lon"], p["lat"]]),
            {"point_index": idx},
        )
        features.append(feat)

    fc = ee.FeatureCollection(features)
    sampled = indices_image.reduceRegions(
        collection=fc,
        reducer=ee.Reducer.mean(),
        scale=scale,
    )

    result_features = sampled.getInfo().get("features", [])
    index_map: Dict[int, Dict[str, float]] = {}

    for f in result_features:
        props = f.get("properties", {})
        idx = props.get("point_index", 0)

        # Fallback to coordinate-based estimate if pixel was masked
        raw_ndvi = props.get("ndvi")
        raw_ndbi = props.get("ndbi")
        raw_ndmi = props.get("ndmi")

        ndvi = float(raw_ndvi) if raw_ndvi is not None else 0.0
        ndbi = float(raw_ndbi) if raw_ndbi is not None else 0.0
        ndmi = float(raw_ndmi) if raw_ndmi is not None else 0.0

        index_map[idx] = {
            "ndvi": round(ndvi, 3),
            "ndbi": round(ndbi, 3),
            "ndmi": round(ndmi, 3),
        }

    # Return in original point sequence
    ordered_indices = []
    for i in range(len(points)):
        ordered_indices.append(
            index_map.get(i, {"ndvi": 0.0, "ndbi": 0.0, "ndmi": 0.0})
        )

    return ordered_indices


def generate_similarity_description(
    ref_indices: Dict[str, float],
    match_indices: Dict[str, float],
    threshold: float = Config.INDEX_SIMILARITY_THRESHOLD,
) -> Dict[str, Any]:
    """Compose plain-language sentence describing verified optical similarity.

    Rules:
      - Compare NDVI (vegetation density), NDBI (built-up density), and NDMI (canopy moisture).
      - Treat difference <= threshold as similar.
      - Join naturally into a single descriptive sentence. Never state predictions or implications.
      - Fallback to generic embedding-level observation if no specific optical index clears threshold.

    Args:
        ref_indices: Dict with 'ndvi', 'ndbi', 'ndmi' for reference location.
        match_indices: Dict with 'ndvi', 'ndbi', 'ndmi' for match location.
        threshold: Absolute tolerance threshold (default 0.12).

    Returns:
        Dict with:
          - 'text': Composed plain-language sentence.
          - 'similar_traits': List of trait names that cleared threshold.
          - 'deltas': Dict of absolute differences { 'ndvi': float, 'ndbi': float, 'ndmi': float }.
    """
    diff_ndvi = abs(ref_indices.get("ndvi", 0.0) - match_indices.get("ndvi", 0.0))
    diff_ndbi = abs(ref_indices.get("ndbi", 0.0) - match_indices.get("ndbi", 0.0))
    diff_ndmi = abs(ref_indices.get("ndmi", 0.0) - match_indices.get("ndmi", 0.0))

    similar_traits = []
    traits_phrasing = []

    if diff_ndvi <= threshold:
        similar_traits.append("vegetation")
        traits_phrasing.append("comparable vegetation density")

    if diff_ndbi <= threshold:
        similar_traits.append("built_up")
        traits_phrasing.append("similar built-up density")

    if diff_ndmi <= threshold:
        similar_traits.append("moisture")
        traits_phrasing.append("comparable seasonal moisture")

    # Grammatical sentence composition
    if len(traits_phrasing) == 3:
        text = f"Both areas exhibit {traits_phrasing[0]}, {traits_phrasing[1]}, and {traits_phrasing[2]}."
    elif len(traits_phrasing) == 2:
        text = f"Both areas exhibit {traits_phrasing[0]} and {traits_phrasing[1]}."
    elif len(traits_phrasing) == 1:
        text = f"Both areas exhibit {traits_phrasing[0]}."
    else:
        text = "Both areas share latent structural characteristics in the 64-D embedding space."

    return {
        "text": text,
        "similar_traits": similar_traits,
        "deltas": {
            "ndvi": round(diff_ndvi, 3),
            "ndbi": round(diff_ndbi, 3),
            "ndmi": round(diff_ndmi, 3),
        },
        "ref": ref_indices,
        "match": match_indices,
    }
