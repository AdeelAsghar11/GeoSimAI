# Project Roadmap — GeoSimAI

This document outlines the phased development roadmap for GeoSimAI. Each phase defines a clear objective and a verifiable exit criterion.

---

## Phase 0: Setup & Infrastructure
- **One-Line Goal:** Establish project repository, scaffolding documentation, Earth Engine registration with Community tier, and verified local authentication.
- **One-Line Exit Criterion:** A Python script successfully initializes Earth Engine via ADC or interactive auth and retrieves metadata from `GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL`.

### Milestones
- [x] Repository initialization (`git init`, `.gitignore`, remote linked).
- [x] Persistent documentation scaffolding (`AGENTS.md`, `CLAUDE.md`, `README.md`, `docs/*`).
- [ ] Google Cloud project registered and Earth Engine API enabled on Community Tier (150 EECU-hours/month).
- [ ] Local Python virtual environment created with initial dependencies installed.
- [ ] Service Account ADC or local authentication confirmed working.

---

## Phase 1: Core Similarity Engine (MVP Backend)
- **One-Line Goal:** Build and verify the core Python processing pipeline for embedding extraction, mean pooling, dot-product similarity computation, and ranked retrieval without a web UI.
- **One-Line Exit Criterion:** A standalone Python script or Jupyter notebook takes arbitrary reference coordinates, an AOI, and a year, and outputs ranked similar coordinates with scores and a generated tile map ID.

### Milestones
- [ ] Earth Engine wrapper module for dataset loading and year/AOI spatial filtering.
- [ ] Point extraction and polygon mean-pooling aggregation logic.
- [ ] In-engine vector dot product computation pipeline across candidate AOI pixels.
- [ ] Top-N coordinate extraction and similarity score ranking routines.
- [ ] Unit tests covering array math, normalization, and bounds validation.

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
- **One-Line Exit Criterion:** An evaluation report documenting retrieval accuracy, score distributions, and confusion analysis for 2–3 specific environmental scenarios.

### Milestones
- [ ] Define 2–3 concrete evaluation case studies (e.g., water bodies, agricultural crops, dense urban vs. forest).
- [ ] Execute similarity queries against known ground-truth locations and collect score distributions.
- [ ] Analyze false positive / false negative patterns and score sensitivity across thresholds.
- [ ] Compile quantitative evaluation tables and visual comparison figures for the FYP report.

---

## Phase 4: Extensions & Stretch Goals
- **One-Line Goal:** Implement secondary analytical features including spatial clustering, session persistence, and deployment hardening.
- **One-Line Exit Criterion:** An analyst can perform k-means spatial clustering over an AOI and export or bookmark historical query sessions.

### Milestones
- [ ] Unsupervised spatial clustering (`ee.Clusterer.wekaKMeans`) across the 64 embedding dimensions.
- [ ] SQLite database integration for saving query sessions, bookmarked sites, and user annotations.
- [ ] Containerization (Dockerfile) and deployment configuration for Google Cloud Run / Render free tier.
- [ ] UI polish and responsive layout refinement.
