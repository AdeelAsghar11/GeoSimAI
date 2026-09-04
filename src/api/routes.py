"""Flask REST API routes for GeoSimAI."""

from typing import Any, Dict, List
import ee
from flask import Blueprint, jsonify, request

from src.config import Config
from src.core.client import initialize_earth_engine, load_embedding_image
from src.core.extraction import extract_point_embedding, extract_polygon_embedding
from src.core.similarity import (
    compute_similarity_image,
    get_similarity_map_id,
    get_top_matches,
)

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/health", methods=["GET"])
def health_check():
    """Health check and Earth Engine connection status."""
    ee_ready = False
    try:
        initialize_earth_engine()
        ee_ready = True
    except Exception:
        pass

    return jsonify(
        {
            "status": "healthy",
            "ee_initialized": ee_ready,
            "version": "0.1.0",
        }
    )


@api_bp.route("/metadata", methods=["GET"])
def get_metadata():
    """Retrieve application configuration, dataset info, and presets."""
    return jsonify(
        {
            "dataset_id": Config.GEE_DATASET_ID,
            "embedding_dim": Config.EMBEDDING_DIM,
            "available_years": Config.AVAILABLE_YEARS,
            "default_year": Config.DEFAULT_YEAR,
            "default_aoi": {
                "name": "Islamabad-Rawalpindi Twin Cities",
                "bounds": Config.DEFAULT_AOI_BOUNDS,
                "geojson": Config.DEFAULT_AOI_GEOJSON,
            },
            "case_studies": Config.CASE_STUDIES,
            "color_palette": Config.SIMILARITY_PALETTE,
        }
    )


@api_bp.route("/extract", methods=["POST"])
def extract_embedding():
    """Extract 64-D embedding vector for a given point or polygon."""
    data = request.get_json() or {}
    year = int(data.get("year", Config.DEFAULT_YEAR))

    try:
        initialize_earth_engine()

        if "lon" in data and "lat" in data:
            lon = float(data["lon"])
            lat = float(data["lat"])
            point = ee.Geometry.Point([lon, lat])
            image = load_embedding_image(year=year, aoi=point)
            vector = extract_point_embedding(image, lon=lon, lat=lat)
            return jsonify(
                {
                    "success": True,
                    "type": "point",
                    "coordinates": [lon, lat],
                    "year": year,
                    "vector": vector,
                }
            )

        elif "geometry" in data:
            geom = data["geometry"]
            ee_geom = ee.Geometry(geom)
            image = load_embedding_image(year=year, aoi=ee_geom)
            vector = extract_polygon_embedding(image, geometry=ee_geom)
            return jsonify(
                {
                    "success": True,
                    "type": "polygon",
                    "year": year,
                    "vector": vector,
                }
            )

        else:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Must provide either (lon, lat) or geometry",
                    }
                ),
                400,
            )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route("/similarity", methods=["POST"])
def run_similarity():
    """Execute in-engine vector dot product similarity search."""
    data = request.get_json() or {}
    year = int(data.get("year", Config.DEFAULT_YEAR))
    threshold = float(data.get("threshold", 0.75))
    top_n = int(data.get("top_n", Config.DEFAULT_TOP_N))

    # Parse AOI
    aoi_data = data.get("aoi")
    try:
        initialize_earth_engine()

        if aoi_data and isinstance(aoi_data, list) and len(aoi_data) == 4:
            aoi = ee.Geometry.BBox(
                aoi_data[0], aoi_data[1], aoi_data[2], aoi_data[3]
            )
        elif aoi_data and isinstance(aoi_data, dict):
            aoi = ee.Geometry(aoi_data)
        else:
            b = Config.DEFAULT_AOI_BOUNDS
            aoi = ee.Geometry.BBox(b[0], b[1], b[2], b[3])

        # Load annual composite mosaic
        image = load_embedding_image(year=year, aoi=aoi)

        # Obtain reference vector
        if "vector" in data and len(data["vector"]) == Config.EMBEDDING_DIM:
            ref_vector = [float(x) for x in data["vector"]]
            ref_info = {"type": "precomputed_vector"}
        elif "lon" in data and "lat" in data:
            lon = float(data["lon"])
            lat = float(data["lat"])
            ref_vector = extract_point_embedding(image, lon=lon, lat=lat)
            ref_info = {"type": "point", "coordinates": [lon, lat]}
        elif "geometry" in data:
            geom = data["geometry"]
            ee_ref_geom = ee.Geometry(geom)
            ref_vector = extract_polygon_embedding(image, geometry=ee_ref_geom)
            ref_info = {"type": "polygon"}
        else:
            # Fallback to Case Study C (Fatima Jinnah Park)
            coords = Config.CASE_STUDIES["C_VEGETATION"]["coords"]
            ref_vector = extract_point_embedding(image, lon=coords[0], lat=coords[1])
            ref_info = {"type": "point", "coordinates": coords, "preset": "C_VEGETATION"}

        # Compute similarity image
        sim_image = compute_similarity_image(
            image=image, reference_vector=ref_vector, aoi=aoi
        )

        # Generate Slippy map XYZ tile format
        tile_info = get_similarity_map_id(
            similarity_image=sim_image,
            min_val=threshold,
            max_val=1.0,
            palette=Config.SIMILARITY_PALETTE,
        )

        # Extract top ranked candidates
        matches = get_top_matches(
            similarity_image=sim_image,
            aoi=aoi,
            threshold=threshold,
            top_n=top_n,
        )

        return jsonify(
            {
                "success": True,
                "year": year,
                "threshold": threshold,
                "reference": ref_info,
                "tile_url": tile_info["tile_url"],
                "matches": matches,
                "total_matches": len(matches),
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
