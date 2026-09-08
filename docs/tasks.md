# Tasks Checklist — GeoSimAI

Track active, completed, and pending tasks. Check items off immediately when completed (`[x]`). Add newly discovered granular sub-tasks as work progresses.

---

## Phase 0: Setup & Infrastructure
- [x] Initialize Git repository and link remote `git@github.com:AdeelAsghar11/GeoSimAI.git`.
- [x] Create `.gitignore` ignoring virtual environments, secrets, proposal directory, and temporary data.
- [x] Create cross-tool agent guidelines (`AGENTS.md` and `CLAUDE.md`).
- [x] Scaffold living documentation system (`docs/PRD.md`, `docs/TRD.md`, `docs/roadmap.md`, `docs/tasks.md`, `docs/progress.md`, `docs/decisions.md`, `README.md`).
- [x] Create Python virtual environment (`venv`) and initial `requirements.txt` (`earthengine-api`, `google-auth`, `flask`, `numpy`, `pandas`, `scikit-learn`, `pytest`).
- [x] Write a smoke test script (`src/core/smoke_test.py`) to verify Earth Engine connectivity and collection accessibility.
- [x] Register Google Cloud Project and configure Earth Engine Community Tier access (150 EECU-hours/mo) — Project: `geosimai`.
- [x] Establish Earth Engine authentication (local `earthengine authenticate` and `earthengine set_project geosimai`).



---

## Phase 1: Core Similarity Engine (MVP Backend)
- [x] Implement GEE client initialization wrapper with ADC and local fallback (`src/core/client.py`).
- [x] Implement embedding extraction module for single point coordinates (`src/core/extraction.py`).
- [x] Implement spatial mean-pooling aggregation for polygon geometries (`src/core/extraction.py`).
- [x] Implement server-side vector dot product computation for candidate AOI pixels (`src/core/similarity.py`).
- [x] Implement similarity score clipping and tile visualization map ID generator (`src/core/similarity.py`).
- [x] Implement top-N candidate coordinate sampling and descending ranking (`src/core/similarity.py`).
- [x] Create an end-to-end prototype runner / demo script to execute a sample query and print results (`src/core/pipeline.py`).
- [x] Write automated unit tests for vector normalization and similarity math (`tests/test_similarity.py`, `tests/test_extraction.py`).


---

## Phase 2: Web Interface & API Integration
- [x] Implement Flask application factory and core configuration (`run.py`, `src/config.py`, `src/__init__.py`).
- [x] Implement `GET /api/health` and `GET /api/metadata` endpoints (`src/api/routes.py`).
- [x] Implement `POST /api/extract` endpoint returning point/polygon embedding signatures (`src/api/routes.py`).
- [x] Implement `POST /api/similarity` endpoint returning tile URLs and top-N ranked matches (`src/api/routes.py`).
- [x] Build basic HTML5/CSS single-page application structure (`src/static/index.html`, `src/static/css/style.css`).
- [x] Integrate Leaflet.js map with tile providers and click-to-pick coordinate marker (`src/static/js/app.js`).
- [x] Add AOI bounding box overlay and click-to-pick coordinate tool.
- [x] Add control panel for selecting year (2017–2024), threshold slider, and top-N limit.
- [x] Implement dynamic Earth Engine tile layer overlay on Leaflet when query finishes.
- [x] Implement ranked results sidebar table with click-to-zoom on matched coordinates.
- [x] Add loading indicators and friendly error handling for quota/network timeouts.


---

## Phase 3: Validation & Empirical Evaluation
- [x] Select 2–3 concrete case study locations and years based on human supervisor confirmation (`src/config.py`).
- [x] Execute reference queries and record similarity score distributions across diverse land covers (`src/core/evaluation.py`).
- [x] Quantify score separation between matching biomes and non-matching biomes (`src/core/evaluation.py`).
- [x] Generate interactive dual-basemap overlays in web UI (satellite basemap vs. similarity heatmap).
- [x] Document false-positive, false-negative edge cases and score distributions in a formal validation report (`docs/validation_report.md`).


---

## Phase 4: Extensions & Stretch Goals
- [x] Implement unsupervised spatial clustering (`ee.Clusterer.wekaKMeans`) over the AOI embedding bands (`src/core/clustering.py`).
- [x] Add clustering layer toggle, opacity slider, and dynamic color legend to frontend map interface.
- [x] Design lightweight SQLite database schema for saved queries and bookmarked reference points (`src/core/database.py`).
- [x] Implement session history and bookmarking endpoints in Flask backend (`src/api/routes.py`).
- [x] Create `Dockerfile` and `.dockerignore` for containerized deployment.
- [x] Finalize code cleanup, documentation refresh, and presentation demo packaging.

---

## Phase 5: Muzaffarabad Migration & Optical Verification Features
- [x] Migrate benchmark Area of Interest to Muzaffarabad Valley (`[73.42, 34.32, 73.60, 34.42]`, ~183 km²).
- [x] Configure 3 new validation case studies: Domel River Confluence (default active), Muzaffarabad City Core, and Pir Chinasi Alpine Forest (`src/config.py`).
- [x] Update database seed bookmarks and empirical ground-truth sites to Muzaffarabad landmarks (`src/core/database.py`, `src/core/evaluation.py`).
- [x] Integrate Sentinel-2 optical imagery pipeline (`COPERNICUS/S2_SR_HARMONIZED`) for true-color satellite crops (`src/core/optical.py`).
- [x] Implement in-memory cached optical thumbnail generator with parallel retrieval (`src/core/optical.py`, `src/api/routes.py`).
- [x] Compute physical spectral indices (NDVI, NDBI, NDMI) and synthesize deterministic plain-language similarity descriptions (`src/core/optical.py`).
- [x] Add dynamic cycling loading copy to search execution button in UI (`src/static/js/app.js`).
- [x] Render side-by-side satellite crops (Reference vs. Match) and plain-language descriptions in match cards (`src/static/index.html`, `src/static/css/style.css`, `src/static/js/app.js`).
- [x] Purge all legacy references to Islamabad and Rawalpindi across UI, copy, styles, and configs.
- [x] Add comprehensive unit test suite for optical spectral analysis (`tests/test_optical.py`).

