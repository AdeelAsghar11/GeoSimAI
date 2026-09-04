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
