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
from src.core.clustering import run_spatial_clustering
from src.core.optical import (
    get_sentinel2_composite,
    compute_spectral_indices,
    get_location_thumbnail_url,
    batch_get_thumbnail_urls,
    sample_optical_indices,
    generate_similarity_description,
)
from src.core.database import (
    init_db,
    log_query,
    get_history,
    add_bookmark,
    get_bookmarks,
    delete_bookmark,
)

# Initialize SQLite database
init_db()

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
                "name": "Muzaffarabad Valley",
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
            # Fallback to Case Study A (Domel River Confluence)
            coords = Config.CASE_STUDIES["A_RIVER"]["coords"]
            ref_vector = extract_point_embedding(image, lon=coords[0], lat=coords[1])
            ref_info = {"type": "point", "coordinates": coords, "preset": "A_RIVER"}

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
            embedding_image=image,
        )

        # Optical Sentinel-2 True-Color Thumbnails & Physical Spectral Indices
        try:
            s2_composite = get_sentinel2_composite(year=year, aoi=aoi)
            # Reference thumbnail
            if "coordinates" in ref_info:
                ref_lon, ref_lat = ref_info["coordinates"][0], ref_info["coordinates"][1]
                ref_info["thumbnail_url"] = get_location_thumbnail_url(
                    s2_composite, lon=ref_lon, lat=ref_lat, year=year
                )
            else:
                ref_lon, ref_lat = Config.CASE_STUDIES["A_RIVER"]["coords"]

            # If candidates exist, batch compute spectral indices and optical crops
            if matches:
                indices_img = compute_spectral_indices(s2_composite)
                all_pts = [{"lon": ref_lon, "lat": ref_lat}] + [
                    {"lon": m["lon"], "lat": m["lat"]} for m in matches
                ]
                sampled = sample_optical_indices(indices_img, all_pts)
                ref_indices = sampled[0] if sampled else {"ndvi": 0.0, "ndbi": 0.0, "ndmi": 0.0}
                ref_info["indices"] = ref_indices

                match_coords = [(m["lon"], m["lat"]) for m in matches]
                match_thumbs = batch_get_thumbnail_urls(s2_composite, match_coords, year=year)

                for i, m in enumerate(matches):
                    m_idx = sampled[i + 1] if len(sampled) > i + 1 else {"ndvi": 0.0, "ndbi": 0.0, "ndmi": 0.0}
                    m["indices"] = m_idx
                    m["thumbnail_url"] = match_thumbs[i] if i < len(match_thumbs) else ""
                    desc_res = generate_similarity_description(ref_indices, m_idx)
                    m["description"] = desc_res["text"]
                    m["similar_traits"] = desc_res["similar_traits"]
                    m["deltas"] = desc_res["deltas"]
        except Exception:
            # Graceful non-blocking fallback if optical retrieval experiences transient quota/network latency
            ref_info.setdefault("thumbnail_url", "")
            for m in matches:
                m.setdefault("thumbnail_url", "")
                m.setdefault("description", "Both areas share latent structural characteristics in the 64-D embedding space.")
                m.setdefault("similar_traits", [])

        # Log query to SQLite history
        ref_label = data.get("label") or (
            f"Point ({ref_info['coordinates'][1]:.4f}, {ref_info['coordinates'][0]:.4f})"
            if "coordinates" in ref_info
            else "Geometry Query"
        )
        top_score = matches[0]["score"] if matches else None
        try:
            log_query(
                lon=float(ref_info.get("coordinates", [0, 0])[0]),
                lat=float(ref_info.get("coordinates", [0, 0])[1]),
                year=year,
                threshold=threshold,
                top_n=top_n,
                match_count=len(matches),
                top_score=top_score,
                label=ref_label,
            )
        except Exception:
            pass  # Non-blocking persistence

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


@api_bp.route("/thumbnail", methods=["GET"])
def get_thumbnail_endpoint():
    """Retrieve Sentinel-2 true-color crop URL for given coordinates and year."""
    lon = float(request.args.get("lon", 73.465))
    lat = float(request.args.get("lat", 34.383))
    year = int(request.args.get("year", Config.DEFAULT_YEAR))
    try:
        initialize_earth_engine()
        s2 = get_sentinel2_composite(year=year)
        url = get_location_thumbnail_url(s2, lon=lon, lat=lat, year=year)
        return jsonify({"success": True, "url": url, "lon": lon, "lat": lat, "year": year})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route("/cluster", methods=["POST"])
def run_clustering_endpoint():
    """Execute unsupervised spatial k-means clustering across the AOI."""
    data = request.get_json() or {}
    year = int(data.get("year", Config.DEFAULT_YEAR))
    n_clusters = int(data.get("n_clusters", 5))

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

        image = load_embedding_image(year=year, aoi=aoi)
        cluster_result = run_spatial_clustering(
            image=image,
            aoi=aoi,
            n_clusters=n_clusters,
            year=year,
        )

        return jsonify(
            {
                "success": True,
                "year": year,
                "n_clusters": cluster_result["n_clusters"],
                "palette": cluster_result["palette"],
                "clusters": cluster_result.get("clusters", []),
                "tile_url": cluster_result["tile_url"],
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route("/history", methods=["GET"])
def get_query_history():
    """Retrieve reverse-chronological query history."""
    try:
        limit = int(request.args.get("limit", 30))
        history = get_history(limit=limit)
        return jsonify({"success": True, "history": history})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route("/bookmarks", methods=["GET"])
def list_bookmarks():
    """Retrieve all bookmarked geographic sites."""
    try:
        bookmarks = get_bookmarks()
        return jsonify({"success": True, "bookmarks": bookmarks})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route("/bookmarks", methods=["POST"])
def create_bookmark():
    """Create a new bookmark."""
    data = request.get_json() or {}
    name = data.get("name")
    lon = data.get("lon")
    lat = data.get("lat")

    if not name or lon is None or lat is None:
        return jsonify({"success": False, "error": "name, lon, and lat are required"}), 400

    try:
        category = data.get("category", "General")
        description = data.get("description", "")
        b_id = add_bookmark(
            name=name,
            lon=float(lon),
            lat=float(lat),
            category=category,
            description=description,
        )
        return jsonify({"success": True, "id": b_id}), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route("/bookmarks/<int:bookmark_id>", methods=["DELETE"])
def remove_bookmark(bookmark_id: int):
    """Delete a bookmark by ID."""
    try:
        deleted = delete_bookmark(bookmark_id)
        return jsonify({"success": True, "deleted": deleted})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

