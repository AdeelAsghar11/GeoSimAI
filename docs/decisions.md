# Decisions Log — GeoSimAI

Lightweight Architectural Decision Records (ADRs). Document each non-trivial technical, architectural, or product choice as it is made. Do not modify or delete historical decisions without appending an explicit superseding record.

---

## 2026-09-04: Region Aggregation Method

- **Decision:** Use spatial mean pooling across pixel embedding vectors to create a single representative 64-D vector for polygon or patch reference regions.
- **Why:** The AlphaEarth Foundations satellite embedding dataset (`GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL`) is explicitly designed and documented as linearly composable. Linear averaging preserves angular and distance relationships in the latent space, making mean pooling the mathematically intended approach rather than a heuristic workaround.
- **Alternatives considered:**
  - *Medoid / Centroid Pixel Selection:* Discards spatial heterogeneity within the polygon.
  - *Concatenation / Multi-Vector Set Matching:* Significantly increases query computation overhead and breaks compatibility with single-raster dot-product operations in Earth Engine.

---

## 2026-09-04: Similarity Metric Selection

- **Decision:** Use vector dot product directly within Google Earth Engine to compute similarity between reference and candidate pixels.
- **Why:** The embedding vectors in the AlphaEarth dataset are normalized unit-length vectors ($\|\mathbf{v}\| = 1$, values bounded strictly between -1.0 and +1.0). For unit vectors, the cosine similarity $\frac{\mathbf{u} \cdot \mathbf{v}}{\|\mathbf{u}\|\|\mathbf{v}\|}$ is algebraically identical to the dot product $\mathbf{u} \cdot \mathbf{v}$. Computing the dot product via band multiplication and summation in Earth Engine is highly optimized, hardware-accelerated, and requires zero client-side data transfer.
- **Alternatives considered:**
  - *Euclidean Distance ($L_2$ norm):* Monotonically related to cosine distance for unit vectors ($d^2 = 2 - 2 \cos \theta$), but requires additional square root and subtractive operations without yielding different rankings.
  - *Client-Side Cosine Similarity:* Infeasible for real-time interaction as it would require downloading millions of 64-band pixels over the network.

---

## 2026-09-04: Backend Framework Selection

- **Decision:** Use Python Flask for the backend web service.
- **Why:** Flask is lightweight, has minimal boilerplate, integrates smoothly with the Earth Engine Python API and scientific Python libraries (NumPy, Scikit-learn), and runs cleanly within free serverless tiers (Cloud Run, Render).
- **Alternatives considered:**
  - *Django:* Offers a rich ORM and admin interface, but introduces substantial overhead, unnecessary boilerplate, and heavier resource footprints for an application whose primary database needs are minimal.
  - *FastAPI:* Excellent for async REST APIs, but the official Earth Engine Python client (`earthengine-api`) is synchronous, eliminating many of FastAPI's async I/O advantages while adding minor typing complexity.

---

## 2026-09-04: Persistence and Database Selection

- **Decision:** Use SQLite as the default local database for storing user sessions, bookmarked queries, and metadata.
- **Why:** SQLite requires zero server daemon setup, zero hosting costs, produces a single portable `.db` file, and effortlessly handles the read/write load of an academic FYP demo.
- **Alternatives considered:**
  - *PostgreSQL / MySQL:* Recommended in the FYP proposal as an option, but adds operational complexity, connection string management, and hosting costs. May be introduced via a free hosted provider (Supabase/Neon) only if multi-user concurrency demands it later.

---

## 2026-09-04: Earth Engine Quota Tier Selection

- **Decision:** Register the project under the noncommercial Google Earth Engine **Community Tier** (150 EECU-hours per month).
- **Why:** Google explicitly recommends the Community tier for noncommercial undergraduate and academic research projects. It provides 150 EECU-hours/month of compute for free. Exceeding the quota does not cut off access or incur financial charges; it simply routes jobs into a slower throttled queue until the monthly reset.
- **Alternatives considered:**
  - *Commercial / Paid Cloud Billing Account:* Unnecessary financial cost for an academic FYP project.
  - *Unregistered Legacy Project:* Deprecated; all noncommercial projects must belong to a registered tier since April 2026.

---

## 2026-09-04: Deployment Authentication Strategy

- **Decision:** Implement Google Cloud Application Default Credentials (ADC) with a Service Account for server deployments.
- **Why:** The interactive `earthengine authenticate` flow requires an interactive human browser session and local token cache, making it completely incompatible with headless cloud hosting (Render, Cloud Run). Service Account credentials loaded via `google.auth.default()` allow fully unattended server initialization.
- **Alternatives considered:**
  - *Hardcoded Refresh Tokens:* Fragile, security risk if committed, prone to expiration.

---

## 2026-09-04: Cloud Hosting Platform

- **Decision:** Target Google Cloud Run or Render free tier for online deployment.
- **Why:** Both platforms support standard Docker containerization or Python runtime, include free tier allocations, and crucially permit unrestricted outbound HTTPS calls to Google Earth Engine APIs (`*.googleapis.com`).
- **Alternatives considered:**
  - *PythonAnywhere:* PythonAnywhere's free tier restricts outbound HTTP traffic to an explicit whitelist of domains. Unless Google Earth Engine API endpoints are verified on the whitelist, it risks network failures during server initialization.

---

## 2026-09-08: Relocation of Benchmark Demo AOI to Muzaffarabad

- **Decision:** Shift canonical demonstration and evaluation Area of Interest from Islamabad-Rawalpindi to Muzaffarabad, Azad Kashmir (`[73.42, 34.32, 73.60, 34.42]`, ~183 km²).
- **Why:** Muzaffarabad sits at the confluence of the Jhelum and Neelum rivers in a steep valley basin receiving ~1,800 mm/year of precipitation. The mountainous topography produces steep microclimate and land-cover gradients (deep river confluence, dense river-basin urban grid, terraced slopes, and high-altitude alpine coniferous forests at Pir Chinasi ~2,900m) over a much smaller spatial footprint (183 km² vs. 1,720 km²). This enhances computational speed within EECU limits while offering rich, hydrologically authentic similarity matching.
- **Alternatives considered:**
  - *Retaining Islamabad-Rawalpindi:* Valid plains/foothills basin, but spans 1,720 km² with wider sampling overhead and less extreme topographical diversity per unit area.
  - *Swat or Gilgit Valley:* High land cover diversity, but lower urban density and less readily accessible ground-truth reference points.

---

## 2026-09-08: Sourcing Visual Verification Crops from Sentinel-2 Rather than Embeddings

- **Decision:** Generate side-by-side optical satellite thumbnails from `COPERNICUS/S2_SR_HARMONIZED` (Sentinel-2 Harmonized Surface Reflectance) rather than attempting to render the AlphaEarth embedding directly.
- **Why:** The AlphaEarth Foundations embedding (`GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL`) consists of 64 learned latent dimensions (`A00`–`A63`). They are dimensionless mathematical vectors, not photographic or multispectral bands. Per `AGENTS.md` Principle #1, embedding dimensions must never be treated as physical pseudo-bands. Sentinel-2 true-color optical imagery (B4, B3, B2) provides genuine, verifiable photographic crops that human evaluators can cross-check with their own eyes.
- **Alternatives considered:**
  - *PCA/t-SNE RGB Projection of Latent Bands:* Creates aesthetically interesting false-color maps, but produces non-intuitive colors that do not resemble optical reality and risks confusing human judges.
  - *Landsat 8/9:* Offers true-color imagery, but at 30m resolution compared to Sentinel-2's sharper 10m native spatial resolution.

---

## 2026-09-08: Deterministic Rule-Based Plain-Language Descriptions Over LLM Generation

- **Decision:** Generate one-line plain-language similarity descriptions ("Both areas exhibit comparable vegetation density and similar built-up density") using deterministic thresholds over independent Sentinel-2 optical spectral indices (NDVI, NDBI, NDMI) rather than an LLM text generator.
- **Why:** 
  1. *Scientific Integrity:* Asking an LLM to narrate AlphaEarth embeddings directly violates Principle #1 by prompting hallucinated physical claims from latent dimensions. Computing real optical indices provides genuine, verifiable physical backing.
  2. *Deterministic Reliability:* Rule-based composition never hallucinates, never fails at demo time due to LLM provider outages, and incurs zero API cost and zero inference latency.
  3. *Verification:* An evaluator can inspect the exact delta values ($\Delta \text{NDVI} \le 0.12$) confirming why a trait was designated as similar.
- **Alternatives considered:**
  - *LLM Prompt Over Embedding Vectors:* Hallucinates physical variables from abstract latent numbers; violates core project principles.
  - *Small LLM Summarizer Over Computed Optical Indices:* Feasible as a future enhancement, but adds API dependencies and non-zero latency without altering the underlying physical facts.
