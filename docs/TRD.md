# Technical Requirements Document (TRD) — GeoSimAI

## 1. System Architecture

GeoSimAI is designed as a decoupled, three-tier cloud-assisted geospatial application:

```
[Browser Client: Leaflet Map UI]
            │  HTTP REST (JSON & Slippy Map Tiles)
            ▼
[Backend Server: Python Flask]
            │  GEE Python API (Service Account ADC)
            ▼
[Compute & Data Engine: Google Earth Engine Cloud]
            │
      [SQLite DB: Local Session & Query Store (Optional)]
```

### Component Breakdown
1. **Frontend Client (Presentation Layer):**
   - Single-page application built with Vanilla HTML5, CSS3, and JavaScript.
   - Interactive mapping powered by Leaflet.js (or OpenLayers).
   - Capable of capturing user click coordinates, bounding boxes, polygon drawings, and rendering Earth Engine XYZ tile overlays and tabular ranking outputs.
2. **Backend Application (Application Layer):**
   - Python Flask web service exposing RESTful API endpoints.
   - Handles request validation, spatial geometry transformation, orchestrates calls to Google Earth Engine via the Python client, and packages results for client rendering.
3. **Geospatial & Machine Learning Engine (Compute Layer):**
   - Google Earth Engine (GEE). Executes heavy raster operations, spatial filtering, pixel-wise dot product calculations, tile rendering, and regional reductions server-side on Google infrastructure.
4. **Local Data Store (Persistence Layer - Optional/MVP+):**
   - SQLite embedded database. Stores user query history, bookmark locations, and cached reference vectors without requiring an external database daemon.

---

## 2. Dataset Specifications

- **Dataset Identifier:** `GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL`
- **Origin:** Google Earth Engine and Google DeepMind AlphaEarth Foundations.
- **Spatial Resolution:** 10 meters per pixel.
- **Band Configuration:** 64 continuous latent bands named `A00`, `A01`, `A02`, ..., `A63`.
- **Band Characteristics:** Dimensionless, normalized unit-length vectors with values ranging strictly between `-1.0` and `+1.0`.
- **Temporal Coverage:** Annual composites available from calendar years 2017 through 2024.
- **Metadata Timestamps:** Each annual composite image has `system:time_start` and `system:time_end` set to the respective calendar year boundaries (e.g., `2023-01-01T00:00:00` to `2024-01-01T00:00:00`).
- **Spatial Footprint & Projection:** Images are organized in local UTM projection tiles spanning approximately 163,840 m by 163,840 m per tile.
- **Mosaicking Requirement:** For any Area of Interest (AOI) spanning across tile boundaries, an `imageCollection.filterBounds(aoi).mosaic()` operation is required to ensure gap-free coverage.
- **Linear Composability:** The embedding dataset is explicitly trained to be linearly composable. Spatial averaging (mean pooling) across pixel vectors preserves geometric distance relationships in embedding space.

### Secondary Optical Dataset (Visual Verification & Interpretable Indices)
- **Dataset Identifier:** `COPERNICUS/S2_SR_HARMONIZED` (Sentinel-2 Level-2A Surface Reflectance, Harmonized)
- **Spatial Resolution:** 10m (B2, B3, B4, B8) and 20m (B11).
- **Temporal Filter:** Filtered to match benchmark embedding year, `CLOUDY_PIXEL_PERCENTAGE < 20`, reduced to annual median composite.
- **RGB True-Color Imagery:** Generated from Red (`B4`), Green (`B3`), and Blue (`B2`), normalized [0, 3000].
- **Spectral Indices Computed:**
  - $\text{NDVI} = \frac{B8 - B4}{B8 + B4}$ (Vegetation canopy density)
  - $\text{NDBI} = \frac{B11 - B8}{B11 + B8}$ (Built-up impervious surface density)
  - $\text{NDMI} = \frac{B8 - B11}{B8 + B11}$ (Canopy and surface moisture)
- **Purpose:** Supplies verifiable true-color crops and physically grounded optical indices for rule-based similarity descriptions without violating the non-negotiable principle against decomposing latent embeddings into physical pseudo-variables.

---

## 3. Core Algorithms and Mathematical Workflow

The core processing pipeline builds upon Google Earth Engine's documented reference pattern (*"Similarity Search with Satellite Embedding Dataset"*, `satellite-embedding-05-similarity-search`):

```
Reference Point/Polygon
         │
         ▼
[1. Extraction & Pooling] ──► 64-D Vector (v_ref)
                                     │
AOI Raster (64-band image) ──────────┴─► [2. Array Dot Product]
                                                │
                                                ▼
                                    Single-band Similarity Image
                                                │
                 ┌──────────────────────────────┴─────────────────────────────┐
                 ▼                                                           ▼
      [3. Tile Layer Map URL]                                     [4. Top-N Candidate Extraction]
      (Visual Similarity Heatmap)                                 (Sample / reduceRegion / Ranking)
```

### Step 1: Embedding Extraction & Aggregation
- For a point reference coordinate $(x, y)$, sample the 64-band image at 10 m resolution:
  $$\mathbf{v}_{\text{ref}} = [A_{00}(x, y), A_{01}(x, y), \dots, A_{63}(x, y)]^T$$
- For a polygon or patch $R$, compute the spatial mean across all pixels inside the geometry:
  $$\mathbf{v}_{\text{ref}} = \frac{1}{|R|} \sum_{(x,y) \in R} \mathbf{v}(x,y)$$
  Because the embeddings are linearly composable, mean pooling yields an accurate, representative signature of the spatial region.

### Step 2: Vector Similarity Computation
Since all pixel embedding vectors $\mathbf{u}$ and the reference vector $\mathbf{v}_{\text{ref}}$ are unit-length ($\|\mathbf{u}\| = 1, \|\mathbf{v}_{\text{ref}}\| = 1$), the cosine similarity reduces directly to the vector dot product:
$$\text{Sim}(\mathbf{u}, \mathbf{v}_{\text{ref}}) = \mathbf{u} \cdot \mathbf{v}_{\text{ref}} = \sum_{i=0}^{63} u_i \cdot v_{\text{ref}, i}$$
This is implemented natively in Earth Engine using array arithmetic or band multiplying and summing (`multiply().reduce(ee.Reducer.sum())`), avoiding client-side pixel downloads.

### Step 3: Heatmap Generation & Tile Visualization
The resulting single-band continuous similarity raster (ranging from approximately 0 to 1 for positively correlated surfaces) is styled with a visual color palette (e.g., Viridis or Turbo) and served directly to the Leaflet frontend via an Earth Engine map ID / XYZ tile URL (`ee.Image.getMapId()`).

### Step 4: Top-N Match Extraction & Ranking
To extract discrete similar candidate sites:
1. Apply a threshold filter (e.g., $\text{Sim} \ge \tau$, default $\tau = 0.80$) to isolate high-similarity zones.
2. Convert contiguous high-value pixels or run `sampleRegions` / `stratifiedSample` within the masked AOI.
3. Order candidates descending by similarity score and return the top $N$ coordinates.

### Step 5: Optional Spatial Clustering (Stretch)
For broad spatial pattern analysis, sample candidate embedding vectors across the AOI and apply an unsupervised clustering algorithm (e.g., `ee.Clusterer.wekaKMeans(k)`) on the 64 bands to partition the landscape into $k$ spectral-semantic clusters.

---

## 4. API Design Sketch

The backend provides the following initial RESTful endpoints:

### `GET /api/health`
Health check and Earth Engine connection status.
- **Response:** `{"status": "ok", "ee_initialized": true, "version": "0.1.0"}`

### `GET /api/metadata`
Dataset temporal bounds, default demo AOIs, and configuration constants.
- **Response:**
  ```json
  {
    "dataset": "GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL",
    "available_years": [2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024],
    "embedding_dimensions": 64,
    "default_year": 2023,
    "default_aoi": {
      "name": "Muzaffarabad Valley",
      "bbox": [73.42, 34.32, 73.60, 34.42]
    }
  }
  ```

### `POST /api/extract`
Extract the 64-D embedding vector for a given point or polygon.
- **Request Body:**
  ```json
  {
    "year": 2023,
    "geometry": {
      "type": "Point",
      "coordinates": [73.0479, 33.6844]
    }
  }
  ```
- **Response:**
  ```json
  {
    "year": 2023,
    "vector_preview": [0.042, -0.115, 0.089, "... 64 values total"],
    "unit_norm": 0.9998
  }
  ```

### `POST /api/similarity`
Compute similarity map and retrieve top matches.
- **Request Body:**
  ```json
  {
    "year": 2023,
    "reference_geometry": {
      "type": "Point",
      "coordinates": [73.0479, 33.6844]
    },
    "aoi_bounds": [72.95, 33.55, 73.20, 33.78],
    "threshold": 0.80,
    "top_n": 10
  }
  ```
- **Response:**
  ```json
  {
    "tile_url_format": "https://earthengine.googleapis.com/v1/projects/.../maps/{mapid}/tiles/{z}/{x}/{y}",
    "matches": [
      {"rank": 1, "coordinates": [73.0512, 33.6890], "similarity": 0.962},
      {"rank": 2, "coordinates": [73.0821, 33.7104], "similarity": 0.941}
    ],
    "execution_time_ms": 1420
  }
  ```

---

## 5. Authentication, Hosting, and Deployment

### Server Authentication Architecture
Because the Flask server runs unattended in headless cloud and local environments, it **must not** rely on interactive browser authentication (`earthengine authenticate`). Instead, it uses Google Cloud Application Default Credentials (ADC) with a Service Account:

```python
import ee
import google.auth

# Non-interactive authentication pattern
credentials, project_id = google.auth.default(
    scopes=['https://www.googleapis.com/auth/earthengine']
)
ee.Initialize(credentials, project=project_id)
```
Reference: `google/earthengine-api` (demos/server-auth-python).

### Target Hosting Options
- **Primary Recommendation:** **Render** (Free Tier) or **Google Cloud Run** (Free Tier).
  - Both platforms permit unrestricted outbound HTTPS API calls necessary to communicate with Earth Engine endpoints.
  - *Cold Start Note:* Free instances spin down after inactivity; initial request latency of 30–60 seconds is normal.
- **Caveat on PythonAnywhere:** PythonAnywhere's free tier restricts outbound traffic strictly to a fixed domain allowlist. It is discouraged unless Earth Engine API domains (`*.googleapis.com`) are confirmed on the allowlist.

---

## 6. Constraints, Performance, and Quota Management

- **Compute Quota:** Noncommercial Earth Engine projects operate under a Community tier allowance of **150 EECU-hours per month**. Exceeding this quota does not terminate access; it places the project into a throttled, slower execution queue until the monthly reset.
- **Spatial Scope Enforcement:** Backend validation must reject AOIs exceeding a predefined bounding limit (e.g., max 2,500 km² per query for the demo) to avoid accidental compute depletion.
- **Mosaicking Overhead:** Queries covering multiple UTM tiles require server-side mosaicking (`ee.ImageCollection.mosaic()`), which incurs marginal additional compute. AOIs should be kept within 1 to 4 adjacent tiles for optimal responsiveness.
- **Client Latency Target:** Heatmap tile generation and top-N ranking must return within 15 seconds under normal Earth Engine operating conditions.

---

## 7. Technology Stack Selection & Decision Matrix

| Layer | Proposal Suggestion | Decision Made | Rationale & Reference |
| :--- | :--- | :--- | :--- |
| **Backend Framework** | Flask or Django | **Flask** | Minimal overhead, fast setup, lightweight REST API. [ADR-003](decisions.md#2026-09-04-backend-framework-selection) |
| **Database** | PostgreSQL or MySQL | **SQLite** | Zero cost, zero config, sufficient for single-user/demo needs. [ADR-004](decisions.md#2026-09-04-database-selection) |
| **Hosting Platform** | Cloud VM / Unspecified | **Cloud Run / Render (Free)** | Zero hosting cost, supports outbound GEE calls, auto-containerized. [ADR-005](decisions.md#2026-09-04-deployment-hosting-platform) |
| **Vector Search Method** | Vector methods (dot/cosine) | **EE Server-Side Dot Product** | Native execution on 10 m pixels without downloading raw rasters. [ADR-002](decisions.md#2026-09-04-similarity-metric-selection) |
| **Region Pooling** | Extract or aggregate | **Mean Pooling** | Dataset is linearly composable by design. [ADR-001](decisions.md#2026-09-04-region-aggregation-method) |

---

## 8. Future Scale Considerations (Non-MVP)

For production-scale deployment across continental or global scales containing billions of candidate pixels:
- **Vector Indexing (FAISS / ScaNN):** In a large precomputed scenario, embeddings would be exported to vector storage and indexed using Hierarchical Navigable Small World (HNSW) or Inverted File with Product Quantization (IVF-PQ) via FAISS.
- **Offline Batch Pipeline:** Earth Engine tasks would export offline embeddings as Cloud-Optimized GeoTIFFs (COGs) or Parquet vector shards to Google Cloud Storage.
- *Status:* **Explicitly not built for MVP.** GeoSimAI computes similarity on demand directly within Earth Engine over scoped AOIs.
