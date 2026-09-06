/**
 * GeoSimAI — Frontend Application Logic
 * Interactive Leaflet Map & Earth Engine Similarity Search & Clustering Client
 */

// Benchmark AOI bounds [min_lon, min_lat, max_lon, max_lat]
const AOI_BOUNDS = [72.80, 33.45, 73.25, 33.82];

// Preset Validation Case Studies
const CASE_STUDIES = {
  B_WATER: {
    name: 'Rawal Lake Deep Water',
    coords: [73.123, 33.702],
    desc: 'Deep freshwater reservoir vs. dry land/vegetation'
  },
  C_VEGETATION: {
    name: 'Fatima Jinnah Park (Islamabad Urban Greenery)',
    coords: [73.018, 33.704],
    desc: 'Urban park canopy vs. Margalla forest reserve and built-up grid'
  },
  A_AGRICULTURE: {
    name: 'Potohar Plateau Cropland (Chak Shahzad)',
    coords: [73.140, 33.670],
    desc: 'Rainfed agricultural parcel vs. urban/barren land'
  }
};

// Application State
const state = {
  currentRef: { lon: 73.018, lat: 33.704, label: 'Fatima Jinnah Park Urban Canopy' },
  year: 2023,
  threshold: 0.75,
  topN: 10,
  opacity: 0.85,
  clusterK: 5,
  clusterOpacity: 0.75,
  isPicking: false,
  lastResult: null
};

// Map & Layer References
let map;
let baseLayers = {};
let currentBaseLayer;
let aoiRectangle;
let refMarkerLayer;
let heatmapLayer = null;
let clusteringLayer = null;
let matchMarkersLayer;

document.addEventListener('DOMContentLoaded', () => {
  initMap();
  initEventListeners();
  checkBackendHealth();
  updateRefMarker();
  loadBookmarks();
  loadHistory();
});

/**
 * Initialize Leaflet Map and Base Layers
 */
function initMap() {
  // Center over Islamabad-Rawalpindi
  map = L.map('map', {
    center: [33.65, 73.05],
    zoom: 11,
    zoomControl: false
  });

  L.control.zoom({ position: 'bottomright' }).addTo(map);

  // Satellite Base Layer (Esri World Imagery)
  baseLayers.satellite = L.tileLayer(
    'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    {
      attribution: 'Esri, Maxar, Earthstar Geographics',
      maxZoom: 18
    }
  );

  // Dark Base Layer (CartoDB Dark Matter)
  baseLayers.dark = L.tileLayer(
    'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
    {
      attribution: '&copy; OpenStreetMap, &copy; CartoDB',
      maxZoom: 19
    }
  );

  // Default to satellite
  currentBaseLayer = baseLayers.satellite;
  currentBaseLayer.addTo(map);

  // AOI Bounding Rectangle Overlay
  const aoiLeafletBounds = [
    [AOI_BOUNDS[1], AOI_BOUNDS[0]], // [south, west]
    [AOI_BOUNDS[3], AOI_BOUNDS[2]]  // [north, east]
  ];

  aoiRectangle = L.rectangle(aoiLeafletBounds, {
    color: '#38bdf8',
    weight: 2,
    dashArray: '6, 6',
    fillColor: '#38bdf8',
    fillOpacity: 0.04
  }).addTo(map);

  aoiRectangle.bindTooltip('Islamabad-Rawalpindi Benchmark AOI (1,720 km²)', {
    permanent: false,
    direction: 'top'
  });

  // Layer groups for markers
  refMarkerLayer = L.layerGroup().addTo(map);
  matchMarkersLayer = L.layerGroup().addTo(map);

  // Map Click Listener for "Pick Point" mode
  map.on('click', (e) => {
    if (state.isPicking) {
      setReferencePoint(e.latlng.lng, e.latlng.lat, 'Custom Clicked Location');
      disablePickingMode();
    }
  });
}

/**
 * Update Reference Point Marker
 */
function updateRefMarker() {
  refMarkerLayer.clearLayers();

  const icon = L.divIcon({
    className: 'ref-marker-pin',
    iconSize: [24, 24],
    iconAnchor: [12, 12]
  });

  const marker = L.marker([state.currentRef.lat, state.currentRef.lon], { icon })
    .bindPopup(`<strong>Reference Location</strong><br>${state.currentRef.label}<br>(${state.currentRef.lat.toFixed(6)}, ${state.currentRef.lon.toFixed(6)})`)
    .addTo(refMarkerLayer);

  // Update Sidebar Displays
  document.getElementById('displayLat').textContent = state.currentRef.lat.toFixed(6);
  document.getElementById('displayLon').textContent = state.currentRef.lon.toFixed(6);
  document.getElementById('selectionStatus').textContent = `Active: ${state.currentRef.label}`;
}

/**
 * Set Reference Point from Coordinates
 */
function setReferencePoint(lon, lat, label) {
  state.currentRef = {
    lon: parseFloat(lon),
    lat: parseFloat(lat),
    label: label
  };
  updateRefMarker();
  map.panTo([lat, lon]);
}

/**
 * Enable/Disable Map Coordinate Picking Mode
 */
function togglePickingMode() {
  if (state.isPicking) {
    disablePickingMode();
  } else {
    state.isPicking = true;
    const btn = document.getElementById('btnPickPoint');
    btn.classList.add('active');
    btn.innerHTML = `<span style="color:#f43f5e">●</span> Click Map`;
    map.getContainer().style.cursor = 'crosshair';
  }
}

function disablePickingMode() {
  state.isPicking = false;
  const btn = document.getElementById('btnPickPoint');
  btn.classList.remove('active');
  btn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg> Click Map`;
  map.getContainer().style.cursor = '';
}

/**
 * Event Listeners Setup
 */
function initEventListeners() {
  // Navigation Tabs Switching
  document.querySelectorAll('.tab-btn').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.tab-btn').forEach(t => t.classList.remove('active'));
      document.querySelectorAll('.tab-pane').forEach(p => p.style.display = 'none');

      tab.classList.add('active');
      const paneId = tab.getAttribute('data-pane');
      const targetPane = document.getElementById(paneId);
      if (targetPane) targetPane.style.display = 'block';

      if (paneId === 'paneBookmarks') {
        loadBookmarks();
        loadHistory();
      }
    });
  });

  // Preset buttons
  document.querySelectorAll('.preset-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.preset-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const caseKey = btn.getAttribute('data-case');
      const study = CASE_STUDIES[caseKey];
      if (study) {
        setReferencePoint(study.coords[0], study.coords[1], study.name);
      }
    });
  });

  // Pick on Map Button
  document.getElementById('btnPickPoint').addEventListener('click', togglePickingMode);

  // Bookmark current location button
  document.getElementById('btnBookmarkCurrent').addEventListener('click', () => {
    const name = prompt('Enter a name for this bookmark:', state.currentRef.label);
    if (name) {
      saveBookmark(name, state.currentRef.lon, state.currentRef.lat);
    }
  });

  // Year select
  document.getElementById('yearSelect').addEventListener('change', (e) => {
    state.year = parseInt(e.target.value);
  });

  // Threshold slider
  const slider = document.getElementById('thresholdSlider');
  const badge = document.getElementById('thresholdVal');
  const legendMin = document.getElementById('legendMin');

  slider.addEventListener('input', (e) => {
    state.threshold = parseFloat(e.target.value);
    badge.textContent = `≥ ${state.threshold.toFixed(2)}`;
    if (legendMin) legendMin.textContent = state.threshold.toFixed(2);
  });

  // Top N select
  document.getElementById('topNSelect').addEventListener('change', (e) => {
    state.topN = parseInt(e.target.value);
  });

  // CTA Execute Similarity Button
  document.getElementById('btnRunSimilarity').addEventListener('click', executeSimilaritySearch);

  // Heatmap visibility toggle
  document.getElementById('toggleHeatmap').addEventListener('change', (e) => {
    if (heatmapLayer) {
      if (e.target.checked) {
        map.addLayer(heatmapLayer);
      } else {
        map.removeLayer(heatmapLayer);
      }
    }
  });

  // Heatmap opacity slider
  document.getElementById('opacitySlider').addEventListener('input', (e) => {
    state.opacity = parseInt(e.target.value) / 100;
    document.getElementById('opacityVal').textContent = `${e.target.value}%`;
    if (heatmapLayer) {
      heatmapLayer.setOpacity(state.opacity);
    }
  });

  // Cluster k selector
  document.getElementById('clusterKSelect').addEventListener('change', (e) => {
    state.clusterK = parseInt(e.target.value);
  });

  // CTA Execute Clustering Button
  document.getElementById('btnRunClustering').addEventListener('click', executeClustering);

  // Cluster layer visibility toggle
  document.getElementById('toggleClusterLayer').addEventListener('change', (e) => {
    if (clusteringLayer) {
      if (e.target.checked) {
        map.addLayer(clusteringLayer);
      } else {
        map.removeLayer(clusteringLayer);
      }
    }
  });

  // Cluster opacity slider
  document.getElementById('clusterOpacitySlider').addEventListener('input', (e) => {
    state.clusterOpacity = parseInt(e.target.value) / 100;
    document.getElementById('clusterOpacityVal').textContent = `${e.target.value}%`;
    if (clusteringLayer) {
      clusteringLayer.setOpacity(state.clusterOpacity);
    }
  });

  // Reset View to AOI
  document.getElementById('btnResetView').addEventListener('click', () => {
    map.fitBounds(aoiRectangle.getBounds(), { padding: [30, 30] });
  });

  // Basemap Switchers
  document.getElementById('btnBaseSatellite').addEventListener('click', () => {
    document.getElementById('btnBaseSatellite').classList.add('active');
    document.getElementById('btnBaseDark').classList.remove('active');
    map.removeLayer(currentBaseLayer);
    currentBaseLayer = baseLayers.satellite;
    map.addLayer(currentBaseLayer);
  });

  document.getElementById('btnBaseDark').addEventListener('click', () => {
    document.getElementById('btnBaseDark').classList.add('active');
    document.getElementById('btnBaseSatellite').classList.remove('active');
    map.removeLayer(currentBaseLayer);
    currentBaseLayer = baseLayers.dark;
    map.addLayer(currentBaseLayer);
  });

  // JSON Export Button
  document.getElementById('btnExportJson').addEventListener('click', exportResultsJson);
}

/**
 * Execute Similarity Query against Flask Backend
 */
async function executeSimilaritySearch() {
  showLoading(true, 'Computing In-Engine Dot Product...', 'Evaluating 64-D AlphaEarth embeddings over AOI...');

  const payload = {
    lon: state.currentRef.lon,
    lat: state.currentRef.lat,
    year: state.year,
    threshold: state.threshold,
    top_n: state.topN,
    label: state.currentRef.label,
    aoi: AOI_BOUNDS
  };

  try {
    const res = await fetch('/api/similarity', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const data = await res.json();

    if (!res.ok || !data.success) {
      throw new Error(data.error || 'Server-side similarity computation failed');
    }

    state.lastResult = data;
    renderResults(data);

  } catch (err) {
    alert(`Error running similarity search:\n${err.message}`);
  } finally {
    showLoading(false);
  }
}

/**
 * Render Heatmap Tile Layer and Ranked Matches
 */
function renderResults(data) {
  // 1. Remove prior heatmap
  if (heatmapLayer) {
    map.removeLayer(heatmapLayer);
  }

  // 2. Add Earth Engine XYZ Tile Layer
  if (data.tile_url) {
    heatmapLayer = L.tileLayer(data.tile_url, {
      opacity: state.opacity,
      maxZoom: 18
    });

    const toggle = document.getElementById('toggleHeatmap');
    if (toggle.checked) {
      heatmapLayer.addTo(map);
    }

    document.getElementById('layerControlSection').style.display = 'flex';
  }

  // 3. Render Match Markers
  matchMarkersLayer.clearLayers();

  const matches = data.matches || [];
  matches.forEach(m => {
    const icon = L.divIcon({
      className: 'match-marker-pin',
      html: `<span>${m.rank}</span>`,
      iconSize: [22, 22],
      iconAnchor: [11, 11]
    });

    const marker = L.marker([m.lat, m.lon], { icon })
      .bindPopup(`
        <strong>Rank #${m.rank}</strong><br>
        <strong>Similarity:</strong> ${(m.score * 100).toFixed(1)}% (${m.score})<br>
        <strong>Coords:</strong> ${m.lat.toFixed(6)}, ${m.lon.toFixed(6)}
      `);

    matchMarkersLayer.addLayer(marker);
  });

  // 4. Populate Ranked Results Sidebar
  const resultsContainer = document.getElementById('resultsList');
  if (matches.length === 0) {
    resultsContainer.innerHTML = `<div class="placeholder-state"><p>No candidates exceeded similarity threshold &tau; ≥ ${data.threshold}. Try lowering threshold.</p></div>`;
    document.getElementById('btnExportJson').style.display = 'none';
    return;
  }

  document.getElementById('btnExportJson').style.display = 'flex';

  resultsContainer.innerHTML = matches.map(m => `
    <div class="result-card" onclick="zoomToMatch(${m.lat}, ${m.lon})">
      <div class="result-rank">#${m.rank}</div>
      <div class="result-coords">
        <span>${m.lat.toFixed(5)}° N</span>
        <span>${m.lon.toFixed(5)}° E</span>
      </div>
      <div class="result-score-pill">${(m.score * 100).toFixed(1)}%</div>
    </div>
  `).join('');
}

/**
 * Execute Spatial K-Means Clustering
 */
async function executeClustering() {
  showLoading(true, 'Training Server-Side K-Means Clusterer...', `Partitioning 64-D embedding space into ${state.clusterK} environmental biomes...`);

  try {
    const res = await fetch('/api/cluster', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        year: state.year,
        n_clusters: state.clusterK,
        aoi: AOI_BOUNDS
      })
    });

    const data = await res.json();
    if (!res.ok || !data.success) {
      throw new Error(data.error || 'Clustering execution failed');
    }

    // 1. Remove previous clustering layer
    if (clusteringLayer) {
      map.removeLayer(clusteringLayer);
    }

    // 2. Add new clustering tile layer
    clusteringLayer = L.tileLayer(data.tile_url, {
      opacity: state.clusterOpacity,
      maxZoom: 18
    });

    const toggle = document.getElementById('toggleClusterLayer');
    if (toggle.checked) {
      clusteringLayer.addTo(map);
    }

    // 3. Show controls and populate legend
    document.getElementById('clusterControlsSection').style.display = 'flex';
    const legendContainer = document.getElementById('clusterLegendList');
    legendContainer.innerHTML = data.palette.map((color, idx) => `
      <div class="cluster-legend-item">
        <span class="cluster-color-badge" style="background: ${color}"></span>
        <span>Cluster #${idx}</span>
      </div>
    `).join('');

  } catch (err) {
    alert(`Clustering Error:\n${err.message}`);
  } finally {
    showLoading(false);
  }
}

/**
 * Load and Render Bookmarks
 */
async function loadBookmarks() {
  const container = document.getElementById('bookmarksList');
  try {
    const res = await fetch('/api/bookmarks');
    const data = await res.json();
    if (!data.success || !data.bookmarks.length) {
      container.innerHTML = '<div class="placeholder-state"><p>No saved bookmarks found.</p></div>';
      return;
    }

    container.innerHTML = data.bookmarks.map(b => `
      <div class="bookmark-card" onclick="selectBookmark(${b.lon}, ${b.lat}, '${escapeQuotes(b.name)}')">
        <div class="bookmark-header">
          <span class="bookmark-name">${b.name}</span>
          <span class="bookmark-category">${b.category || 'Site'}</span>
          <button class="btn-delete-bookmark" onclick="event.stopPropagation(); removeBookmark(${b.id})">✕</button>
        </div>
        <p class="bookmark-desc">${b.description || `(${b.lat.toFixed(4)}, ${b.lon.toFixed(4)})`}</p>
      </div>
    `).join('');
  } catch {
    container.innerHTML = '<div class="placeholder-state"><p>Failed to load bookmarks.</p></div>';
  }
}

/**
 * Save Current Coordinates as Bookmark
 */
async function saveBookmark(name, lon, lat) {
  try {
    const res = await fetch('/api/bookmarks', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, lon, lat, category: 'Custom' })
    });
    const data = await res.json();
    if (data.success) {
      alert(`Bookmark "${name}" saved!`);
      loadBookmarks();
    }
  } catch (err) {
    alert(`Failed to save bookmark: ${err.message}`);
  }
}

/**
 * Remove Bookmark
 */
window.removeBookmark = async function(id) {
  if (!confirm('Delete this bookmark?')) return;
  try {
    const res = await fetch(`/api/bookmarks/${id}`, { method: 'DELETE' });
    const data = await res.json();
    if (data.success) {
      loadBookmarks();
    }
  } catch (err) {
    alert(`Failed to delete bookmark: ${err.message}`);
  }
};

/**
 * Select Bookmark
 */
window.selectBookmark = function(lon, lat, name) {
  setReferencePoint(lon, lat, name);
  // Switch to similarity tab
  document.getElementById('tabSimilarity').click();
};

/**
 * Load and Render Query History
 */
async function loadHistory() {
  const container = document.getElementById('historyList');
  try {
    const res = await fetch('/api/history?limit=15');
    const data = await res.json();
    if (!data.success || !data.history.length) {
      container.innerHTML = '<div class="placeholder-state"><p>No recent queries.</p></div>';
      return;
    }

    container.innerHTML = data.history.map(h => `
      <div class="history-card" onclick="selectBookmark(${h.lon}, ${h.lat}, '${escapeQuotes(h.label || 'History Item')}')">
        <div class="history-header">
          <strong style="font-size:0.8rem; color:var(--text-primary)">${h.label || 'Search'}</strong>
          <span style="font-size:0.72rem; color:var(--accent-emerald)">${h.match_count} matches</span>
        </div>
        <div class="history-meta">
          <span>Year: ${h.year} &bull; &tau; &ge; ${h.threshold} &bull; Top Score: ${h.top_score ? (h.top_score * 100).toFixed(1) + '%' : 'N/A'}</span>
        </div>
      </div>
    `).join('');
  } catch {
    container.innerHTML = '<div class="placeholder-state"><p>Failed to load history.</p></div>';
  }
}

function escapeQuotes(str) {
  return str.replace(/'/g, "\\'");
}

/**
 * Zoom map to candidate match
 */
window.zoomToMatch = function(lat, lon) {
  map.flyTo([lat, lon], 14, { duration: 1.2 });
};

/**
 * Export results as JSON
 */
function exportResultsJson() {
  if (!state.lastResult) return;
  const blob = new Blob([JSON.stringify(state.lastResult, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `geosim_results_${state.year}_thresh${state.threshold}.json`;
  a.click();
  URL.revokeObjectURL(url);
}

/**
 * Backend Health Check
 */
async function checkBackendHealth() {
  try {
    const res = await fetch('/api/health');
    const data = await res.json();
    const badge = document.getElementById('statusBadge');
    if (data.ee_initialized) {
      badge.className = 'status-indicator online';
      badge.innerHTML = '<span class="status-dot"></span> GEE Ready';
    } else {
      badge.className = 'status-indicator';
      badge.style.color = '#f59e0b';
      badge.innerHTML = '<span class="status-dot" style="background:#f59e0b"></span> GEE Pending';
    }
  } catch {
    const badge = document.getElementById('statusBadge');
    badge.className = 'status-indicator';
    badge.style.color = '#ef4444';
    badge.innerHTML = '<span class="status-dot" style="background:#ef4444"></span> Offline';
  }
}

/**
 * Show / Hide Loading Overlay
 */
function showLoading(show, title = '', msg = '') {
  const overlay = document.getElementById('loadingOverlay');
  if (show) {
    if (title) document.getElementById('loadingTitle').textContent = title;
    if (msg) document.getElementById('loadingMsg').textContent = msg;
    overlay.style.display = 'flex';
  } else {
    overlay.style.display = 'none';
  }
}
