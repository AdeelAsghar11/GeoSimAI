"""Unsupervised spatial clustering over Earth Engine satellite embeddings."""

from typing import Dict, List, Any, Optional
import ee

from src.config import Config


# Curated qualitative palette for categorical cluster visualization
CLUSTER_PALETTES: Dict[int, List[str]] = {
    3: ["38bdf8", "10b981", "f59e0b"],
    4: ["38bdf8", "10b981", "f59e0b", "f43f5e"],
    5: ["38bdf8", "10b981", "f59e0b", "f43f5e", "8b5cf6"],
    6: ["38bdf8", "10b981", "f59e0b", "f43f5e", "8b5cf6", "ec4899"],
    8: [
        "38bdf8", "10b981", "f59e0b", "f43f5e",
        "8b5cf6", "ec4899", "14b8a6", "6366f1"
    ],
}


def run_spatial_clustering(
    image: ee.Image,
    aoi: ee.Geometry,
    n_clusters: int = 5,
    scale: int = 30,
    num_samples: int = 1500,
) -> Dict[str, Any]:
    """Train unsupervised k-means clusterer on 64-D embedding bands and return tile visualization.

    Partitions the landscape into k coherent environmental clusters based on latent
    geophysical and ecological signatures, without requiring labeled ground truth.

    Args:
        image: 64-band AlphaEarth embedding ee.Image.
        aoi: ee.Geometry defining training and clustering bounds.
        n_clusters: Number of clusters (k), between 2 and 8.
        scale: Spatial sampling resolution in meters.
        num_samples: Number of training pixels sampled across the AOI.

    Returns:
        Dictionary containing 'tile_url', 'n_clusters', 'palette', and 'mapid'.
    """
    if n_clusters < 2 or n_clusters > 8:
        raise ValueError(f"n_clusters must be between 2 and 8, got {n_clusters}")

    # 1. Sample pixels across the AOI for unsupervised training
    training = image.select(Config.EMBEDDING_BANDS).sample(
        region=aoi,
        scale=scale,
        numPixels=num_samples,
        dropNulls=True,
    )

    # 2. Train wekaKMeans clusterer server-side in Earth Engine
    clusterer = ee.Clusterer.wekaKMeans(n_clusters).train(training)

    # 3. Classify all AOI pixels
    clustered_image = (
        image.select(Config.EMBEDDING_BANDS)
        .cluster(clusterer)
        .rename("cluster")
        .clip(aoi)
    )

    # 4. Generate tile visualization
    palette = CLUSTER_PALETTES.get(n_clusters, CLUSTER_PALETTES[5][:n_clusters])
    vis_params = {
        "min": 0,
        "max": n_clusters - 1,
        "palette": palette,
    }

    map_dict = clustered_image.getMapId(vis_params)
    tile_url = map_dict.get("tile_fetcher", {}).url_format or ""

    return {
        "tile_url": tile_url,
        "n_clusters": n_clusters,
        "palette": [f"#{c}" for c in palette],
        "mapid": map_dict.get("mapid", ""),
    }
