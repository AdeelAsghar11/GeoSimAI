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

## 8. Open Questions & Clarifications Needed

> [!IMPORTANT]
> The following items are gaps in the source FYP proposal that must be resolved with project supervisors before or during Phase 1 execution:

1. **[NEEDS CLARIFICATION: Default Study AOI & Target Year]**
   What specific geographic region(s) (e.g., Islamabad/Rawalpindi district, Indus Basin agricultural sector, or a specific forest reserve) and default calendar year should be established as the canonical benchmark demo for the project?
2. **[NEEDS CLARIFICATION: Scope of Clustering and Database Persistence]**
   Are spatial clustering (FR-008) and persistent user session databases (SQLite/PostgreSQL) strictly committed deliverables for the core FYP evaluation, or are they formally designated as stretch goals to be tackled only after the core similarity workflow is validated?
3. **[NEEDS CLARIFICATION: Definition of "Done" for Current Milestone]**
   What is the specific milestone deliverable expected for the upcoming evaluation committee: a finalized proposal and technical specification, a working local CLI/notebook prototype, or a fully deployed live web demonstration?
4. **[NEEDS CLARIFICATION: Concrete Validation Case Studies]**
   Which 2 to 3 concrete ground-truth scenarios will anchor the formal validation chapter? (e.g., Case Study 1: Agricultural crop field retrieval; Case Study 2: Water body / reservoir delineation; Case Study 3: Urban vs. peri-urban vegetation contrast).
