# AGENTS.md

## Project Overview
GeoSimAI is a machine learning framework for geospatial similarity analysis using annual satellite embeddings from Google Earth Engine (DeepMind AlphaEarth Foundations, `GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL`). Given a user-selected reference location (point, patch, or region), GeoSimAI computes vector similarity against candidate locations within a defined Area of Interest (AOI) to retrieve and rank environmentally and geophysically similar areas without manual feature engineering or single-band index decomposition.

## Tech Stack
- **Language & Runtime:** Python 3.10+
- **Geospatial & Compute:** Google Earth Engine Python API (`earthengine-api`), Google Cloud Auth (`google-auth`)
- **Scientific Computing & ML:** NumPy, Pandas, Scikit-learn
- **Backend Framework:** Flask (lightweight REST API)
- **Database:** SQLite (local file-based; no external database server needed for MVP)
- **Frontend:** Vanilla HTML5, CSS3, JavaScript (interactive map via Leaflet or OpenLayers)
- **GIS / Exploration:** QGIS (optional, manual/offline reference only)

## Setup, Run, and Test Commands

### 1. Environment Setup
```bash
# Create and activate virtual environment
python -m venv venv

# Windows (PowerShell)
.\venv\Scripts\Activate.ps1

# Linux / macOS
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Earth Engine Authentication
```bash
# Local development authentication (one-time interactive)
earthengine authenticate

# For server / unattended mode:
# Set GOOGLE_APPLICATION_CREDENTIALS=/path/to/service_account.json
```

### 3. Run Development Server
```bash
# Run Flask dev server
python run.py
# Or: flask --app app.py run --port 5000 --debug
```

### 4. Run Tests
```bash
# Run all unit and integration tests
pytest tests/ -v
```

## Code Style and Conventions
- **Style Guide:** Strict adherence to PEP 8. Clean, readable, well-commented code.
- **Type Hints:** Required on all public functions, methods, and API request/response schemas.
- **Naming Conventions:**
  - Modules and functions: `snake_case` (e.g., `extract_reference_embedding`, `compute_similarity`)
  - Classes: `PascalCase` (e.g., `EmbeddingExtractor`, `SimilarityService`)
  - Constants: `UPPER_SNAKE_CASE` (e.g., `DATASET_ID`, `EMBEDDING_DIM`)
- **Tests:** All tests reside in `tests/`. Unit tests for core math/aggregation should not require live Earth Engine network calls (use mocking/fixtures). Integration tests hitting Earth Engine should be clearly separated.

## Directory Layout
```
GeoSimAI/
├── AGENTS.md               # Cross-agent standing instructions (this file)
├── CLAUDE.md               # Claude Code pointer
├── README.md               # Human-facing overview and quickstart
├── .gitignore              # Ignored files (secrets, venv, proposal, data)
├── requirements.txt        # Python package dependencies
├── run.py                  # Application entry point
├── docs/                   # Living project memory and specifications
│   ├── PRD.md              # Product Requirements Document
│   ├── TRD.md              # Technical Requirements Document
│   ├── roadmap.md          # Phased milestones and exit criteria
│   ├── tasks.md            # Granular task checklist
│   ├── progress.md         # Reverse-chronological session logs
│   └── decisions.md        # Architecture and tooling decision log
├── src/                    # Backend application source code
│   ├── __init__.py
│   ├── config.py           # Configuration and environment settings
│   ├── core/               # Earth Engine & embedding processing engine
│   │   ├── __init__.py
│   │   ├── client.py       # Earth Engine initialization and authentication
│   │   ├── extraction.py   # Extraction and mean-pool aggregation
│   │   ├── similarity.py   # Vector similarity (dot product / cosine)
│   │   └── clustering.py   # Spatial clustering (optional/stretch)
│   ├── api/                # Flask API routes and controllers
│   │   ├── __init__.py
│   │   └── routes.py       # REST endpoints (similarity search, metadata)
│   └── static/             # Frontend web assets
│       ├── index.html      # Single page map interface
│       ├── css/
│       │   └── style.css
│       └── js/
│           └── app.js      # Map selection and API client logic
└── tests/                  # Test suite
    ├── __init__.py
    ├── test_similarity.py
    └── test_extraction.py
```

## Non-Negotiable Principles

1. **Never treat individual embedding bands (A00 to A63) as physical variables:**
   The 64 dimensions in `GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL` are learned latent representations from DeepMind AlphaEarth Foundations. They are dimensionless, unit-length, and mathematically meaningful only as a unified 64-D vector. Never decompose them into separate physical pseudo-variables (like NDVI, temperature, or moisture) in code, docstrings, comments, or UI copy.
2. **Keep the Area of Interest (AOI) strictly scoped:**
   Always bound queries to a manageable city or small regional AOI. Never launch an unbounded, country-wide, or global similarity sweep without explicit human approval. Noncommercial Earth Engine accounts operate under a 150 EECU-hour/month Community quota.
3. **Never silently introduce paid services or external dependencies:**
   Do not add paid cloud tiers, managed databases (e.g. paid RDS), commercial APIs, or custom domains without first logging them in [docs/decisions.md](file:///d:/GeoSimAI/docs/decisions.md) and securing explicit human approval. Default to free tiers (Google Cloud Run / Render free tier, SQLite).
4. **Prefer the simplest tool that works:**
   Use SQLite over Postgres for local/demo state. Use documented Google Earth Engine tutorial patterns (`satellite-embedding-05-similarity-search`) over unverified custom architectures. Any deviation must be justified in [docs/decisions.md](file:///d:/GeoSimAI/docs/decisions.md).

## Project Documentation Pointers
- **[docs/PRD.md](file:///d:/GeoSimAI/docs/PRD.md):** Product Requirements Document (problem statement, goals, non-goals, user stories, functional requirements, open questions).
- **[docs/TRD.md](file:///d:/GeoSimAI/docs/TRD.md):** Technical Requirements Document (architecture, data specifications, algorithms, API schemas, auth, quota constraints).
- **[docs/roadmap.md](file:///d:/GeoSimAI/docs/roadmap.md):** Phased project roadmap (Phase 0 Setup through Phase 4 Stretch) with exit criteria.
- **[docs/tasks.md](file:///d:/GeoSimAI/docs/tasks.md):** Granular task checklist; check off completed items immediately.
- **[docs/progress.md](file:///d:/GeoSimAI/docs/progress.md):** Reverse-chronological session history of work completed, blockers, and next steps.
- **[docs/decisions.md](file:///d:/GeoSimAI/docs/decisions.md):** Architectural decision records (ADRs) explaining the rationale behind design choices.
