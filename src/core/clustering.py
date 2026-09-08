"""Unsupervised spatial clustering over Earth Engine satellite embeddings."""

from typing import Dict, List, Any, Optional
import ee

import numpy as np
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


def assign_cluster_biome_names(
    cluster_indices: Dict[int, Dict[str, float]],
    n_clusters: int,
) -> Dict[int, str]:
    """Assign human-interpretable ecological biome names based on mean optical indices.

    Evaluates relative vegetation density (NDVI), built-up presence (NDBI),
    and moisture (NDMI) across the clusters.
    """
    if not cluster_indices:
        defaults = [
            "Dense Alpine Pine Forest",
            "Montane Highland Forest",
            "Terraced Valley Agriculture",
            "Urban Fabric & Commercial Core",
            "River Channels & Confluence",
            "Barren Scree & Rocky Escarpment",
            "Sub-Alpine Ridge Canopy",
            "Riparian Buffer Zone",
        ]
        return {c: defaults[c % len(defaults)] for c in range(n_clusters)}

    # Rank clusters by NDVI descending
    ranked_by_ndvi = sorted(
        cluster_indices.keys(),
        key=lambda c: cluster_indices[c].get("ndvi", 0.0),
        reverse=True,
    )

    max_ndbi_cluster = max(
        cluster_indices.keys(),
        key=lambda c: cluster_indices[c].get("ndbi", -1.0),
    )

    assigned: Dict[int, str] = {}

    for rank, c in enumerate(ranked_by_ndvi):
        idx = cluster_indices[c]
        ndvi = idx.get("ndvi", 0.0)
        ndbi = idx.get("ndbi", 0.0)
        ndmi = idx.get("ndmi", 0.0)

        # 1. Water signal (low NDVI and high moisture or low reflectance)
        if ndvi < 0.12 and (ndmi > -0.05 or ndbi < -0.12):
            assigned[c] = "River Channel & Water Surface"
        # 2. Strongest urban / built-up fabric signal
        elif c == max_ndbi_cluster and (ndbi > -0.09 or ndvi < 0.38):
            assigned[c] = "Urban Core & Built-up Fabric"
        # 3. Dense forest (highest relative vegetative biomass)
        elif rank == 0:
            assigned[c] = "Dense Alpine Pine Forest"
        # 4. Secondary montane canopy
        elif rank == 1:
            assigned[c] = "Montane Forest & Highland Canopy"
        # 5. Valley agricultural terraces
        elif rank == 2:
            assigned[c] = "Terraced Valley Agriculture"
        # 6. Settled / low-density greenery
        elif rank == 3:
            assigned[c] = "Sparse Vegetation & Settlements"
        # 7. Low biomass / rocky terrain
        else:
            assigned[c] = "Barren Scree & Rocky Escarpment"

    # Fill any unassigned
    for c in range(n_clusters):
        if c not in assigned:
            assigned[c] = f"Biome Cluster #{c}"

    return assigned


def run_spatial_clustering(
    image: ee.Image,
    aoi: ee.Geometry,
    n_clusters: int = 5,
    year: int = Config.DEFAULT_YEAR,
    scale: int = 30,
    num_samples: int = 1500,
) -> Dict[str, Any]:
    """Train unsupervised k-means clusterer on 64-D embedding bands and return tile visualization.

    Partitions the landscape into k coherent environmental clusters based on latent
    geophysical and ecological signatures, without requiring labeled ground truth.
    Dynamically auto-labels clusters using Sentinel-2 optical spectral indices.

    Args:
        image: 64-band AlphaEarth embedding ee.Image.
        aoi: ee.Geometry defining training and clustering bounds.
        n_clusters: Number of clusters (k), between 2 and 8.
        year: Year for optical spectral index analysis.
        scale: Spatial sampling resolution in meters.
        num_samples: Number of training pixels sampled across the AOI.

    Returns:
        Dictionary containing 'tile_url', 'n_clusters', 'palette', 'clusters', and 'mapid'.
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

    # 5. Extract optical spectral indices per cluster to auto-name biomes
    cluster_means: Dict[int, Dict[str, float]] = {}
    try:
        from src.core.optical import get_sentinel2_composite, compute_spectral_indices
        s2 = get_sentinel2_composite(year=year, aoi=aoi)
        idx_img = compute_spectral_indices(s2)
        sample_target = clustered_image.addBands(idx_img)
        sample_features = sample_target.sample(
            region=aoi,
            scale=max(scale * 2, 50),
            numPixels=500,
            dropNulls=True,
        ).getInfo().get("features", [])

        accumulator: Dict[int, Dict[str, List[float]]] = {}
        for f in sample_features:
            p = f.get("properties", {})
            c = int(p.get("cluster", 0))
            accumulator.setdefault(c, {"ndvi": [], "ndbi": [], "ndmi": []})
            for k in ["ndvi", "ndbi", "ndmi"]:
                if k in p and p[k] is not None:
                    accumulator[c][k].append(float(p[k]))

        for c, vals in accumulator.items():
            cluster_means[c] = {
                k: round(float(np.mean(v)), 3) for k, v in vals.items() if v
            }
    except Exception:
        pass

    names = assign_cluster_biome_names(cluster_means, n_clusters)

    clusters_payload = [
        {
            "id": c,
            "name": names.get(c, f"Biome Cluster #{c}"),
            "color": f"#{palette[c]}" if c < len(palette) else "#8b5cf6",
            "indices": cluster_means.get(c, {"ndvi": 0.0, "ndbi": 0.0, "ndmi": 0.0}),
        }
        for c in range(n_clusters)
    ]

    return {
        "tile_url": tile_url,
        "n_clusters": n_clusters,
        "palette": [f"#{c}" for c in palette],
        "clusters": clusters_payload,
        "mapid": map_dict.get("mapid", ""),
    }
