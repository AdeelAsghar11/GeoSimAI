"""Smoke test to verify Earth Engine connection and collection access.

Usage:
    python -m src.core.smoke_test [--project PROJECT_ID]
"""

import argparse
import sys
from typing import Optional

from src.config import Config


def run_smoke_test(project: Optional[str] = None) -> bool:
    """Verify Google Earth Engine initialization and access to DeepMind AlphaEarth collection.

    Args:
        project: Google Cloud project ID. If None, uses Config.GEE_PROJECT or default.

    Returns:
        True if all checks pass, False otherwise.
    """
    print("=" * 60)
    print("GeoSimAI — Earth Engine & AlphaEarth Smoke Test")
    print("=" * 60)

    # 1. Import ee
    try:
        import ee
    except ImportError:
        print("[FAIL] 'ee' (earthengine-api) is not installed.")
        print("       Run: pip install -r requirements.txt")
        return False

    print("[PASS] earthengine-api library imported successfully.")

    # 2. Initialize Earth Engine
    project_id = project or Config.GEE_PROJECT or None
    print(f"[*] Initializing Earth Engine (project: {project_id or 'default/ADC'})...")

    try:
        if project_id:
            ee.Initialize(project=project_id)
        else:
            ee.Initialize()
        print("[PASS] Earth Engine initialized successfully.")
    except Exception as e:
        print(f"[FAIL] Earth Engine initialization failed:\n       {e}")
        print("\nFix suggestions:")
        print("  1. Authenticate locally: Run 'earthengine authenticate'")
        print("  2. If using a specific project: Run with '--project <YOUR_GCP_PROJECT_ID>'")
        print("     or set environment variable GEE_PROJECT=<YOUR_GCP_PROJECT_ID>")
        return False

    # 3. Verify AlphaEarth Collection
    print(f"[*] Checking dataset: {Config.GEE_DATASET_ID}...")
    try:
        collection = ee.ImageCollection(Config.GEE_DATASET_ID)
        sample_img = collection.filterDate("2023-01-01", "2023-12-31").first()

        band_names = sample_img.bandNames().getInfo()
        print(f"[PASS] Successfully accessed collection. Found {len(band_names)} bands.")

        # Check for 64 latent bands
        expected_bands = Config.EMBEDDING_BANDS
        missing_bands = [b for b in expected_bands if b not in band_names]

        if not missing_bands:
            print(f"[PASS] All 64 embedding bands (A00 - A63) verified.")
        else:
            print(f"[WARN] Missing expected bands: {missing_bands[:5]}...")

        # Image footprint / metadata test
        date_start = sample_img.get("system:time_start").getInfo()
        print(f"[PASS] Sample 2023 image time_start: {date_start}")

        print("=" * 60)
        print("[SUCCESS] All Earth Engine connectivity checks passed!")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"[FAIL] Failed to query {Config.GEE_DATASET_ID}:\n       {e}")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GeoSimAI Earth Engine Smoke Test")
    parser.add_argument(
        "--project",
        type=str,
        default=None,
        help="Google Cloud project ID registered with Earth Engine",
    )
    args = parser.parse_args()
    success = run_smoke_test(project=args.project)
    sys.exit(0 if success else 1)
