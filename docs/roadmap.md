# Project Roadmap — GeoSimAI

This document outlines the phased development roadmap for GeoSimAI. Each phase defines a clear objective and a verifiable exit criterion.

---

## Phase 0: Setup & Infrastructure
- **One-Line Goal:** Establish project repository, scaffolding documentation, Earth Engine registration with Community tier, and verified local authentication.
- **One-Line Exit Criterion:** A Python script successfully initializes Earth Engine via ADC or interactive auth and retrieves metadata from `GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL`.

### Milestones
- [x] Repository initialization (`git init`, `.gitignore`, remote linked).
- [x] Persistent documentation scaffolding (`AGENTS.md`, `CLAUDE.md`, `README.md`, `docs/*`).
- [x] Local Python virtual environment created with core dependencies installed (`earthengine-api`, `flask`, `numpy`, `pandas`, `scikit-learn`, `pytest`).
- [ ] Google Cloud project registered and Earth Engine API enabled on Community Tier (150 EECU-hours/month).
- [ ] Service Account ADC or local authentication confirmed working.

---

## Phase 1: Core Similarity Engine (MVP Backend — Target Milestone)
- **One-Line Goal:** Build and verify the core Python processing pipeline for embedding extraction, mean pooling, dot-product similarity computation, and ranked retrieval without a web UI.
- **Target Milestone Status:** Primary target deliverable. *(Note: Adeel to confirm with supervisor/committee if a specific evaluation checkpoint requires web UI demonstration earlier).*
- **One-Line Exit Criterion:** A standalone Python script or notebook takes arbitrary reference coordinates, an AOI, and a year, and outputs ranked similar coordinates with scores and a generated tile map ID.

### Milestones
- [ ] Earth Engine client wrapper module with authentication & initialization (`src/core/client.py`).
- [ ] Embedding extraction module for points and mean-pooled polygons (`src/core/extraction.py`).
- [ ] In-engine vector dot product computation pipeline across candidate AOI pixels (`src/core/similarity.py`).
- [ ] Top-N coordinate extraction and similarity score ranking routines (`src/core/similarity.py`).
- [ ] End-to-end CLI execution script with benchmark AOI defaults (`src/core/pipeline.py`).
- [ ] Automated unit tests for vector math, pooling, and ranking (`tests/test_similarity.py`, `tests/test_extraction.py`).

---

## Phase 2: Web Interface & API Integration
- **One-Line Goal:** Connect the core similarity engine to a lightweight Flask backend and an interactive Leaflet web frontend.
- **One-Line Exit Criterion:** A user can open the browser, click a point on the map, trigger a search, and view both the similarity heatmap tile overlay and a ranked match table.

### Milestones
- [ ] Flask REST API endpoints (`/api/metadata`, `/api/extract`, `/api/similarity`).
- [ ] Leaflet.js interactive map frontend with coordinate picking and bounding box selection.
- [ ] Visualization layer integrating Earth Engine Slippy Map XYZ tile layers.
- [ ] Results panel displaying ranked matches, coordinates, and similarity scores.
- [ ] Error handling and loading state animations for long-running GEE queries.

---

## Phase 3: Validation & Empirical Evaluation
- **One-Line Goal:** Validate the retrieval pipeline using concrete ground-truth case studies with quantitative fidelity metrics.
- **One-Line Exit Criterion:** An evaluation report documenting retrieval accuracy, score distributions, and confusion analysis for 3 specific environmental scenarios.

### Milestones
- [ ] Benchmark Area of Interest established: Islamabad/Rawalpindi metropolitan region (`[72.80, 33.45, 73.25, 33.82]`, Year: 2023).
- [ ] **Case Study A:** Potohar plateau agricultural land retrieval (`[73.140, 33.670]`) vs. urban and barren land.
- [ ] **Case Study B:** Rawal Lake deep water delineation (`[73.123, 33.702]`) vs. regional water bodies & dry land.
- [ ] **Case Study C:** Islamabad urban greenery (Fatima Jinnah Park, `[73.018, 33.704]`) vs. Margalla forest canopy (`[73.060, 33.750]`) vs. built-up.
- [ ] Collect similarity score distributions and analyze false positive / false negative patterns.
- [ ] Compile quantitative evaluation tables and visual comparison figures for the FYP report.

---

## Phase 4: Extensions & Stretch Goals (Deferred)
- **One-Line Goal:** Implement secondary analytical features including spatial clustering, session persistence, and deployment hardening.
- **Scope Notice:** Explicitly deferred until Phases 1–3 are fully validated.
- **One-Line Exit Criterion:** An analyst can perform k-means spatial clustering over an AOI and export or bookmark historical query sessions.

### Milestones
- [ ] Unsupervised spatial clustering (`ee.Clusterer.wekaKMeans`, FR-008) across the 64 embedding dimensions.
- [ ] SQLite database integration for saving query sessions, bookmarked sites, and user annotations.
- [ ] Containerization (Dockerfile) and deployment configuration for Google Cloud Run / Render free tier.
- [ ] UI polish and responsive layout refinement.

