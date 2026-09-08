/**
 * GeoSimAI — Latent Spectrum Application Logic
 * 64-D Foundation Satellite Embedding Similarity Search & Landscape Clustering
 */

// Benchmark AOI bounds [min_lon, min_lat, max_lon, max_lat]
const AOI_BOUNDS = [73.42, 34.32, 73.60, 34.42];

// Preset Validation Case Studies
const CASE_STUDIES = {
  A_RIVER: {
    name: 'Domel River Confluence',
    coords: [73.465, 34.383],
    desc: 'Confluence of Neelum and Jhelum rivers vs. surrounding terrain'
  },
  B_URBAN: {
    name: 'Muzaffarabad City Core',
    coords: [73.472, 34.358],
    desc: 'Dense valley urban fabric and commercial core'
  },
  C_FOREST: {
    name: 'Pir Chinasi Alpine Forest',
    coords: [73.550, 34.389],
    desc: 'High-altitude coniferous forest and green ridgeline plateau (~2,900m)'
  }
};

// Application State
const state = {
  currentRef: { lon: 73.465, lat: 34.383, label: 'Domel River Confluence' },
  year: 2023,
  threshold: 0.75,
  topN: 10,
  opacity: 0.85,
  clusterK: 5,
  clusterOpacity: 0.75,
  isPicking: false,
  mapMode: 'field', // 'field' or 'satellite'
  lastResult: null
};

// Map & Layer References
let map;
let satelliteTileLayer;
let aoiRectangle;
let refMarkerLayer;
let matchMarkersLayer;
let connectorLinesLayer;
let heatmapLayer = null;
let clusteringLayer = null;

// Registry of rendered polyline connector lines and match markers for hover highlights
let connectorLines = [];
let matchMarkers = [];

document.addEventListener('DOMContentLoaded', () => {
  initMap();
  initEventListeners();
  checkBackendHealth();
  updateRefMarker();
  loadBookmarks();
  loadHistory();
});

/**
 * Initialize Leaflet Map with Field View and Satellite View
 */
function initMap() {
  // Centered on Muzaffarabad Valley
  map = L.map('map', {
    center: [34.37, 73.48],
    zoom: 12,
    zoomControl: false,
    attributionControl: false
  });

  // Custom styled zoom control bottom-right
  L.control.zoom({ position: 'bottomright' }).addTo(map);

  // Esri World Imagery (Satellite)
  satelliteTileLayer = L.tileLayer(
    'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    {
      attribution: 'Esri, Maxar, Earthstar Geographics',
      maxZoom: 18
    }
  );

  // In Field view by default, satellite tiles are NOT added; ambient canvas gradient shows
  if (state.mapMode === 'satellite') {
    satelliteTileLayer.addTo(map);
  }

  // AOI Bounding Box (Latent Spectrum theme: violet line + subtle glow)
  const aoiLeafletBounds = [
    [AOI_BOUNDS[1], AOI_BOUNDS[0]], // [south, west]
    [AOI_BOUNDS[3], AOI_BOUNDS[2]]  // [north, east]
  ];

  aoiRectangle = L.rectangle(aoiLeafletBounds, {
    color: '#a58bff',
    weight: 1.5,
    dashArray: '5, 5',
    fillColor: '#a58bff',
    fillOpacity: 0.035
  }).addTo(map);

  aoiRectangle.bindTooltip('Muzaffarabad Latent Field (183 km²)', {
    permanent: false,
    direction: 'top',
    className: 'aoi-tooltip'
  });

  // Layer groups for dynamic geographic features
  connectorLinesLayer = L.layerGroup().addTo(map);
  refMarkerLayer = L.layerGroup().addTo(map);
  matchMarkersLayer = L.layerGroup().addTo(map);

  // Map Click Listener for picking mode
  map.on('click', (e) => {
    if (state.isPicking) {
      setReferencePoint(e.latlng.lng, e.latlng.lat, `Custom Site (${e.latlng.lat.toFixed(4)}, ${e.latlng.lng.toFixed(4)})`);
      disablePickingMode();
    }
  });
}

/**
 * Update Reference Point Marker with pulsing gold ripple pin
 */
function updateRefMarker() {
  refMarkerLayer.clearLayers();

  const icon = L.divIcon({
    className: 'custom-leaflet-pin',
    html: `
      <div class="marker ref">
        <div class="ring"></div>
        <div class="pin"></div>
        <div class="tag">${state.currentRef.label} · reference</div>
      </div>
    `,
    iconSize: [20, 20],
    iconAnchor: [10, 10]
  });

  L.marker([state.currentRef.lat, state.currentRef.lon], { icon })
    .bindPopup(`
      <strong style="color:var(--gold)">Reference Point</strong><br>
      ${state.currentRef.label}<br>
      <span style="font-family:var(--font-mono);font-size:10px;color:var(--text-2);">
        ${state.currentRef.lat.toFixed(5)}° N, ${state.currentRef.lon.toFixed(5)}° E
      </span>
    `)
    .addTo(refMarkerLayer);

  // Update Sidebar Displays
  document.getElementById('displayLat').textContent = state.currentRef.lat.toFixed(4);
  document.getElementById('displayLon').textContent = state.currentRef.lon.toFixed(4);
  document.getElementById('selectionStatus').textContent = state.currentRef.label;

  // Redraw connector lines if previous search matches exist
  if (state.lastResult && state.lastResult.matches) {
    drawConnectorLines(state.lastResult.matches);
  }
}

/**
 * Set Reference Point Coordinates and Pan Map
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
    btn.textContent = 'Picking...';
    map.getContainer().style.cursor = 'crosshair';
  }
}

function disablePickingMode() {
  state.isPicking = false;
  const btn = document.getElementById('btnPickPoint');
  btn.classList.remove('active');
  btn.textContent = 'Pick';
  map.getContainer().style.cursor = '';
}

/**
 * Draw Geographic Connector Lines between Reference and Matches
 */
function drawConnectorLines(matches) {
  connectorLinesLayer.clearLayers();
  connectorLines = [];

  const refCoords = [state.currentRef.lat, state.currentRef.lon];

  matches.forEach((m, idx) => {
    // Line weight scales with similarity score
    const norm = Math.max(0.1, (m.score - 0.70) / 0.30);
    const weight = Math.max(1.2, norm * 4.5);

    const line = L.polyline([refCoords, [m.lat, m.lon]], {
      color: '#a58bff',
      weight: weight,
      opacity: 0.38,
      interactive: true
    }).addTo(connectorLinesLayer);

    line.on('mouseover', () => highlightMatch(idx, true));
    line.on('mouseout', () => highlightMatch(idx, false));
    line.on('click', () => zoomToMatch(m.lat, m.lon));

    connectorLines[idx] = line;
  });
}

/**
 * Highlight a match marker, its connector line, and sidebar row on hover
 */
function highlightMatch(index, isHighlight) {
  const line = connectorLines[index];
  if (line) {
    if (isHighlight) {
      line.setStyle({ color: '#f2b544', opacity: 0.95, weight: line.options.weight + 2 });
      line.bringToFront();
    } else {
      line.setStyle({ color: '#a58bff', opacity: 0.38, weight: line.options.weight - 2 });
    }
  }

  const markerEl = document.getElementById(`marker-hit-${index}`);
  if (markerEl) {
    if (isHighlight) {
      markerEl.classList.add('highlighted');
    } else {
      markerEl.classList.remove('highlighted');
    }
  }

  const matchRow = document.querySelector(`.match[data-index="${index}"]`);
  if (matchRow) {
    if (isHighlight) {
      matchRow.classList.add('active');
    } else {
      matchRow.classList.remove('active');
    }
  }
}

/**
 * Event Listeners Setup
 */
function initEventListeners() {
  // Navigation Tabs Switching
  document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
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

  // Preset Validation Case Studies
  document.querySelectorAll('.case-card').forEach(card => {
    card.addEventListener('click', () => {
      document.querySelectorAll('.case-card').forEach(c => c.classList.remove('active'));
      card.classList.add('active');
      const caseKey = card.getAttribute('data-case');
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
    const name = prompt('Enter a label for this site:', state.currentRef.label);
    if (name) {
      saveBookmark(name, state.currentRef.lon, state.currentRef.lat);
    }
  });

  // Year select
  document.getElementById('yearSelect').addEventListener('change', (e) => {
    state.year = parseInt(e.target.value);
    document.getElementById('mapEpochYear').textContent = state.year;
  });

  // Threshold slider with readout
  const slider = document.getElementById('thresholdSlider');
  const readout = document.getElementById('thresh-out');
  slider.addEventListener('input', (e) => {
    state.threshold = parseInt(e.target.value) / 100;
    readout.textContent = state.threshold.toFixed(2);
  });

  // Top N select
  document.getElementById('topNSelect').addEventListener('change', (e) => {
    state.topN = parseInt(e.target.value);
  });

  // Execute Latent Search Button
  document.getElementById('execbtn').addEventListener('click', executeSimilaritySearch);

  // Basemap Switchers (Field view vs. Satellite)
  const btnField = document.getElementById('btnModeField');
  const btnSat = document.getElementById('btnModeSatellite');

  btnField.addEventListener('click', () => {
    btnField.classList.add('active');
    btnSat.classList.remove('active');
    state.mapMode = 'field';
    if (map.hasLayer(satelliteTileLayer)) {
      map.removeLayer(satelliteTileLayer);
    }
  });

  btnSat.addEventListener('click', () => {
    btnSat.classList.add('active');
    btnField.classList.remove('active');
    state.mapMode = 'satellite';
    if (!map.hasLayer(satelliteTileLayer)) {
      satelliteTileLayer.addTo(map);
      satelliteTileLayer.bringToBack();
    }
  });

  // Reset View to AOI
  document.getElementById('btnResetView').addEventListener('click', () => {
    map.fitBounds(aoiRectangle.getBounds(), { padding: [30, 30] });
  });

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

  // JSON Export Button
  document.getElementById('btnExportJson').addEventListener('click', exportResultsJson);
}

/**
 * Execute Similarity Query against Flask Backend
 */
async function executeSimilaritySearch() {
  const btn = document.getElementById('execbtn');
  const lbl = btn.querySelector('.lbl2');
  btn.classList.add('loading');

  // Dynamic loading copy cycling through computation phases
  const loadingSteps = [
    `Fetching ${state.year} embeddings...`,
    'Comparing 64 dimensions...',
    'Extracting optical spectral indices...',
    'Ranking candidates...'
  ];
  let stepIdx = 0;
  lbl.textContent = loadingSteps[0];
  const stepTimer = setInterval(() => {
    stepIdx = (stepIdx + 1) % loadingSteps.length;
    lbl.textContent = loadingSteps[stepIdx];
  }, 1100);

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
    clearInterval(stepTimer);
    btn.classList.remove('loading');
    lbl.textContent = 'Run latent search';
  }
}

/**
 * Render Heatmap Tile Layer, Markers, Connector Lines, and Ranked Matches with Spectral Bars
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

    document.getElementById('layerControlSection').style.display = 'block';
  }

  // 3. Render Match Markers
  matchMarkersLayer.clearLayers();
  matchMarkers = [];

  const matches = data.matches || [];
  matches.forEach((m, idx) => {
    const icon = L.divIcon({
      className: 'custom-leaflet-pin',
      html: `
        <div class="marker hit" id="marker-hit-${idx}">
          <div class="pin"></div>
          <div class="tag">#${m.rank} · ${m.score.toFixed(2)}</div>
        </div>
      `,
      iconSize: [16, 16],
      iconAnchor: [8, 8]
    });

    const marker = L.marker([m.lat, m.lon], { icon })
      .bindPopup(`
        <strong style="color:var(--violet)">Candidate #${m.rank}</strong><br>
        <strong>Similarity:</strong> ${(m.score * 100).toFixed(1)}% (${m.score})<br>
        <span style="font-family:var(--font-mono);font-size:10px;color:var(--text-2);">
          ${m.lat.toFixed(5)}° N, ${m.lon.toFixed(5)}° E
        </span>
        ${m.description ? `<p style="margin:6px 0 0;font-size:11px;color:#c9bffa;">${m.description}</p>` : ''}
      `);

    marker.on('mouseover', () => highlightMatch(idx, true));
    marker.on('mouseout', () => highlightMatch(idx, false));
    marker.on('click', () => zoomToMatch(m.lat, m.lon));

    matchMarkersLayer.addLayer(marker);
    matchMarkers[idx] = marker;
  });

  // 4. Draw dynamic geographic connector lines
  drawConnectorLines(matches);

  // 5. Populate Ranked Results Sidebar with 14-bucket spectral bars, descriptions & side-by-side satellite crops
  const resultsContainer = document.getElementById('matches');
  if (matches.length === 0) {
    resultsContainer.innerHTML = `
      <div class="placeholder-match">
        No candidate locations met the similarity threshold &tau; &ge; ${data.threshold}. Try lowering the threshold slider.
      </div>
    `;
    document.getElementById('btnExportJson').style.display = 'none';
    return;
  }

  document.getElementById('btnExportJson').style.display = 'inline-block';

  const refThumb = data.reference && data.reference.thumbnail_url ? data.reference.thumbnail_url : '';

  let html = '';
  matches.forEach((m, i) => {
    // Generate spectral bars from real 14-bucket pooled values
    let bars = '';
    const spectrum = m.spectrum || [];
    for (let b = 0; b < 14; b++) {
      let val = spectrum[b];
      if (val === undefined || isNaN(val)) {
        val = 0.5 + 0.5 * Math.sin(b * 1.7 + i);
      }
      const h = Math.max(3, Math.round(val * 14));
      const isBright = val > 0.65 || h > 9;
      bars += `<i style="height:${h}px;" class="${isBright ? 'bright' : ''}"></i>`;
    }

    const rankStr = String(i + 1).padStart(2, '0');
    const nameStr = m.name || `Latent match ${m.lat.toFixed(4)}°N, ${m.lon.toFixed(4)}°E`;
    const descText = m.description || 'Both areas share latent structural characteristics in the 64-D embedding space.';
    const matchThumb = m.thumbnail_url || '';

    // Index delta pills
    let indexPillsHtml = '';
    if (m.deltas) {
      const dNdvi = typeof m.deltas.ndvi === 'number' ? m.deltas.ndvi.toFixed(2) : '-';
      const dNdbi = typeof m.deltas.ndbi === 'number' ? m.deltas.ndbi.toFixed(2) : '-';
      const dNdmi = typeof m.deltas.ndmi === 'number' ? m.deltas.ndmi.toFixed(2) : '-';

      const okNdvi = m.deltas.ndvi <= 0.12 ? 'match-ok' : '';
      const okNdbi = m.deltas.ndbi <= 0.12 ? 'match-ok' : '';
      const okNdmi = m.deltas.ndmi <= 0.12 ? 'match-ok' : '';

      indexPillsHtml = `
        <div class="index-pills">
          <span class="index-pill ${okNdvi}" title="Normalized Difference Vegetation Index difference">ΔNDVI: ${dNdvi}</span>
          <span class="index-pill ${okNdbi}" title="Normalized Difference Built-Up Index difference">ΔNDBI: ${dNdbi}</span>
          <span class="index-pill ${okNdmi}" title="Normalized Difference Moisture Index difference">ΔNDMI: ${dNdmi}</span>
        </div>
      `;
    }

    html += `
      <div class="match" data-index="${i}" onclick="zoomToMatch(${m.lat}, ${m.lon})" onmouseenter="highlightMatch(${i}, true)" onmouseleave="highlightMatch(${i}, false)">
        <div class="match-header">
          <span class="rank">${rankStr}</span>
          <div>
            <div class="name">${nameStr}</div>
            <div class="spectrum">${bars}</div>
          </div>
          <span class="score">${m.score.toFixed(2)}</span>
        </div>

        <!-- Plain-Language Similarity Description -->
        <div class="similarity-desc">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#a58bff" stroke-width="2">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="16" x2="12" y2="12"></line>
            <line x1="12" y1="8" x2="12.01" y2="8"></line>
          </svg>
          <span>${descText}</span>
        </div>

        <!-- Side-by-side Optical Satellite Crops (Sentinel-2) -->
        <div class="thumb-compare-tray">
          <div class="thumb-box">
            <div class="thumb-lbl ref"><span>●</span> Ref Optical (S2)</div>
            <div class="thumb-img-wrap">
              ${refThumb ? `<img src="${refThumb}" alt="Reference crop" loading="lazy">` : `<div class="thumb-img-placeholder">Optical Crop</div>`}
            </div>
          </div>
          <div class="thumb-box">
            <div class="thumb-lbl match"><span>●</span> #${m.rank} Match (S2)</div>
            <div class="thumb-img-wrap">
              ${matchThumb ? `<img src="${matchThumb}" alt="Candidate crop" loading="lazy">` : `<div class="thumb-img-placeholder">Optical Crop</div>`}
            </div>
          </div>
        </div>

        ${indexPillsHtml}
      </div>
    `;
  });

  resultsContainer.innerHTML = html;
}

/**
 * Execute Spatial K-Means Clustering
 */
async function executeClustering() {
  const btn = document.getElementById('btnRunClustering');
  const lbl = btn.querySelector('.lbl2');
  btn.classList.add('loading');

  const clusterSteps = [
    'Sampling 64-D landscape...',
    'Running k-means partitioning...',
    'Profiling optical biomes...',
  ];
  let cStepIdx = 0;
  if (lbl) lbl.textContent = clusterSteps[0];
  const cTimer = setInterval(() => {
    cStepIdx = (cStepIdx + 1) % clusterSteps.length;
    if (lbl) lbl.textContent = clusterSteps[cStepIdx];
  }, 1200);

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

    // 3. Show controls and populate legend with real auto-labeled biomes
    document.getElementById('clusterControlsSection').style.display = 'block';
    const legendContainer = document.getElementById('clusterLegendList');
    const clusters = data.clusters || [];

    if (clusters.length > 0) {
      legendContainer.innerHTML = clusters.map(c => {
        const ndviStr = c.indices && typeof c.indices.ndvi === 'number' ? c.indices.ndvi.toFixed(2) : '-';
        const ndbiStr = c.indices && typeof c.indices.ndbi === 'number' ? c.indices.ndbi.toFixed(2) : '-';
        return `
          <div class="cluster-legend-item">
            <span class="cluster-color-badge" style="background: ${c.color}"></span>
            <div class="cluster-legend-text">
              <span class="cluster-name">${c.name}</span>
              <span class="cluster-sub">Cluster #${c.id} &bull; NDVI: ${ndviStr} &bull; Built: ${ndbiStr}</span>
            </div>
          </div>
        `;
      }).join('');
    } else {
      legendContainer.innerHTML = data.palette.map((color, idx) => `
        <div class="cluster-legend-item">
          <span class="cluster-color-badge" style="background: ${color}"></span>
          <div class="cluster-legend-text">
            <span class="cluster-name">Biome Cluster #${idx}</span>
          </div>
        </div>
      `).join('');
    }

  } catch (err) {
    alert(`Clustering Error:\n${err.message}`);
  } finally {
    clearInterval(cTimer);
    btn.classList.remove('loading');
    if (lbl) lbl.textContent = 'Partition Landscape';
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
      container.innerHTML = '<div class="placeholder-match">No saved bookmarks found.</div>';
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
    container.innerHTML = '<div class="placeholder-match">Failed to load bookmarks.</div>';
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
      container.innerHTML = '<div class="placeholder-match">No queries executed yet.</div>';
      return;
    }

    container.innerHTML = data.history.map(h => `
      <div class="history-card" onclick="selectBookmark(${h.lon}, ${h.lat}, '${escapeQuotes(h.label || 'History Item')}')">
        <div class="history-header">
          <span class="bookmark-name">${h.label || 'Search'}</span>
          <span class="bookmark-category">${h.match_count} matches</span>
        </div>
        <div class="history-meta">
          <span>Year: ${h.year} &bull; &tau; &ge; ${h.threshold} &bull; Top: ${h.top_score ? (h.top_score * 100).toFixed(1) + '%' : 'N/A'}</span>
        </div>
      </div>
    `).join('');
  } catch {
    container.innerHTML = '<div class="placeholder-match">Failed to load history.</div>';
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
  a.download = `geosim_latent_spectrum_${state.year}_thresh${state.threshold}.json`;
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
      badge.className = 'status';
      badge.textContent = 'gee connected';
    } else {
      badge.className = 'status';
      badge.style.color = '#f59e0b';
      badge.style.borderColor = '#78350f';
      badge.textContent = 'gee connecting...';
    }
  } catch {
    const badge = document.getElementById('statusBadge');
    badge.className = 'status offline';
    badge.textContent = 'backend offline';
  }
}
