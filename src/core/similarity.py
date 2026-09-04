"""Server-side Earth Engine vector similarity and top-N ranking routines."""

from typing import List, Dict, Any, Optional
import ee

from src.config import Config


def compute_similarity_image(
    image: ee.Image,
    reference_vector: List[float],
    aoi: Optional[ee.Geometry] = None,
) -> ee.Image:
    """Compute continuous dot product similarity image against a 64-D reference vector.

    Since AlphaEarth embeddings are unit-normalized vectors, the vector dot product
    is mathematically identical to cosine similarity:
        Sim(u, v) = sum(u_i * v_i) for i in [0, 63]

    Args:
        image: 64-band AlphaEarth embedding ee.Image.
        reference_vector: 64-element list of floats.
        aoi: Optional ee.Geometry to clip calculation extent.

    Returns:
        Single-band ee.Image named 'similarity' with values theoretically in [-1.0, 1.0].
    """
    if len(reference_vector) != Config.EMBEDDING_DIM:
        raise ValueError(
            f"Reference vector must have {Config.EMBEDDING_DIM} dimensions, got {len(reference_vector)}"
        )

    # Construct constant 64-band image from reference vector
    ref_image = ee.Image.constant(reference_vector).rename(Config.EMBEDDING_BANDS)

    # Element-wise multiplication followed by sum reduction
    sim_image = (
        image.select(Config.EMBEDDING_BANDS)
        .multiply(ref_image)
        .reduce(ee.Reducer.sum())
        .rename("similarity")
    )

    if aoi is not None:
        sim_image = sim_image.clip(aoi)

    return sim_image


def get_similarity_map_id(
    similarity_image: ee.Image,
    min_val: float = 0.0,
    max_val: float = 1.0,
    palette: Optional[List[str]] = None,
) -> Dict[str, str]:
    """Generate XYZ tile URL format for Leaflet/Slippy map overlay.

    Args:
        similarity_image: Single-band similarity ee.Image.
        min_val: Lower visual clamp value (default 0.0).
        max_val: Upper visual clamp value (default 1.0).
        palette: Hex color sequence (default: blue -> cyan -> yellow -> orange -> red).

    Returns:
        Dictionary containing 'tile_url_format', 'mapid', and 'token'.
    """
    vis_params = {
        "min": min_val,
        "max": max_val,
        "palette": palette or Config.SIMILARITY_PALETTE,
    }

    map_dict = similarity_image.getMapId(vis_params)
    tile_url = map_dict.get("tile_fetcher", {}).url_format or ""

    return {
        "tile_url": tile_url,
        "mapid": map_dict.get("mapid", ""),
        "token": map_dict.get("token", ""),
    }


def get_top_matches(
    similarity_image: ee.Image,
    aoi: ee.Geometry,
    threshold: float = 0.80,
    top_n: int = Config.DEFAULT_TOP_N,
    scale: int = Config.DEFAULT_SEARCH_SCALE_METERS,
    max_samples: int = Config.MAX_SEARCH_SAMPLES,
) -> List[Dict[str, Any]]:
    """Sample candidate pixels within AOI exceeding threshold and return ranked top-N locations.

    Args:
        similarity_image: Single-band 'similarity' ee.Image.
        aoi: ee.Geometry bounding the search Area of Interest.
        threshold: Minimum similarity score cutoff (0.0 to 1.0).
        top_n: Number of top candidate matches to return.
        scale: Sampling resolution scale in meters.
        max_samples: Maximum pixels to sample before sorting.

    Returns:
        List of dicts: [{'rank': 1, 'lon': float, 'lat': float, 'score': float}, ...]
    """
    # Filter candidates meeting similarity threshold
    masked_sim = similarity_image.updateMask(similarity_image.gte(threshold))

    # Sample pixels within AOI
    samples = masked_sim.sample(
        region=aoi,
        scale=scale,
        numPixels=max_samples,
        geometries=True,
        dropNulls=True,
    )

    # Retrieve features client-side
    features = samples.getInfo().get("features", [])
    if not features:
        return []

    # Parse and sort descending by similarity score
    parsed_matches = []
    for f in features:
        props = f.get("properties", {})
        score = float(props.get("similarity", 0.0))
        geom = f.get("geometry", {})
        coords = geom.get("coordinates", [0.0, 0.0])

        parsed_matches.append(
            {
                "lon": round(float(coords[0]), 6),
                "lat": round(float(coords[1]), 6),
                "score": round(score, 4),
            }
        )

    # Sort descending by score
    parsed_matches.sort(key=lambda x: x["score"], reverse=True)

    # Deduplicate closely-spaced points (keep highest score in local vicinity)
    unique_matches = []
    min_dist_deg = 0.005  # ~500m separation to ensure spatial diversity
    for m in parsed_matches:
        is_duplicate = False
        for u in unique_matches:
            d_lon = abs(m["lon"] - u["lon"])
            d_lat = abs(m["lat"] - u["lat"])
            if d_lon < min_dist_deg and d_lat < min_dist_deg:
                is_duplicate = True
                break
        if not is_duplicate:
            unique_matches.append(m)
        if len(unique_matches) >= top_n:
            break

    # Assign 1-indexed ranks
    for i, m in enumerate(unique_matches, start=1):
        m["rank"] = i

    return unique_matches
