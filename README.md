# GeoSimAI

**GeoSimAI** is a machine learning framework for geospatial similarity analysis using Google Earth Engine annual satellite embeddings (DeepMind AlphaEarth Foundations). It enables users to select a reference location and automatically discover, rank, and visualize environmentally and geophysically similar locations within a defined study region without relying on hand-engineered vegetation or surface indices.

---

## Guidelines & Configuration

- [Agent Guidelines (AGENTS.md)](AGENTS.md) — Core directives and architecture conventions.

---

## Quick Start (Preview)

### Prerequisites
- Python 3.10+
- A Google Cloud Project with the Google Earth Engine API enabled (Community tier recommended)

### Setup
```bash
# Clone the repository
git clone https://github.com/<username>/GeoSimAI.git
cd GeoSimAI

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1   # On Windows
# source venv/bin/activate    # On Linux/macOS

# Install dependencies (once requirements.txt is populated)
pip install -r requirements.txt

# Authenticate Earth Engine (local development)
earthengine authenticate
```

### Running the Application
```bash
python run.py
```
Open your browser and navigate to `http://127.0.0.1:5000` to interact with the map interface.
