"""End-to-end CLI pipeline runner for GeoSimAI similarity search."""

import argparse
import json
import sys
from typing import Optional, List, Dict, Any
import ee

from src.config import Config
from src.core.client import initialize_earth_engine, load_embedding_image
from src.core.extraction import extract_point_embedding, extract_polygon_embedding
from src.core.similarity import (
    compute_similarity_image,
    get_similarity_map_id,
    get_top_matches,
)


def run_pipeline(
    lon: float,
    lat: float,
    year: int = Config.DEFAULT_YEAR,
    aoi_bounds: Optional[List[float]] = None,
    threshold: float = 0.75,
    top_n: int = 10,
    project: Optional[str] = None,
    output_json: Optional[str] = None,
) -> Dict[str, Any]:
    """Execute complete Earth Engine similarity search pipeline.

    Args:
        lon: Reference longitude.
        lat: Reference latitude.
        year: Target year (2017-2024).
        aoi_bounds: [min_lon, min_lat, max_lon, max_lat] bounding box.
        threshold: Minimum similarity cutoff.
        top_n: Number of ranked matches to return.
        project: Optional Google Cloud Project ID.
        output_json: Optional file path to export JSON results.

    Returns:
        Dictionary with reference info, tile URL, and ranked candidate coordinates.
    """
    print("=" * 70)
    print("GeoSimAI — Geospatial Vector Similarity Search")
    print("=" * 70)

    # 1. Initialize GEE
    initialize_earth_engine(project=project)
    print(f"[*] Earth Engine initialized.")

    # 2. Define AOI
    bounds = aoi_bounds or Config.DEFAULT_AOI_BOUNDS
    aoi = ee.Geometry.BBox(bounds[0], bounds[1], bounds[2], bounds[3])
    print(f"[*] AOI bounds: {bounds}")
    print(f"[*] Target Year: {year}")
    print(f"[*] Reference Point: ({lon}, {lat})")

    # 3. Load embedding image
    print(f"[*] Loading & mosaicking AlphaEarth embeddings for {year}...")
    image = load_embedding_image(year=year, aoi=aoi)

    # 4. Extract reference embedding
    print(f"[*] Extracting 64-D embedding vector at reference location...")
    ref_vector = extract_point_embedding(image, lon=lon, lat=lat)
    print(
        f"[+] Extracted 64-D vector. Norm: {sum(x**2 for x in ref_vector)**0.5:.4f}, Sample: {ref_vector[:3]}..."
    )

    # 5. Compute similarity image
    print(f"[*] Computing pixel-wise vector dot product across AOI...")
    sim_image = compute_similarity_image(image, reference_vector=ref_vector, aoi=aoi)

    # 6. Generate Tile URL
    print(f"[*] Generating visualization tile map ID...")
    tile_info = get_similarity_map_id(sim_image, min_val=threshold, max_val=1.0)
    print(f"[+] Heatmap Tile URL: {tile_info['tile_url']}")

    # 7. Extract Top Matches
    print(f"[*] Sampling and ranking top {top_n} candidate locations (threshold >= {threshold})...")
    matches = get_top_matches(
        similarity_image=sim_image,
        aoi=aoi,
        threshold=threshold,
        top_n=top_n,
    )

    print("\n" + "=" * 70)
    print(f"{'Rank':<6} {'Latitude':<12} {'Longitude':<12} {'Similarity Score':<18}")
    print("-" * 70)
    for m in matches:
        print(f"{m['rank']:<6} {m['lat']:<12.6f} {m['lon']:<12.6f} {m['score']:<18.4f}")
    print("=" * 70)

    result = {
        "year": year,
        "reference": {"lon": lon, "lat": lat},
        "aoi_bounds": bounds,
        "threshold": threshold,
        "tile_info": tile_info,
        "matches": matches,
    }

    if output_json:
        with open(output_json, "w") as f:
            json.dump(result, f, indent=2)
        print(f"[+] Results saved to {output_json}")

    return result


def main():
    """CLI entry point for pipeline runner."""
    parser = argparse.ArgumentParser(
        description="GeoSimAI: In-Engine Geospatial Vector Similarity Search"
    )
    parser.add_argument(
        "--case-study",
        choices=list(Config.CASE_STUDIES.keys()),
        default=None,
        help="Run predefined validation case study (e.g. A_AGRICULTURE, B_WATER, C_VEGETATION)",
    )
    parser.add_argument("--lon", type=float, default=None, help="Reference longitude")
    parser.add_argument("--lat", type=float, default=None, help="Reference latitude")
    parser.add_argument(
        "--year",
        type=int,
        default=Config.DEFAULT_YEAR,
        help=f"Year to search ({min(Config.AVAILABLE_YEARS)}-{max(Config.AVAILABLE_YEARS)})",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.75,
        help="Similarity score threshold (0.0 to 1.0)",
    )
    parser.add_argument(
        "--top-n", type=int, default=10, help="Number of top candidates to retrieve"
    )
    parser.add_argument("--project", type=str, default=None, help="Google Cloud Project ID")
    parser.add_argument(
        "--output", type=str, default=None, help="Path to export JSON output"
    )

    args = parser.parse_args()

    if args.case_study:
        study = Config.CASE_STUDIES[args.case_study]
        print(f"Running Case Study: {study['name']}")
        print(f"Description: {study['description']}")
        lon, lat = study["coords"]
        year = study.get("year", args.year)
    else:
        if args.lon is None or args.lat is None:
            # Default to Fatima Jinnah Park
            study = Config.CASE_STUDIES["C_VEGETATION"]
            lon, lat = study["coords"]
            year = args.year
            print(f"No coordinates provided. Defaulting to: {study['name']} ({lon}, {lat})")
        else:
            lon, lat = args.lon, args.lat
            year = args.year

    try:
        run_pipeline(
            lon=lon,
            lat=lat,
            year=year,
            threshold=args.threshold,
            top_n=args.top_n,
            project=args.project,
            output_json=args.output,
        )
    except Exception as e:
        print(f"\n[ERROR] Pipeline execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
