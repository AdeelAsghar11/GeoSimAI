# Product Requirements Document (PRD) — GeoSimAI

## 1. Overview
Geospatial similarity analysis assesses how closely geographic locations resemble one another based on observable surface characteristics. In domains like environmental monitoring, agricultural assessment, urban and regional land-use planning, and natural resource management, analysts frequently need to identify regions sharing identical or analogous surface conditions.

Conventional workflows rely heavily on manual visual inspection or hand-engineered physical indices (e.g., NDVI, NDWI, surface temperature). These handcrafted heuristics often miss multidimensional, subtle environmental patterns across diverse data sources. **GeoSimAI** resolves this challenge by providing an automated machine learning framework powered by Google Earth Engine's annual satellite embedding dataset (`GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL`, developed by Google Earth Engine and Google DeepMind AlphaEarth Foundations). By projecting geographic locations into a continuous 64-dimensional latent embedding space, GeoSimAI enables rapid, objective similarity comparison, ranked retrieval, and interactive visualization across defined study areas.

---

## 2. Goals
- **G-1 (Data Access & Preprocessing):** Ingest and preprocess 64-dimensional annual satellite embedding imagery from Google Earth Engine for specified study boundaries and calendar years (2017–2024).
- **G-2 (Vector Representation):** Extract and represent reference locations at point, patch, or region levels, using mean pooling for polygon-level embedding aggregation.
- **G-3 (Similarity Metric):** Compute geospatial similarity between reference signatures and target areas using standardized vector operations (dot product / cosine similarity).
- **G-4 (Ranked Retrieval & Heatmaps):** Efficiently rank candidate locations within an Area of Interest (AOI), isolate top matches via thresholding, and generate continuous similarity heatmaps.
- **G-5 (Exploratory Clustering):** Provide optional spatial clustering capabilities to partition regions into coherent environmental groupings.
- **G-6 (Interactive Web Interface):** Deliver an intuitive, lightweight web interface allowing users to pick reference locations on an interactive map, configure search parameters, trigger similarity searches, and explore visual results.
- **G-7 (Rigorous Validation):** Validate retrieval accuracy and geospatial fidelity through empirical case studies, visual ground-truth comparisons, and error/anomaly analysis.

---

## 3. Non-Goals / Out of Scope
To maintain technical focus and respect computational quotas, the following are strictly out of scope:
- **No Real-Time Streaming:** The system will not process real-time or streaming satellite feeds; it relies strictly on annual composite embeddings.
- **No High-Resolution Object Detection:** GeoSimAI is not designed for fine-grained computer vision tasks (e.g., detecting individual vehicles, roofs, or trees) beyond the 10-meter pixel resolution.
- **No Decomposition into Physical Variables:** Individual embedding dimensions (`A00` through `A63`) **must never** be isolated or interpreted as physical variables (such as moisture or vegetation indices). The 64 dimensions represent a unified latent coordinate space and must always be processed collectively.
- **No Unbounded Global Sweeps:** The system will not execute unconstrained global or continental searches that exhaust Earth Engine compute quotas.

---

## 4. Users and Use Cases

### Target Users
- **Academic Researchers & Students:** Investigating remote sensing representations, climate analogs, or land-cover changes.
- **Agricultural & Forestry Planners:** Identifying areas with growing conditions or canopy signatures analogous to benchmark reference plots.
- **Environmental & Conservation Agencies:** Tracking ecosystem fragmentation and pinpointing habitats sharing characteristics with protected reserves.
- **Urban & Regional Planners:** Evaluating spatial growth patterns and identifying zones with similar surface and built-environment signatures.

### Primary Use Cases
1. **Analytic Site Retrieval:** An agricultural scientist selects a high-yield reference orchard and searches across a province to locate fields sharing similar surface properties.
2. **Ecological Analog Search:** An ecologist selects a degraded wetland polygon and identifies other regional water basins experiencing comparable surface transformations.
3. **Regional Land-Cover Inspection:** A municipal planner assesses an urban heat island zone and retrieves similarly paved and low-canopy tracts across neighboring districts.

---

## 5. User Stories and Acceptance Criteria

### US-01: Map-Based Reference Selection
**As an** analyst,  
**I want to** select a reference point or polygon on an interactive map and select a calendar year,  
**So that I can** specify the exact baseline environmental signature I wish to compare.

> **Scenario: Selecting a single reference point**  
> **Given** an interactive map centered over an AOI and a selected calendar year (e.g., 2023),  
> **When** the user clicks on a geographic coordinate,  
> **Then** a marker appears displaying the latitude/longitude, and the system extracts the corresponding 64-D embedding vector.

> **Scenario: Drawing a reference polygon**  
> **Given** a polygon selection tool activated on the map,  
> **When** the user draws and closes a bounding polygon,  
> **Then** the system computes the mean-pooled 64-D embedding vector across all constituent pixels.

---

### US-02: Scoped Similarity Search & Heatmap Generation
**As a** researcher,  
**I want to** define an Area of Interest (AOI) and initiate a similarity search,  
**So that I can** view a similarity heatmap highlighting how closely candidate pixels match the reference.

> **Scenario: Running similarity query within an AOI**  
> **Given** a valid reference embedding vector and a defined AOI polygon/bounding box,  
> **When** the user clicks "Run Similarity Analysis",  
> **Then** the system returns an Earth Engine tile layer / heatmap overlay displaying similarity scores from 0.0 to 1.0 within 15 seconds for a city-scale region.

---

### US-03: Ranked Match Retrieval & Threshold Filtering
**As a** planner,  
**I want to** specify a similarity threshold or a top-N limit,  
**So that I can** inspect a ranked list of candidate locations meeting my matching criteria.

> **Scenario: Filtering top matches by threshold**  
> **Given** computed similarity scores across an AOI,  
> **When** the user sets a threshold slider to 0.85 and requests the top 10 matches,  
> **Then** the map highlights the top 10 discrete candidate locations and displays a ranked table showing coordinates and match scores.

---

### US-04: Multi-Temporal Comparison (Stretch)
**As an** environmental scientist,  
**I want to** compare similarity scores across different years (2017–2024),  
**So that I can** observe whether a candidate location has maintained or deviated from its resemblance to the reference over time.

> **Scenario: Temporal trajectory evaluation**  
> **Given** a reference site from 2018 and a candidate location,  
> **When** the user requests a multi-year similarity trajectory,  
> **Then** the system plots annual similarity scores from 2018 through 2024.

---

## 6. Functional Requirements

| ID | Category | Requirement Description |
| :--- | :--- | :--- |
| **FR-001** | Data Acquisition | The system shall query and filter the Earth Engine ImageCollection `GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL` by year (2017–2024) and geographic bounds. |
| **FR-002** | Preprocessing & Mosaicking | The system shall handle spatial clipping and tile mosaicking for study areas exceeding a single tile footprint (~163.8 km × 163.8 km) without data loss. |
| **FR-003** | Vector Extraction | The system shall extract the 64-band (`A00`–`A63`) embedding vector for any designated coordinate within the dataset coverage. |
| **FR-004** | Region Aggregation | The system shall aggregate multi-pixel reference regions (patches or polygons) into a single 64-dimensional vector using spatial mean pooling. |
| **FR-005** | Similarity Computation | The system shall compute the dot product / cosine similarity between the reference vector and all candidate pixels in the AOI natively within Earth Engine. |
| **FR-006** | Score Normalization & Masking | The system shall clamp or scale similarity values to [0.0, 1.0] and mask out invalid or nodata areas. |
| **FR-007** | Match Extraction & Ranking | The system shall extract top-N candidate locations meeting user-defined similarity thresholds and return ordered geographic coordinates with scores. |
| **FR-008** | Spatial Pattern Clustering | The system shall optionally cluster candidate embedding vectors within the study area using k-means or equivalent algorithms to identify recurring land classes. |
| **FR-009** | Interactive Map Web Interface | The system shall provide a browser-based user interface supporting pan/zoom, coordinate picking, polygon drawing, parameter configuration, and layer toggles. |
| **FR-010** | Heatmap Overlay | The system shall render similarity heatmaps as interactive map tile layers directly over standard base maps. |
| **FR-011** | Results Export | The system shall provide an option to download ranked match coordinates and similarity metrics in JSON or CSV format. |

---

## 7. Success Metrics
- **Response Latency:** For a standard city-scale AOI (~500 km²), similarity heatmap tiles and top-10 candidate extraction must return in under 15 seconds.
- **Geospatial Consistency:** Known homogeneous surface types (e.g., deep water reservoirs vs. dense forest canopies) must exhibit clear bimodal separation in similarity score distribution (>0.90 within class, <0.30 across discordant classes).
- **Compute Efficiency:** Normal demonstration and testing sessions must stay well within the monthly 150 EECU-hour Community tier quota without triggering throttling.
- **System Stability:** Zero server crashes caused by unhandled GEE quota or authentication timeout exceptions.

---

## 8. Resolved Domain Specifications (Formerly Open Questions)

The initial gaps in the source FYP proposal have been resolved as follows:

1. **Benchmark Study AOI & Default Target Year:**
   - **Canonical Region:** Islamabad/Rawalpindi Twin-Cities Metropolitan & Peri-Urban Region (Pakistan).
   - **Characteristics:** Compact, diverse zone encompassing dense unplanned urban fabric, planned urban grid, urban greenery, protected sub-Himalayan forest canopy (Margalla Hills), major water bodies (Rawal Lake, Simly catchment), and rainfed agricultural parcels.
   - **Bounding Box (WGS84 `[min_lon, min_lat, max_lon, max_lat]`):** `[72.80, 33.45, 73.25, 33.82]`
   - **Bounding Polygon (GeoJSON format):**
     ```json
     {
       "type": "Polygon",
       "coordinates": [[
         [72.80, 33.45],
         [73.25, 33.45],
         [73.25, 33.82],
         [72.80, 33.82],
         [72.80, 33.45]
       ]]
     }
     ```
   - **Spatial Extent:** ~41 km (N-S) × 42 km (E-W) ≈ 1,720 km².
   - **Benchmark Calendar Year:** `2023` (most recent complete cloud-free annual embedding composite).

2. **Scope of Clustering and Database Persistence:**
   - Spatial clustering (FR-008, `ee.Clusterer`) and database session persistence (SQLite) are formally **deferred to Phase 4 (Extensions & Stretch Goals)** per the original proposal's optional designation.
   - Phases 1 through 3 target strictly the core similarity extraction/search engine, interactive web UI, and empirical validation.

3. **Milestone Deliverable Target:**
   - **Current Target:** **Phase 1 (Working CLI / Python Core Pipeline)**. Produces a verifiable command-line runner and modules (`src/core/`) that take coordinates/AOI, execute Earth Engine vector dot products, and output ranked candidate coordinates with map tile IDs.

4. **Concrete Validation Case Studies:**
   - **Case Study A (Agricultural Lands):** Reference parcel in Potohar plateau / Chak Shahzad rainfed cropland (`[73.140, 33.670]`) evaluated for retrieval across the Potohar agricultural belt vs. urban and barren land.
   - **Case Study B (Water Body Delineation):** Deep water reference point in Rawal Lake (`[73.123, 33.702]`) evaluated against Simly Dam, river beds, and terrestrial land covers.
   - **Case Study C (Urban Greenery vs. Natural Forest):** Reference canopy in Islamabad urban park (Fatima Jinnah Park, `[73.018, 33.704]`) evaluated against dense Margalla Hills natural reserve (`[73.060, 33.750]`) and surrounding built-up sectors.

