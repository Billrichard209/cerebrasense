/* ═══════════════════════════════════════════════════════════
   CerebraSense Interactive Engine v2.0
   Vanilla SPA Router, Procedural MRI Viewer, & Dynamic Charts
   ═══════════════════════════════════════════════════════════ */

// ── 1. Rich Patient Profiles & Datasets ───────────────────
const patients = {
  'OAS2_0001': {
    name: 'OAS2_0001',
    age: 72,
    gender: 'F',
    scanner: 'Siemens 3T Magnetom',
    sequence: 'T1w MPRAGE',
    voxelSize: '1.0 × 1.0 × 1.0 mm³',
    matrixSize: '256 × 256 × 96',
    acquisitionDate: '2024-03-15',
    risk: 0.74,
    hippocampalVolume: 5.8,
    completeness: 96,
    confidence: 88,
    mmse: 24,
    trend: [
      { visit: 1, date: '2019-02-10', risk: 0.52, hippo: 6.4, mmse: 28 },
      { visit: 2, date: '2020-03-14', risk: 0.58, hippo: 6.2, mmse: 27 },
      { visit: 3, date: '2021-04-18', risk: 0.63, hippo: 6.1, mmse: 26 },
      { visit: 4, date: '2022-05-20', risk: 0.69, hippo: 5.9, mmse: 25 },
      { visit: 5, date: '2023-04-22', risk: 0.71, hippo: 5.8, mmse: 24 },
      { visit: 6, date: '2024-03-15', risk: 0.74, hippo: 5.8, mmse: 24 },
      { visit: 7, date: '2024-09-12', risk: 0.78, hippo: 5.6, mmse: 23 },
      { visit: 8, date: '2025-03-10', risk: 0.81, hippo: 5.5, mmse: 22 },
      { visit: 9, date: '2025-09-15', risk: 0.83, hippo: 5.3, mmse: 21 },
      { visit: 10, date: '2026-03-20', risk: 0.85, hippo: 5.2, mmse: 21 },
      { visit: 11, date: '2026-09-10', risk: 0.87, hippo: 5.0, mmse: 20 },
      { visit: 12, date: '2027-03-15', risk: 0.89, hippo: 4.8, mmse: 19 }
    ],
    features: [
      { name: "Hippocampal asymmetry", impact: 82, trend: 'up', desc: 'Asymmetry index is significantly elevated at 82%, reflecting progressive left-sided volume loss.' },
      { name: "Ventricular enlargement", impact: 74, trend: 'up', desc: 'Lateral ventricles show moderate expansion (74th percentile for age), consistent with ex-vacuo changes.' },
      { name: "Temporal lobe thinning", impact: 68, trend: 'up', desc: 'Left superior temporal gyrus cortical thickness is reduced to 68% of standard control thresholds.' },
      { name: "Global cortical pattern", impact: 57, trend: 'neutral', desc: 'Diffuse cortical atrophy pattern is emerging, particularly localized in parieto-temporal association areas.' },
    ],
    regions: [
      { name: 'Left Hippocampus', volume: '2.68 cm³', status: 'critical', pct: '−18.4% vs control' },
      { name: 'Right Hippocampus', volume: '3.12 cm³', status: 'moderate', pct: '−8.2% vs control' },
      { name: 'Lateral Ventricles', volume: '48.2 cm³', status: 'critical', pct: '+35.1% enlargement' },
      { name: 'Entorhinal Cortex', volume: '2.14 mm thickness', status: 'critical', pct: '−15.2% thinning' },
      { name: 'Frontal Cortex', volume: '3.42 mm thickness', status: 'normal', pct: '−1.1% stable' }
    ],
    recommendations: "Recommend close clinical follow-up in 6 months with Repeat Structural MRI sequence. Volumetric progression in left hippocampus (atrophy rate of 5.8% annually) exceeds standard healthy aging thresholds. Consider starting pharmacological interventions (acetylcholinesterase inhibitors) if clinically indicated and initiate cognitive exercises.",
    findings: [
      { severity: 'high', text: 'Significant bilateral hippocampal atrophy, more pronounced on the left (volume 2.68 cm³, −18.4% deviation from control).' },
      { severity: 'high', text: 'Ventriculomegaly involving the lateral and third ventricles, representing ex-vacuo dilation secondary to cerebral volume loss.' },
      { severity: 'medium', text: 'Cortical thinning of the entorhinal and temporoparietal cortices, consistent with Braak Stage III-IV structural pattern.' },
      { severity: 'low', text: 'Frontal lobe structures and white matter tracts are relatively preserved with minimal focal hyperintensities.' }
    ]
  },
  'OAS2_0002': {
    name: 'OAS2_0002',
    age: 68,
    gender: 'M',
    scanner: 'GE Healthcare 3T Signa',
    sequence: 'T1w CUBE',
    voxelSize: '1.0 × 1.0 × 1.0 mm³',
    matrixSize: '256 × 256 × 96',
    acquisitionDate: '2024-04-10',
    risk: 0.38,
    hippocampalVolume: 6.9,
    completeness: 100,
    confidence: 84,
    mmse: 27,
    trend: [
      { visit: 1, date: '2021-04-15', risk: 0.32, hippo: 7.2, mmse: 28 },
      { visit: 2, date: '2022-04-20', risk: 0.33, hippo: 7.1, mmse: 28 },
      { visit: 3, date: '2023-04-18', risk: 0.35, hippo: 7.0, mmse: 27 },
      { visit: 4, date: '2024-04-10', risk: 0.38, hippo: 6.9, mmse: 27 },
      { visit: 5, date: '2024-10-15', risk: 0.40, hippo: 6.8, mmse: 27 },
      { visit: 6, date: '2025-04-22', risk: 0.42, hippo: 6.7, mmse: 26 },
      { visit: 7, date: '2025-10-12', risk: 0.43, hippo: 6.6, mmse: 26 },
      { visit: 8, date: '2026-04-18', risk: 0.45, hippo: 6.6, mmse: 26 },
      { visit: 9, date: '2026-10-15', risk: 0.47, hippo: 6.5, mmse: 25 },
      { visit: 10, date: '2027-04-20', risk: 0.49, hippo: 6.4, mmse: 25 },
      { visit: 11, date: '2027-10-10', risk: 0.51, hippo: 6.3, mmse: 24 },
      { visit: 12, date: '2028-04-15', risk: 0.53, hippo: 6.2, mmse: 24 }
    ],
    features: [
      { name: "Global cortical pattern", impact: 52, trend: 'up', desc: 'Mild cortical volume reductions are noted in parietal regions, slightly exceeding standard reference lines.' },
      { name: "Temporal lobe thinning", impact: 44, trend: 'neutral', desc: 'Temporal cortex thickness is in the low-normal range (44% relative impact index) without localized lesions.' },
      { name: "Ventricular enlargement", impact: 38, trend: 'up', desc: 'Lateral ventricles show very mild expansion, remaining well within the normal distribution for a 68-year-old.' },
      { name: "Hippocampal asymmetry", impact: 29, trend: 'neutral', desc: 'Hippocampal structures are largely symmetrical with an asymmetry index of only 29%.' },
    ],
    regions: [
      { name: 'Left Hippocampus', volume: '3.41 cm³', status: 'normal', pct: '−3.2% stable' },
      { name: 'Right Hippocampus', volume: '3.49 cm³', status: 'normal', pct: '−1.4% stable' },
      { name: 'Lateral Ventricles', volume: '34.8 cm³', status: 'moderate', pct: '+8.4% enlargement' },
      { name: 'Entorhinal Cortex', volume: '2.48 mm thickness', status: 'normal', pct: '−2.5% stable' },
      { name: 'Frontal Cortex', volume: '3.85 mm thickness', status: 'normal', pct: '+0.5% stable' }
    ],
    recommendations: "Bilateral brain volumes and hippocampal regions are largely stable, showing age-appropriate changes with a slight, non-statistically-significant risk of progressive cognitive decline. Regular longitudinal MRI follow-up is recommended in 12 months. Encourage cardiovascular exercise and mental stimulation activities.",
    findings: [
      { severity: 'medium', text: 'Mild ventricular enlargement corresponding to age-appropriate cerebral volume loss.' },
      { severity: 'low', text: 'Bilateral hippocampal structures are within normal boundaries (combined volume 6.90 cm³, −2.3% age deviation).' },
      { severity: 'low', text: 'No evidence of severe cortical thinning or localized focal atrophy. Normal signal intensities in subcortical nuclei.' }
    ]
  },
  'OAS2_0003': {
    name: 'OAS2_0003',
    age: 63,
    gender: 'F',
    scanner: 'Philips Intera 3T',
    sequence: 'T1w 3D FFE',
    voxelSize: '1.0 × 1.0 × 1.0 mm³',
    matrixSize: '256 × 256 × 96',
    acquisitionDate: '2024-05-02',
    risk: 0.12,
    hippocampalVolume: 7.6,
    completeness: 100,
    confidence: 94,
    mmse: 30,
    trend: [
      { visit: 1, date: '2021-05-10', risk: 0.10, hippo: 7.7, mmse: 30 },
      { visit: 2, date: '2022-05-15', risk: 0.11, hippo: 7.6, mmse: 30 },
      { visit: 3, date: '2023-05-08', risk: 0.11, hippo: 7.6, mmse: 30 },
      { visit: 4, date: '2024-05-02', risk: 0.12, hippo: 7.6, mmse: 30 },
      { visit: 5, date: '2024-11-04', risk: 0.12, hippo: 7.5, mmse: 30 },
      { visit: 6, date: '2025-05-10', risk: 0.13, hippo: 7.5, mmse: 29 },
      { visit: 7, date: '2025-11-12', risk: 0.13, hippo: 7.5, mmse: 29 },
      { visit: 8, date: '2026-05-15', risk: 0.14, hippo: 7.4, mmse: 30 },
      { visit: 9, date: '2026-11-08', risk: 0.14, hippo: 7.4, mmse: 29 },
      { visit: 10, date: '2027-05-10', risk: 0.15, hippo: 7.3, mmse: 30 },
      { visit: 11, date: '2027-11-12', risk: 0.15, hippo: 7.3, mmse: 29 },
      { visit: 12, date: '2028-05-15', risk: 0.16, hippo: 7.2, mmse: 29 }
    ],
    features: [
      { name: "Global cortical pattern", impact: 18, trend: 'neutral', desc: 'No signs of cortical thinning; thickness indices remain in the upper 80th percentile.' },
      { name: "Hippocampal asymmetry", impact: 15, trend: 'neutral', desc: 'Bilateral hippocampal structures show excellent symmetry.' },
      { name: "Ventricular enlargement", impact: 12, trend: 'neutral', desc: 'Ventricles are tight and slit-like, indicating zero pathological expansion.' },
      { name: "Temporal lobe thinning", impact: 10, trend: 'neutral', desc: 'Temporal cortex thickness is normal and stable.' },
    ],
    regions: [
      { name: 'Left Hippocampus', volume: '3.78 cm³', status: 'normal', pct: '+2.1% vs control' },
      { name: 'Right Hippocampus', volume: '3.82 cm³', status: 'normal', pct: '+2.8% vs control' },
      { name: 'Lateral Ventricles', volume: '22.4 cm³', status: 'normal', pct: 'Normal volume' },
      { name: 'Entorhinal Cortex', volume: '2.84 mm thickness', status: 'normal', pct: 'Normal thickness' },
      { name: 'Frontal Cortex', volume: '4.12 mm thickness', status: 'normal', pct: 'Perfect thickness' }
    ],
    recommendations: "MRI findings demonstrate completely healthy cerebral structures, with no indications of neurodegenerative atrophy or progressive ventricular expansion. Cognitive performance is excellent. Routine screening as appropriate in 2 years.",
    findings: [
      { severity: 'low', text: 'Bilateral hippocampal volumes are highly preserved and show perfect symmetry, within normal high ranges.' },
      { severity: 'low', text: 'Ventricular space is well-defined and exhibits normal volume without enlargement.' },
      { severity: 'low', text: 'Cortical mantle thickness is preserved uniformly across all lobes. Zero signs of focal atrophy or vascular lesions.' }
    ]
  }
};

// ── 2. Application Global State ──────────────────────────
const state = {
  activePage: 'overview',
  activePatient: 'OAS2_0001',
  activeVisitsCount: 6,
  selectedMetrics: ['risk', 'hippo'], // Default active metrics in Longitudinal Trend page
  sliceIndices: {
    axial: 48,
    coronal: 48,
    sagittal: 48
  },
  hoveredPoint: null
};

// Helper constants
const CIRCUMFERENCE = 2 * Math.PI * 24; // ~150.796 for circular progress rings (radius = 24)

// ── 3. Application Entry & Router Initialization ──────────
document.addEventListener("DOMContentLoaded", () => {
  initRouter();
  initPatientDropdown();
  initScanExplorer();
  initLongitudinalControls();
  initAnalysisSimulation();
  initReportExport();
  
  // Perform first render cycle
  triggerFullRender();
});

// SPA Router
function initRouter() {
  const navItems = document.querySelectorAll(".nav-item");
  navItems.forEach(btn => {
    btn.addEventListener("click", () => {
      const pageId = btn.getAttribute("data-page");
      switchPage(pageId);
    });
  });

  // Mobile navigation overlay closing
  const overlay = document.getElementById("sidebarOverlay");
  const sidebar = document.getElementById("sidebar");
  const menuBtn = document.getElementById("menuBtn");

  menuBtn.addEventListener("click", () => {
    sidebar.classList.add("open");
    overlay.classList.add("open");
  });

  overlay.addEventListener("click", () => {
    sidebar.classList.remove("open");
    overlay.classList.remove("open");
  });

  // Global keyboard listener for navigation
  document.addEventListener("keydown", (e) => {
    if (document.activeElement.tagName === 'INPUT' || document.activeElement.tagName === 'TEXTAREA') return;
    
    const pages = ['overview', 'scan-explorer', 'longitudinal', 'explainability', 'reports'];
    let idx = pages.indexOf(state.activePage);
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      idx = (idx + 1) % pages.length;
      switchPage(pages[idx]);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      idx = (idx - 1 + pages.length) % pages.length;
      switchPage(pages[idx]);
    }
  });
}

function switchPage(pageId) {
  state.activePage = pageId;

  // Toggle active CSS class in sidebar nav items
  document.querySelectorAll(".nav-item").forEach(item => {
    if (item.getAttribute("data-page") === pageId) {
      item.classList.add("active");
    } else {
      item.classList.remove("active");
    }
  });

  // Toggle page visibility
  document.querySelectorAll(".page-view").forEach(page => {
    if (page.id === `page-${pageId}`) {
      page.classList.add("active");
    } else {
      page.classList.remove("active");
    }
  });

  // Update topbar title based on active page
  const titles = {
    'overview': 'Structural MRI Review Workspace',
    'scan-explorer': 'High-Resolution MRI Scan Explorer',
    'longitudinal': 'Multi-Metric Longitudinal Tracking',
    'explainability': 'Clinical Explainability & Feature Attributions',
    'reports': 'AI-Assisted Clinical Decision Report'
  };
  document.getElementById("pageTitle").textContent = titles[pageId] || 'Workspace';

  // Redraw canvases depending on the active page
  if (pageId === 'overview') {
    renderTrendChart();
  } else if (pageId === 'scan-explorer') {
    renderAllMRIPlanes();
  } else if (pageId === 'longitudinal') {
    renderLongitudinalChart();
  }

  // Close sidebar drawer if open on mobile view
  document.getElementById("sidebar").classList.remove("open");
  document.getElementById("sidebarOverlay").classList.remove("open");
}

// ── 4. Patient Selector Custom Dropdown ───────────────────
function initPatientDropdown() {
  const patientBtn = document.getElementById("patientSelector");
  
  // Create beautiful glass dropdown list element
  const dropdown = document.createElement("div");
  dropdown.className = "patient-dropdown-menu";
  
  // Add item for each patient
  Object.keys(patients).forEach(id => {
    const p = patients[id];
    const item = document.createElement("div");
    item.className = "patient-dropdown-item";
    if (id === state.activePatient) item.classList.add("active");
    
    item.innerHTML = `
      <strong>Patient: ${p.name}</strong>
      <span>Age: ${p.age} · ${p.gender} · Risk Signal: ${(p.risk).toFixed(2)}</span>
    `;
    
    item.addEventListener("click", (e) => {
      e.stopPropagation();
      selectPatient(id);
      dropdown.classList.remove("open");
    });
    
    dropdown.appendChild(item);
  });
  
  patientBtn.appendChild(dropdown);
  
  // Toggle dropdown on selector button click
  patientBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    dropdown.classList.toggle("open");
  });
  
  // Close dropdown if clicked outside
  document.addEventListener("click", () => {
    dropdown.classList.remove("open");
  });
}

function selectPatient(id) {
  state.activePatient = id;
  
  // Update dropdown checked active state
  document.querySelectorAll(".patient-dropdown-item").forEach(item => {
    const isTarget = item.querySelector("strong").textContent.includes(id);
    item.classList.toggle("active", isTarget);
  });
  
  // Update Patient Selector Text
  document.querySelector("#patientSelector span").textContent = `Patient: ${id}`;
  
  // Redraw all components
  triggerFullRender();
}

// ── 5. KPI Count-Up & Radial Gauge Animation ─────────────
function animateKPIValue(elId, start, end, formatFn) {
  const el = document.getElementById(elId);
  if (!el) return;
  
  const duration = 1000;
  const startTime = performance.now();
  
  function update(currentTime) {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);
    
    // Smooth quadratic ease-out
    const ease = progress * (2 - progress);
    const value = start + (end - start) * ease;
    
    el.textContent = formatFn(value);
    
    if (progress < 1) {
      requestAnimationFrame(update);
    }
  }
  
  requestAnimationFrame(update);
}

function updateKPIGauges(patient) {
  // Update Risk Gauge
  const riskCircle = document.querySelector('circle[data-gauge="risk"]');
  if (riskCircle) {
    riskCircle.style.strokeDasharray = CIRCUMFERENCE;
    const offset = CIRCUMFERENCE - (patient.risk * CIRCUMFERENCE);
    riskCircle.style.strokeDashoffset = offset;
    
    // Scale container badge opacity color index
    const parentCard = riskCircle.closest(".kpi");
    if (parentCard) parentCard.setAttribute("data-gauge-pct", Math.round(patient.risk * 100));
  }
  animateKPIValue("riskValue", 0, patient.risk, v => v.toFixed(2));
  
  // Update Hippocampal Vol Gauge
  const hippoCircle = document.querySelector('circle[data-gauge="hippo"]');
  if (hippoCircle) {
    hippoCircle.style.strokeDasharray = CIRCUMFERENCE;
    // Normalize: healthy volume range is ~4.0 to ~8.0 cm³
    const pct = Math.max(10, Math.min(98, ((patient.hippocampalVolume - 4) / 4) * 100));
    hippoCircle.style.strokeDashoffset = CIRCUMFERENCE - (pct / 100 * CIRCUMFERENCE);
    
    const parentCard = hippoCircle.closest(".kpi");
    if (parentCard) parentCard.setAttribute("data-gauge-pct", Math.round(pct));
  }
  animateKPIValue("hippoValue", 0, patient.hippocampalVolume, v => `${v.toFixed(1)} cm³`);
  
  // Update Data Completeness Gauge
  const dataCircle = document.querySelector('circle[data-gauge="data"]');
  if (dataCircle) {
    dataCircle.style.strokeDasharray = CIRCUMFERENCE;
    dataCircle.style.strokeDashoffset = CIRCUMFERENCE - (patient.completeness / 100 * CIRCUMFERENCE);
  }
  animateKPIValue("dataValue", 0, patient.completeness, v => `${Math.round(v)}%`);
  
  // Update Model Confidence Gauge
  const confCircle = document.querySelector('circle[data-gauge="conf"]');
  if (confCircle) {
    confCircle.style.strokeDasharray = CIRCUMFERENCE;
    confCircle.style.strokeDashoffset = CIRCUMFERENCE - (patient.confidence / 100 * CIRCUMFERENCE);
  }
  animateKPIValue("confValue", 0, patient.confidence, v => `${Math.round(v)}%`);
}

// ── 6. Longitudinal Risk Chart (Interactive Canvas) ──────
function renderTrendChart() {
  const canvas = document.getElementById("trendChart");
  if (!canvas || state.activePage !== 'overview') return;

  const patient = patients[state.activePatient];
  // Filter the visits count
  const visits = patient.trend.slice(0, state.activeVisitsCount);
  
  // Setup HDPI Scaling
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  canvas.width = rect.width * dpr;
  canvas.height = 240 * dpr;
  canvas.style.height = '240px';
  
  const ctx = canvas.getContext("2d");
  ctx.scale(dpr, dpr);
  
  const width = rect.width;
  const height = 240;
  const paddingLeft = 45;
  const paddingRight = 20;
  const paddingTop = 25;
  const paddingBottom = 35;
  
  const chartW = width - paddingLeft - paddingRight;
  const chartH = height - paddingTop - paddingBottom;
  
  ctx.clearRect(0, 0, width, height);
  
  // 1. Draw Grid Lines & Y-Axis Scale
  const yLines = 5;
  ctx.strokeStyle = "rgba(148, 163, 184, 0.08)";
  ctx.lineWidth = 1;
  ctx.fillStyle = "rgba(148, 163, 184, 0.5)";
  ctx.font = "10px Inter, sans-serif";
  ctx.textAlign = "right";
  ctx.textBaseline = "middle";
  
  for (let i = 0; i < yLines; i++) {
    const val = 0.2 + (i * 0.8) / (yLines - 1); // 0.2 to 1.0
    const y = paddingTop + chartH - (i * chartH) / (yLines - 1);
    
    // Grid line
    ctx.beginPath();
    ctx.moveTo(paddingLeft, y);
    ctx.lineTo(width - paddingRight, y);
    ctx.stroke();
    
    // Label
    ctx.fillText(val.toFixed(2), paddingLeft - 10, y);
  }
  
  // 2. Draw Clinical Threshold Line at 0.70
  const thresholdVal = 0.70;
  const thresholdY = paddingTop + chartH - ((thresholdVal - 0.2) / 0.8) * chartH;
  ctx.strokeStyle = "rgba(239, 68, 68, 0.4)";
  ctx.lineWidth = 1.5;
  ctx.setLineDash([5, 5]);
  ctx.beginPath();
  ctx.moveTo(paddingLeft, thresholdY);
  ctx.lineTo(width - paddingRight, thresholdY);
  ctx.stroke();
  ctx.setLineDash([]); // Reset
  
  ctx.fillStyle = "rgba(239, 68, 68, 0.8)";
  ctx.font = "9px Inter, sans-serif";
  ctx.textAlign = "left";
  ctx.fillText("CLINICAL DANGER THRESHOLD (0.70)", paddingLeft + 10, thresholdY - 8);
  
  // 3. Map Data points to Canvas Coordinates
  const points = visits.map((pt, idx) => {
    const x = paddingLeft + (idx * chartW) / (visits.length - 1);
    const y = paddingTop + chartH - ((pt.risk - 0.2) / 0.8) * chartH;
    return { x, y, val: pt.risk, date: pt.date, visit: pt.visit, original: pt };
  });
  
  // Store mapped coordinates globally for hover logic
  state.mappedTrendPoints = points;
  
  if (points.length < 2) return;
  
  // 4. Draw Line Area Gradient Fill (Bezier Path)
  const fillGrad = ctx.createLinearGradient(0, paddingTop, 0, paddingTop + chartH);
  fillGrad.addColorStop(0, "rgba(59, 130, 246, 0.25)");
  fillGrad.addColorStop(1, "rgba(59, 130, 246, 0.0)");
  
  ctx.fillStyle = fillGrad;
  ctx.beginPath();
  ctx.moveTo(points[0].x, paddingTop + chartH);
  
  // Draw Bezier curves to fill
  ctx.lineTo(points[0].x, points[0].y);
  for (let i = 0; i < points.length - 1; i++) {
    const p0 = points[i];
    const p1 = points[i + 1];
    const cpX1 = p0.x + (p1.x - p0.x) / 2;
    const cpY1 = p0.y;
    const cpX2 = p0.x + (p1.x - p0.x) / 2;
    const cpY2 = p1.y;
    ctx.bezierCurveTo(cpX1, cpY1, cpX2, cpY2, p1.x, p1.y);
  }
  ctx.lineTo(points[points.length - 1].x, paddingTop + chartH);
  ctx.closePath();
  ctx.fill();
  
  // 5. Draw Curve Stroke Line
  const lineGrad = ctx.createLinearGradient(paddingLeft, 0, width - paddingRight, 0);
  lineGrad.addColorStop(0, "#3b82f6");
  lineGrad.addColorStop(1, "#06b6d4");
  
  ctx.strokeStyle = lineGrad;
  ctx.lineWidth = 3.5;
  ctx.lineCap = "round";
  ctx.beginPath();
  
  ctx.moveTo(points[0].x, points[0].y);
  for (let i = 0; i < points.length - 1; i++) {
    const p0 = points[i];
    const p1 = points[i + 1];
    const cpX1 = p0.x + (p1.x - p0.x) / 2;
    const cpY1 = p0.y;
    const cpX2 = p0.x + (p1.x - p0.x) / 2;
    const cpY2 = p1.y;
    ctx.bezierCurveTo(cpX1, cpY1, cpX2, cpY2, p1.x, p1.y);
  }
  ctx.stroke();
  
  // 6. Draw X-Axis labels & Point Circles
  ctx.font = "10px Inter, sans-serif";
  ctx.fillStyle = "rgba(148, 163, 184, 0.6)";
  ctx.textAlign = "center";
  
  points.forEach((pt, idx) => {
    // X Label
    ctx.fillText(`V${pt.visit}`, pt.x, paddingTop + chartH + 18);
    
    // Draw outer glow circle
    const isHovered = state.hoveredPoint && state.hoveredPoint.idx === idx && state.hoveredPoint.chart === 'trend';
    
    ctx.beginPath();
    ctx.arc(pt.x, pt.y, isHovered ? 9 : 6, 0, Math.PI * 2);
    ctx.fillStyle = isHovered ? "rgba(59, 130, 246, 0.4)" : "rgba(6, 182, 212, 0.2)";
    ctx.fill();
    
    // Inner solid core
    ctx.beginPath();
    ctx.arc(pt.x, pt.y, 4, 0, Math.PI * 2);
    ctx.fillStyle = "#ffffff";
    ctx.fill();
    ctx.strokeStyle = "#3b82f6";
    ctx.lineWidth = 2.5;
    ctx.stroke();
  });
  
  // Set up hover listeners on trendChart if not already added
  if (!canvas.dataset.listener) {
    canvas.addEventListener("mousemove", handleTrendChartHover);
    canvas.addEventListener("mouseleave", handleTrendChartLeave);
    canvas.dataset.listener = "true";
  }
}

function handleTrendChartHover(e) {
  const canvas = e.target;
  const rect = canvas.getBoundingClientRect();
  const x = e.clientX - rect.left;
  const y = e.clientY - rect.top;
  
  const points = state.mappedTrendPoints;
  if (!points) return;
  
  let closest = null;
  let minDist = 20; // 20px threshold
  
  points.forEach((pt, idx) => {
    const dist = Math.hypot(pt.x - x, pt.y - y);
    if (dist < minDist) {
      minDist = dist;
      closest = { ...pt, idx };
    }
  });
  
  const tooltip = document.getElementById("chartTooltip");
  if (closest) {
    state.hoveredPoint = { chart: 'trend', idx: closest.idx };
    
    // Calculate delta text
    let deltaText = "First baseline visit";
    let deltaClass = "neutral";
    if (closest.idx > 0) {
      const prev = points[closest.idx - 1].val;
      const diff = closest.val - prev;
      if (diff > 0) {
        deltaText = `▲ +${diff.toFixed(2)} vs previous`;
        deltaClass = "up"; // higher risk is worse (colored red/up)
      } else if (diff < 0) {
        deltaText = `▼ ${diff.toFixed(2)} vs previous`;
        deltaClass = "down";
      } else {
        deltaText = `■ Unchanged`;
      }
    }
    
    // Populate tooltip UI
    tooltip.querySelector(".tt-label").textContent = `Visit ${closest.visit} · ${closest.date}`;
    tooltip.querySelector(".tt-value").textContent = `Risk Score: ${closest.val.toFixed(2)}`;
    
    const deltaEl = tooltip.querySelector(".tt-delta");
    deltaEl.className = `tt-delta ${deltaClass === 'up' ? 'down' : 'up'}`; // Reverse classes since higher risk is negative outcome
    deltaEl.textContent = deltaText;
    
    // Position tooltip
    tooltip.style.left = `${closest.x - tooltip.offsetWidth / 2}px`;
    tooltip.style.top = `${closest.y - tooltip.offsetHeight - 12}px`;
    tooltip.classList.add("visible");
    
    // Re-draw canvas to trigger point highlight animation frame
    renderTrendChart();
  } else {
    handleTrendChartLeave();
  }
}

function handleTrendChartLeave() {
  if (state.hoveredPoint && state.hoveredPoint.chart === 'trend') {
    state.hoveredPoint = null;
    const tooltip = document.getElementById("chartTooltip");
    tooltip.classList.remove("visible");
    renderTrendChart();
  }
}

// ── 7. Explainability Features List (Overview & Explain Page) ──
function renderExplainability(patient) {
  // 1. Render mini Overview list
  const overviewList = document.getElementById("featureList");
  if (overviewList) {
    overviewList.innerHTML = "";
    patient.features.forEach(feat => {
      const li = document.createElement("li");
      
      let tierClass = "low";
      if (feat.impact >= 75) tierClass = "high";
      else if (feat.impact >= 50) tierClass = "medium";
      
      const icon = feat.trend === 'up' ? '▲' : (feat.trend === 'down' ? '▼' : '•');
      const trendColor = feat.trend === 'up' ? 'var(--danger)' : 'var(--text-muted)';
      
      li.innerHTML = `
        <div class="feature-row">
          <span>${feat.name} <span style="color:${trendColor}; font-size:10px; margin-left:4px;">${icon}</span></span>
          <strong>${feat.impact}%</strong>
        </div>
        <div class="bar ${tierClass}"><span style="width: 0%"></span></div>
      `;
      overviewList.appendChild(li);
      
      // Animate width progress bar asynchronously after rendering
      setTimeout(() => {
        const barSpan = li.querySelector(".bar span");
        if (barSpan) barSpan.style.width = `${feat.impact}%`;
      }, 50);
    });
  }
  
  // 2. Render Full Explainability page details
  const fullList = document.getElementById("explainFullList");
  if (fullList) {
    fullList.innerHTML = "";
    patient.features.forEach(feat => {
      const li = document.createElement("li");
      li.style.marginBottom = "var(--sp-4)";
      
      let tierClass = "low";
      if (feat.impact >= 75) tierClass = "high";
      else if (feat.impact >= 50) tierClass = "medium";
      
      li.innerHTML = `
        <div class="feature-row" style="font-weight: 600; font-size: var(--text-base);">
          <span>${feat.name}</span>
          <span style="color: var(--primary-light)">${feat.impact}% Attribution</span>
        </div>
        <div class="bar ${tierClass}" style="height: 10px; margin: var(--sp-2) 0;"><span style="width: 0%"></span></div>
        <p style="font-size: var(--text-sm); color: var(--text-secondary); line-height: 1.5;">${feat.desc}</p>
      `;
      fullList.appendChild(li);
      
      setTimeout(() => {
        const barSpan = li.querySelector(".bar span");
        if (barSpan) barSpan.style.width = `${feat.impact}%`;
      }, 50);
    });
  }
  
  // Populate Region list
  const regionList = document.getElementById("regionList");
  if (regionList) {
    regionList.innerHTML = "";
    patient.regions.forEach(reg => {
      const item = document.createElement("div");
      item.className = "region-item";
      
      let badgeClass = "normal";
      if (reg.status === 'critical') badgeClass = "critical";
      else if (reg.status === 'moderate') badgeClass = "moderate";
      
      item.innerHTML = `
        <div>
          <div style="font-weight:600;">${reg.name}</div>
          <div style="font-size:10px; color:var(--text-muted); margin-top:2px;">${reg.pct}</div>
        </div>
        <span class="region-badge ${badgeClass}">${reg.status.toUpperCase()} (${reg.volume})</span>
      `;
      regionList.appendChild(item);
    });
  }
  
  // Populate Performance metrics cards
  const perfMetrics = document.getElementById("perfMetrics");
  if (perfMetrics) {
    perfMetrics.innerHTML = `
      <div class="perf-item">
        <div class="perf-val">0.942</div>
        <div class="perf-label">ROC-AUC Score</div>
      </div>
      <div class="perf-item">
        <div class="perf-val">91.8%</div>
        <div class="perf-label">Sensitivity</div>
      </div>
      <div class="perf-item">
        <div class="perf-val">88.4%</div>
        <div class="perf-label">Specificity</div>
      </div>
      <div class="perf-item">
        <div class="perf-val">90.5%</div>
        <div class="perf-label">F1-Score</div>
      </div>
    `;
  }
}

// ── 8. Procedural MRI Scan Plane Slice Renderer ──────────
function initScanExplorer() {
  const planes = ['Axial', 'Coronal', 'Sagittal'];
  
  planes.forEach(planeLower => {
    const plane = planeLower.toLowerCase();
    const slider = document.getElementById(`slider${planeLower}`);
    const label = document.getElementById(`label${planeLower}`);
    
    if (slider) {
      slider.addEventListener("input", (e) => {
        const val = parseInt(e.target.value);
        state.sliceIndices[plane] = val;
        label.textContent = `Slice ${val}`;
        
        // Render target plane slice
        renderMRIPlane(planeLower, val);
      });
    }
  });
}

function renderAllMRIPlanes() {
  renderMRIPlane('Axial', state.sliceIndices.axial);
  renderMRIPlane('Coronal', state.sliceIndices.coronal);
  renderMRIPlane('Sagittal', state.sliceIndices.sagittal);
}

function renderMRIPlane(plane, sliceIndex) {
  const canvas = document.getElementById(`scan${plane}`);
  if (!canvas || state.activePage !== 'scan-explorer') return;
  
  const ctx = canvas.getContext("2d");
  const width = canvas.width;
  const height = canvas.height;
  
  // Clear black canvas
  ctx.fillStyle = "#020617";
  ctx.fillRect(0, 0, width, height);
  
  // Get active patient details to adjust brain structure shapes (e.g. atrophic ventricles enlargement)
  const patient = patients[state.activePatient];
  const isHighRisk = patient.risk > 0.6;
  const ventricleEnlargeFactor = isHighRisk ? 1.6 : 0.8;
  const hippocampusAtrophyFactor = isHighRisk ? 0.6 : 1.0;
  
  // Add medical grid overlay ticks
  ctx.strokeStyle = "rgba(148, 163, 184, 0.05)";
  ctx.lineWidth = 1;
  ctx.beginPath();
  for (let i = 32; i < width; i += 32) {
    ctx.moveTo(i, 0); ctx.lineTo(i, height);
    ctx.moveTo(0, i); ctx.lineTo(width, i);
  }
  ctx.stroke();
  
  const centerX = width / 2;
  const centerY = height / 2;
  
  // Calculate rendering size factor based on slice index (simulating moving along the head volume)
  // Slices near edges (0 and 95) are smaller, middle slices (48) are largest
  const distFromCenter = Math.abs(sliceIndex - 48);
  const volumeFactor = Math.max(0.1, 1 - (distFromCenter / 52));
  
  if (plane === 'Axial') {
    // 1. Draw Skull boundary
    ctx.strokeStyle = "#1e293b";
    ctx.lineWidth = 4 * volumeFactor;
    ctx.beginPath();
    ctx.ellipse(centerX, centerY - 5, 88 * volumeFactor, 106 * volumeFactor, 0, 0, Math.PI * 2);
    ctx.stroke();
    
    // 2. Cerebrospinal Fluid (CSF) buffer space (darker ring inside skull)
    ctx.fillStyle = "#0c1524";
    ctx.beginPath();
    ctx.ellipse(centerX, centerY - 5, 84 * volumeFactor, 102 * volumeFactor, 0, 0, Math.PI * 2);
    ctx.fill();
    
    // 3. Draw Cortical Outline with complex folding convolutions
    ctx.fillStyle = "#334155"; // Gray matter cortex
    ctx.beginPath();
    
    const steps = 180;
    const baseRx = 80 * volumeFactor;
    const baseRy = 98 * volumeFactor;
    
    for (let i = 0; i <= steps; i++) {
      const angle = (i * 2 * Math.PI) / steps;
      // Procedural fold pattern based on sine waves
      const ripple = Math.sin(angle * 28) * 2.8 * volumeFactor + Math.cos(angle * 14) * 1.5 * volumeFactor;
      const rx = baseRx + ripple;
      const ry = baseRy + ripple;
      
      const x = centerX + Math.cos(angle) * rx;
      const y = centerY - 5 + Math.sin(angle) * ry;
      
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.closePath();
    ctx.fill();
    
    // 4. White Matter inner contour (slightly lighter gray matter)
    ctx.fillStyle = "#475569";
    ctx.beginPath();
    const wmRx = 68 * volumeFactor;
    const wmRy = 84 * volumeFactor;
    for (let i = 0; i <= steps; i++) {
      const angle = (i * 2 * Math.PI) / steps;
      const ripple = Math.sin(angle * 20) * 1.8 * volumeFactor;
      const x = centerX + Math.cos(angle) * (wmRx + ripple);
      const y = centerY - 5 + Math.sin(angle) * (wmRy + ripple);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.closePath();
    ctx.fill();
    
    // 5. Draw Lateral Ventricles (CSF - black space in core of brain)
    // Slices 25-70 have ventricles visible
    if (sliceIndex > 20 && sliceIndex < 75) {
      ctx.fillStyle = "#020617";
      
      const ventH = 14 * volumeFactor * ventricleEnlargeFactor;
      const ventW = 5 * volumeFactor * ventricleEnlargeFactor;
      const ventOffset = 10 * volumeFactor;
      
      // Left ventricle horn shape
      ctx.beginPath();
      ctx.ellipse(centerX - ventOffset, centerY - 10 * volumeFactor, ventW, ventH, -0.15, 0, Math.PI * 2);
      ctx.fill();
      
      // Right ventricle horn shape
      ctx.beginPath();
      ctx.ellipse(centerX + ventOffset, centerY - 10 * volumeFactor, ventW, ventH, 0.15, 0, Math.PI * 2);
      ctx.fill();
    }
    
    // 6. Hippocampal Temporal regions (Symmetrical bottom gray structures)
    if (sliceIndex > 35 && sliceIndex < 60) {
      const hippoSize = 8 * volumeFactor * hippocampusAtrophyFactor;
      
      ctx.fillStyle = isHighRisk ? "#64748b" : "#475569"; // Normal vs atrophic shading
      ctx.beginPath();
      ctx.arc(centerX - 24 * volumeFactor, centerY + 24 * volumeFactor, hippoSize, 0, Math.PI * 2);
      ctx.arc(centerX + 24 * volumeFactor, centerY + 24 * volumeFactor, hippoSize, 0, Math.PI * 2);
      ctx.fill();
      
      // Highlight Hippocampus Region on scan in Scan Explorer
      if (isHighRisk) {
        ctx.strokeStyle = "rgba(239, 68, 68, 0.6)"; // glowing coral ring
        ctx.lineWidth = 1.5;
        ctx.setLineDash([3, 3]);
        
        ctx.beginPath();
        ctx.arc(centerX - 24 * volumeFactor, centerY + 24 * volumeFactor, hippoSize + 6, 0, Math.PI * 2);
        ctx.stroke();
        
        ctx.beginPath();
        ctx.arc(centerX + 24 * volumeFactor, centerY + 24 * volumeFactor, hippoSize + 6, 0, Math.PI * 2);
        ctx.stroke();
        ctx.setLineDash([]);
        
        // Add label text inside canvas
        ctx.fillStyle = "rgba(239, 68, 68, 0.9)";
        ctx.font = "8px Inter, sans-serif";
        ctx.textAlign = "center";
        ctx.fillText("BILATERAL HIPPOCAMPAL REGION ATROPHY", centerX, centerY + 54 * volumeFactor);
      }
    }
    
  } else if (plane === 'Coronal') {
    // 1. Draw Skull boundary
    ctx.strokeStyle = "#1e293b";
    ctx.lineWidth = 4 * volumeFactor;
    ctx.beginPath();
    ctx.ellipse(centerX, centerY - 5, 92 * volumeFactor, 92 * volumeFactor, 0, 0, Math.PI * 2);
    ctx.stroke();
    
    // 2. CSF space
    ctx.fillStyle = "#0c1524";
    ctx.beginPath();
    ctx.ellipse(centerX, centerY - 5, 88 * volumeFactor, 88 * volumeFactor, 0, 0, Math.PI * 2);
    ctx.fill();
    
    // 3. Cortical Outlines (Coronal slice has double lobed "butterfly" shape)
    ctx.fillStyle = "#334155";
    ctx.beginPath();
    
    const steps = 180;
    const baseR = 76 * volumeFactor;
    for (let i = 0; i <= steps; i++) {
      const angle = (i * 2 * Math.PI) / steps;
      // Add indentation at top and bottom to create bilateral lobe hemisphere division
      const indent = Math.pow(Math.abs(Math.sin(angle)), 1.5) * 8 * volumeFactor;
      const ripple = Math.sin(angle * 24) * 2.5 * volumeFactor;
      const r = baseR - indent + ripple;
      
      const x = centerX + Math.cos(angle) * r;
      const y = centerY - 5 + Math.sin(angle) * r;
      
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.closePath();
    ctx.fill();
    
    // 4. Inner White Matter
    ctx.fillStyle = "#475569";
    ctx.beginPath();
    const wmR = 64 * volumeFactor;
    for (let i = 0; i <= steps; i++) {
      const angle = (i * 2 * Math.PI) / steps;
      const indent = Math.pow(Math.abs(Math.sin(angle)), 1.5) * 6 * volumeFactor;
      const ripple = Math.sin(angle * 18) * 1.5 * volumeFactor;
      const r = wmR - indent + ripple;
      
      const x = centerX + Math.cos(angle) * r;
      const y = centerY - 5 + Math.sin(angle) * r;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.closePath();
    ctx.fill();
    
    // 5. Ventricles (Inverted butterfly / V shaped slit in center)
    if (sliceIndex > 25 && sliceIndex < 70) {
      ctx.fillStyle = "#020617";
      
      const vSize = 12 * volumeFactor * ventricleEnlargeFactor;
      const vOffset = 6 * volumeFactor;
      
      ctx.beginPath();
      ctx.ellipse(centerX - vOffset, centerY - 14 * volumeFactor, 4 * volumeFactor * ventricleEnlargeFactor, vSize, -0.2, 0, Math.PI * 2);
      ctx.ellipse(centerX + vOffset, centerY - 14 * volumeFactor, 4 * volumeFactor * ventricleEnlargeFactor, vSize, 0.2, 0, Math.PI * 2);
      ctx.fill();
    }
    
    // 6. Lower Hippocampal structures
    if (sliceIndex > 40 && sliceIndex < 60) {
      const hSize = 7 * volumeFactor * hippocampusAtrophyFactor;
      ctx.fillStyle = isHighRisk ? "#64748b" : "#475569";
      
      ctx.beginPath();
      ctx.ellipse(centerX - 18 * volumeFactor, centerY + 18 * volumeFactor, hSize * 1.2, hSize * 0.8, -0.4, 0, Math.PI * 2);
      ctx.ellipse(centerX + 18 * volumeFactor, centerY + 18 * volumeFactor, hSize * 1.2, hSize * 0.8, 0.4, 0, Math.PI * 2);
      ctx.fill();
    }
    
  } else if (plane === 'Sagittal') {
    // 1. Draw Skull boundary (side profile: back-of-head, nose projection)
    ctx.strokeStyle = "#1e293b";
    ctx.lineWidth = 4 * volumeFactor;
    ctx.beginPath();
    ctx.ellipse(centerX - 10 * volumeFactor, centerY - 5, 102 * volumeFactor, 92 * volumeFactor, 0, 0, Math.PI * 2);
    ctx.stroke();
    
    // 2. CSF space
    ctx.fillStyle = "#0c1524";
    ctx.beginPath();
    ctx.ellipse(centerX - 10 * volumeFactor, centerY - 5, 96 * volumeFactor, 86 * volumeFactor, 0, 0, Math.PI * 2);
    ctx.fill();
    
    // 3. Cerebral hemisphere cortex shape
    ctx.fillStyle = "#334155";
    ctx.beginPath();
    const steps = 180;
    const baseRx = 84 * volumeFactor;
    const baseRy = 74 * volumeFactor;
    
    for (let i = 0; i <= steps; i++) {
      const angle = (i * 2 * Math.PI) / steps;
      // Add asymmetry (back of brain is fuller, bottom is flatter)
      const asymmetry = (Math.cos(angle) > 0) ? (Math.sin(angle) * 8 * volumeFactor) : 0;
      const ripple = Math.sin(angle * 26) * 2.2 * volumeFactor;
      
      const x = centerX - 10 * volumeFactor + Math.cos(angle) * baseRx + ripple;
      const y = centerY - 12 * volumeFactor + Math.sin(angle) * (baseRy + asymmetry) + ripple;
      
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.closePath();
    ctx.fill();
    
    // 4. White matter
    ctx.fillStyle = "#475569";
    ctx.beginPath();
    const wmRx = 70 * volumeFactor;
    const wmRy = 60 * volumeFactor;
    for (let i = 0; i <= steps; i++) {
      const angle = (i * 2 * Math.PI) / steps;
      const asymmetry = (Math.cos(angle) > 0) ? (Math.sin(angle) * 6 * volumeFactor) : 0;
      const ripple = Math.sin(angle * 18) * 1.5 * volumeFactor;
      const x = centerX - 10 * volumeFactor + Math.cos(angle) * wmRx + ripple;
      const y = centerY - 12 * volumeFactor + Math.sin(angle) * (wmRy + asymmetry) + ripple;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.closePath();
    ctx.fill();
    
    // 5. Draw Cerebellum (Small circular structure at lower rear right)
    ctx.fillStyle = "#334155";
    ctx.beginPath();
    ctx.ellipse(centerX - 35 * volumeFactor, centerY + 42 * volumeFactor, 26 * volumeFactor, 18 * volumeFactor, 0.2, 0, Math.PI * 2);
    ctx.fill();
    
    // Cerebellum fine internal layers stripes (Arbor Vitae)
    ctx.strokeStyle = "#475569";
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    for (let i = -14; i <= 14; i += 6) {
      ctx.arc(centerX - 35 * volumeFactor, centerY + 42 * volumeFactor + i, 16 * volumeFactor, 0, Math.PI, true);
    }
    ctx.stroke();
    
    // 6. Draw Brainstem (thick vertical trunk descending in center-bottom)
    ctx.fillStyle = "#475569";
    ctx.beginPath();
    ctx.moveTo(centerX - 14 * volumeFactor, centerY + 20 * volumeFactor);
    ctx.quadraticCurveTo(centerX - 4 * volumeFactor, centerY + 58 * volumeFactor, centerX - 4 * volumeFactor, centerY + 78 * volumeFactor);
    ctx.lineTo(centerX + 16 * volumeFactor, centerY + 78 * volumeFactor);
    ctx.quadraticCurveTo(centerX + 12 * volumeFactor, centerY + 58 * volumeFactor, centerX + 10 * volumeFactor, centerY + 20 * volumeFactor);
    ctx.closePath();
    ctx.fill();
    
    // 7. Lateral Ventricle (CSF core space - elegant C-loop in center)
    if (sliceIndex > 30 && sliceIndex < 65) {
      ctx.strokeStyle = "#020617";
      ctx.lineWidth = 8 * volumeFactor * ventricleEnlargeFactor;
      ctx.lineCap = "round";
      ctx.beginPath();
      // Draw standard C-loop ventricle shape
      ctx.arc(centerX - 10 * volumeFactor, centerY - 6 * volumeFactor, 22 * volumeFactor, 0.7 * Math.PI, 1.9 * Math.PI, false);
      ctx.stroke();
    }
  }
  
  // 7. Add beautiful crosshair and slice indicators
  ctx.strokeStyle = "rgba(59, 130, 246, 0.25)";
  ctx.lineWidth = 1;
  ctx.beginPath();
  // Draw light indicator tick marks at the borders
  ctx.moveTo(centerX, 0); ctx.lineTo(centerX, 10);
  ctx.moveTo(centerX, height); ctx.lineTo(centerX, height - 10);
  ctx.moveTo(0, centerY); ctx.lineTo(10, centerY);
  ctx.moveTo(width, centerY); ctx.lineTo(width - 10, centerY);
  ctx.stroke();
  
  // Draw slice index label text top-left corner
  ctx.fillStyle = "rgba(148, 163, 184, 0.6)";
  ctx.font = "10px Inter, sans-serif";
  ctx.textAlign = "left";
  ctx.fillText(`INDEX: ${sliceIndex}`, 14, 20);
}

// ── 9. Longitudinal Page Controls & Table Population ─────
function initLongitudinalControls() {
  // Toggle metrics lines
  const metricToggles = document.querySelectorAll(".metric-toggle");
  metricToggles.forEach(btn => {
    btn.addEventListener("click", () => {
      const metric = btn.getAttribute("data-metric");
      const idx = state.selectedMetrics.indexOf(metric);
      
      if (idx > -1) {
        // Don't allow removing if it is the only one selected
        if (state.selectedMetrics.length > 1) {
          state.selectedMetrics.splice(idx, 1);
          btn.classList.remove("active");
        }
      } else {
        state.selectedMetrics.push(metric);
        btn.classList.add("active");
      }
      
      renderLongitudinalChart();
    });
  });

  // Range button selector (3, 6, 12 visits)
  const rangeBtns = document.querySelectorAll(".range-btn");
  rangeBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      rangeBtns.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      
      state.activeVisitsCount = parseInt(btn.getAttribute("data-range"));
      
      // Update both charts
      renderTrendChart();
      renderLongitudinalChart();
      populateMetricsTable();
    });
  });
}

function populateMetricsTable() {
  const tableBody = document.querySelector("#metricsTable tbody");
  if (!tableBody) return;
  
  const patient = patients[state.activePatient];
  const visits = patient.trend.slice(0, state.activeVisitsCount);
  
  tableBody.innerHTML = "";
  
  visits.forEach((vt, idx) => {
    const row = document.createElement("tr");
    
    // Calculate risk delta
    let deltaStr = "—";
    let deltaClass = "";
    if (idx > 0) {
      const diff = vt.risk - visits[idx - 1].risk;
      if (diff > 0) {
        deltaStr = `▲ +${diff.toFixed(2)}`;
        deltaClass = "down"; // Higher risk is medically unfavorable (red)
      } else if (diff < 0) {
        deltaStr = `▼ ${diff.toFixed(2)}`;
        deltaClass = "up";
      } else {
        deltaStr = `■ 0.00`;
      }
    }
    
    row.innerHTML = `
      <td><strong>Visit ${vt.visit}</strong></td>
      <td>${vt.date}</td>
      <td><span style="font-weight:600; color:${vt.risk >= 0.70 ? 'var(--danger)' : 'var(--text)'}">${vt.risk.toFixed(2)}</span></td>
      <td>${vt.hippo.toFixed(2)} cm³</td>
      <td>${vt.mmse} / 30</td>
      <td><span class="trend ${deltaClass}">${deltaStr}</span></td>
    `;
    
    tableBody.appendChild(row);
  });
}

// ── 10. Multi-Series Longitudinal Trend Chart ────────────
function renderLongitudinalChart() {
  const canvas = document.getElementById("longChart");
  if (!canvas || state.activePage !== 'longitudinal') return;

  const patient = patients[state.activePatient];
  const visits = patient.trend.slice(0, state.activeVisitsCount);
  
  // Setup HDPI scaling
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  canvas.width = rect.width * dpr;
  canvas.height = 280 * dpr;
  canvas.style.height = '280px';
  
  const ctx = canvas.getContext("2d");
  ctx.scale(dpr, dpr);
  
  const width = rect.width;
  const height = 280;
  const paddingLeft = 45;
  const paddingRight = 45; // Margin on right for secondary axis
  const paddingTop = 30;
  const paddingBottom = 35;
  
  const chartW = width - paddingLeft - paddingRight;
  const chartH = height - paddingTop - paddingBottom;
  
  ctx.clearRect(0, 0, width, height);
  
  // Draw Grid Lines
  const yLines = 5;
  ctx.strokeStyle = "rgba(148, 163, 184, 0.05)";
  ctx.lineWidth = 1;
  for (let i = 0; i < yLines; i++) {
    const y = paddingTop + (i * chartH) / (yLines - 1);
    ctx.beginPath();
    ctx.moveTo(paddingLeft, y);
    ctx.lineTo(width - paddingRight, y);
    ctx.stroke();
  }
  
  // Metric configurations
  const config = {
    risk: {
      color: "#3b82f6",
      label: "Risk Score",
      min: 0.0,
      max: 1.0,
      format: v => v.toFixed(2),
      points: visits.map((pt, idx) => ({
        x: paddingLeft + (idx * chartW) / (visits.length - 1),
        y: paddingTop + chartH - ((pt.risk - 0.0) / 1.0) * chartH,
        val: pt.risk,
        label: "Risk Score"
      }))
    },
    hippo: {
      color: "#10b981",
      label: "Hippo Vol (cm³)",
      min: 4.0,
      max: 8.0,
      format: v => `${v.toFixed(1)} cm³`,
      points: visits.map((pt, idx) => ({
        x: paddingLeft + (idx * chartW) / (visits.length - 1),
        y: paddingTop + chartH - ((pt.hippo - 4.0) / 4.0) * chartH,
        val: pt.hippo,
        label: "Hippo. Vol"
      }))
    },
    mmse: {
      color: "#f59e0b",
      label: "MMSE Score",
      min: 15,
      max: 30,
      format: v => `${Math.round(v)} pts`,
      points: visits.map((pt, idx) => ({
        x: paddingLeft + (idx * chartW) / (visits.length - 1),
        y: paddingTop + chartH - ((pt.mmse - 15) / 15) * chartH,
        val: pt.mmse,
        label: "MMSE Score"
      }))
    }
  };
  
  // 1. Draw Left Y-Axis labels (Primary: Risk & MMSE)
  ctx.fillStyle = "rgba(148, 163, 184, 0.5)";
  ctx.font = "9px Inter, sans-serif";
  ctx.textAlign = "right";
  ctx.textBaseline = "middle";
  for (let i = 0; i < yLines; i++) {
    const val = 1.0 - (i * 1.0) / (yLines - 1);
    const y = paddingTop + (i * chartH) / (yLines - 1);
    ctx.fillText(val.toFixed(1), paddingLeft - 10, y);
  }
  
  // 2. Draw Right Y-Axis labels (Secondary: Hippocampal Volume 4.0 to 8.0 cm³)
  if (state.selectedMetrics.includes("hippo")) {
    ctx.fillStyle = "#10b981";
    ctx.textAlign = "left";
    for (let i = 0; i < yLines; i++) {
      const val = 8.0 - (i * 4.0) / (yLines - 1);
      const y = paddingTop + (i * chartH) / (yLines - 1);
      ctx.fillText(`${val.toFixed(1)}`, width - paddingRight + 10, y);
    }
  }
  
  // 3. Draw Curves & Area for Active Metrics
  state.selectedMetrics.forEach(metricKey => {
    const met = config[metricKey];
    const pts = met.points;
    if (pts.length < 2) return;
    
    // Draw line curve
    ctx.strokeStyle = met.color;
    ctx.lineWidth = 3;
    ctx.lineCap = "round";
    ctx.beginPath();
    ctx.moveTo(pts[0].x, pts[0].y);
    
    for (let i = 0; i < pts.length - 1; i++) {
      const p0 = pts[i];
      const p1 = pts[i + 1];
      const cpX1 = p0.x + (p1.x - p0.x) / 2;
      const cpY1 = p0.y;
      const cpX2 = p0.x + (p1.x - p0.x) / 2;
      const cpY2 = p1.y;
      ctx.bezierCurveTo(cpX1, cpY1, cpX2, cpY2, p1.x, p1.y);
    }
    ctx.stroke();
    
    // Draw dots
    pts.forEach(pt => {
      ctx.beginPath();
      ctx.arc(pt.x, pt.y, 4.5, 0, Math.PI * 2);
      ctx.fillStyle = "#0c1829";
      ctx.fill();
      ctx.strokeStyle = met.color;
      ctx.lineWidth = 2;
      ctx.stroke();
    });
  });
  
  // 4. Draw X-Axis labels
  ctx.fillStyle = "rgba(148, 163, 184, 0.5)";
  ctx.font = "9px Inter, sans-serif";
  ctx.textAlign = "center";
  visits.forEach((vt, idx) => {
    const x = paddingLeft + (idx * chartW) / (visits.length - 1);
    ctx.fillText(`V${vt.visit}`, x, paddingTop + chartH + 18);
    
    ctx.fillStyle = "rgba(148, 163, 184, 0.35)";
    ctx.fillText(vt.date.substring(2), x, paddingTop + chartH + 30);
    ctx.fillStyle = "rgba(148, 163, 184, 0.5)";
  });
}

// ── 11. Reports Page Content Generation ──────────────────
function renderClinicalReport(patient) {
  // 1. Report Header Date
  const dateEl = document.getElementById("reportDate");
  if (dateEl) dateEl.textContent = `Acquisition Date: ${patient.acquisitionDate} · Generated: ${new Date().toLocaleDateString()}`;
  
  // 2. Key Findings list
  const findingsList = document.getElementById("findingsList");
  if (findingsList) {
    findingsList.innerHTML = "";
    patient.findings.forEach(fin => {
      const item = document.createElement("div");
      item.className = `finding-item severity-${fin.severity}`;
      
      let severityBadgeColor = "var(--success)";
      if (fin.severity === 'high') severityBadgeColor = "var(--danger)";
      else if (fin.severity === 'medium') severityBadgeColor = "var(--warning)";
      
      item.innerHTML = `
        <svg class="finding-icon" style="color:${severityBadgeColor}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
        <div>
          <span style="font-weight:700; text-transform:uppercase; font-size:10px; color:${severityBadgeColor}; margin-right:6px;">${fin.severity}</span>
          ${fin.text}
        </div>
      `;
      findingsList.appendChild(item);
    });
  }
  
  // 3. Clinical recommendation paragraph
  const recBox = document.getElementById("recommendationBox");
  if (recBox) {
    recBox.querySelector("p").innerHTML = `<strong>RECOMMENDED CLINICAL ACTION:</strong> ${patient.recommendations}`;
  }
  
  // 4. Report Summary KPI Metrics
  const reportMetrics = document.getElementById("reportMetrics");
  if (reportMetrics) {
    let riskColor = "var(--success)";
    if (patient.risk >= 0.70) riskColor = "var(--danger)";
    else if (patient.risk >= 0.40) riskColor = "var(--warning)";
    
    reportMetrics.innerHTML = `
      <div class="kpi glass" style="padding:var(--sp-3) var(--sp-4);">
        <div class="kpi-info">
          <span class="kpi-label">Risk Signal</span>
          <span class="kpi-value" style="color:${riskColor}">${patient.risk.toFixed(2)}</span>
        </div>
      </div>
      <div class="kpi glass" style="padding:var(--sp-3) var(--sp-4);">
        <div class="kpi-info">
          <span class="kpi-label">Hippocampal Vol.</span>
          <span class="kpi-value">${patient.hippocampalVolume.toFixed(2)} cm³</span>
        </div>
      </div>
      <div class="kpi glass" style="padding:var(--sp-3) var(--sp-4);">
        <div class="kpi-info">
          <span class="kpi-label">Cognitive MMSE</span>
          <span class="kpi-value">${patient.mmse} / 30</span>
        </div>
      </div>
    `;
  }
}

// ── 12. Run New Analysis Pipeline Simulation ─────────────
function initAnalysisSimulation() {
  const analyzeBtn = document.getElementById("analyzeBtn");
  if (!analyzeBtn) return;
  
  analyzeBtn.addEventListener("click", () => {
    // 1. Enter button loading state
    analyzeBtn.classList.add("loading");
    analyzeBtn.disabled = true;
    
    const originalContent = analyzeBtn.innerHTML;
    analyzeBtn.innerHTML = `<span class="spinner"></span> Analyzing Scan...`;
    
    // 2. Add skeleton shimmers on Overview page elements to simulate data loading
    const cards = document.querySelectorAll(".kpi");
    const chart = document.getElementById("trendChart");
    const explainList = document.getElementById("featureList");
    
    cards.forEach(c => c.classList.add("skeleton"));
    if (chart) chart.style.opacity = "0.3";
    if (explainList) explainList.style.opacity = "0.3";
    
    // 3. Run Pipeline ML delay simulation (~1800ms)
    setTimeout(() => {
      // Restore buttons & clean shimmers
      analyzeBtn.classList.remove("loading");
      analyzeBtn.disabled = false;
      analyzeBtn.innerHTML = originalContent;
      
      cards.forEach(c => c.classList.remove("skeleton"));
      if (chart) chart.style.opacity = "1";
      if (explainList) explainList.style.opacity = "1";
      
      // Mutate current active patient data slightly to represent new diagnostic sequence run
      const activePatientData = patients[state.activePatient];
      
      // Jitter risk and hippocampal slightly
      const randomShift = (Math.random() * 0.08 - 0.03); // slight fluctuation
      activePatientData.risk = Math.max(0.05, Math.min(0.98, activePatientData.risk + randomShift));
      activePatientData.hippocampalVolume = Math.max(3.8, Math.min(8.5, activePatientData.hippocampalVolume - (randomShift * 3)));
      activePatientData.confidence = Math.round(Math.max(68, Math.min(99, activePatientData.confidence + (Math.random() * 6 - 3))));
      
      // Add a simulated new visit to trend array
      const lastVisit = activePatientData.trend.at(-1);
      const nextVisitNum = lastVisit.visit + 1;
      const date = new Date();
      date.setMonth(date.getMonth() + 6);
      const dateString = date.toISOString().split('T')[0];
      
      activePatientData.trend.push({
        visit: nextVisitNum,
        date: dateString,
        risk: activePatientData.risk,
        hippo: activePatientData.hippocampalVolume,
        mmse: Math.max(15, Math.min(30, activePatientData.mmse - Math.round(randomShift * 10)))
      });
      
      // Re-trigger global render
      triggerFullRender();
      
      // Play brief high-tech beep/flash indication
      const pulseDot = document.querySelector(".pulse-dot");
      if (pulseDot) {
        pulseDot.style.background = "#10b981";
        pulseDot.style.boxShadow = "0 0 12px #10b981";
        setTimeout(() => {
          pulseDot.style.background = "var(--accent)";
          pulseDot.style.boxShadow = "0 0 8px var(--accent)";
        }, 1500);
      }
      
    }, 1800);
  });
}

// ── 13. PDF Report Export Action ─────────────────────────
function initReportExport() {
  const exportBtn = document.getElementById("exportBtn");
  if (!exportBtn) return;
  
  exportBtn.addEventListener("click", () => {
    // Show a premium glass loader dialogue overlay while building clinical PDF
    const loaderOverlay = document.createElement("div");
    loaderOverlay.style.position = "fixed";
    loaderOverlay.style.inset = "0";
    loaderOverlay.style.background = "rgba(6, 13, 26, 0.9)";
    loaderOverlay.style.backdropFilter = "blur(20px)";
    loaderOverlay.style.display = "grid";
    loaderOverlay.style.placeItems = "center";
    loaderOverlay.style.zIndex = "1000";
    loaderOverlay.style.opacity = "0";
    loaderOverlay.style.transition = "opacity var(--dur-normal) var(--ease-smooth)";
    
    loaderOverlay.innerHTML = `
      <div class="glass" style="padding: var(--sp-6) var(--sp-8); text-align: center; max-width: 400px; width: 90%;">
        <span class="spinner" style="width:32px; height:32px; border-width:3px; margin: 0 auto var(--sp-4) auto; border-top-color: var(--primary);"></span>
        <h3 style="font-size: var(--text-md); font-weight:600; margin-bottom: var(--sp-2)">Compiling Medical Records</h3>
        <p style="font-size: var(--text-xs); color: var(--text-muted); line-height: 1.5">Extracting voxel morphometry vectors, temporal thickness indices, and explainability heatmaps for ${state.activePatient}...</p>
        <div class="bar" style="height: 4px; margin-top: var(--sp-4);"><span style="width:0%; background:var(--primary);"></span></div>
      </div>
    `;
    
    document.body.appendChild(loaderOverlay);
    
    // Animate opacity in
    setTimeout(() => {
      loaderOverlay.style.opacity = "1";
      // Animate progress loader bar
      const barSpan = loaderOverlay.querySelector(".bar span");
      if (barSpan) {
        barSpan.style.transition = "width 1.2s ease-in-out";
        barSpan.style.width = "100%";
      }
    }, 50);
    
    // Complete compile after 1500ms and trigger system print / download prompt
    setTimeout(() => {
      loaderOverlay.style.opacity = "0";
      setTimeout(() => {
        loaderOverlay.remove();
        // Trigger print view which handles PDF saving organically
        window.print();
      }, 300);
    }, 1600);
  });
}

// ── 14. Trigger Full Component Render Cycle ──────────────
function triggerFullRender() {
  const patient = patients[state.activePatient];
  
  // 1. Update Top level KPI cards
  updateKPIGauges(patient);
  
  // 2. Redraw Overview trend line canvas
  renderTrendChart();
  
  // 3. Render features attributions
  renderExplainability(patient);
  
  // 4. Update Longitudinal page data and grid table
  populateMetricsTable();
  renderLongitudinalChart();
  
  // 5. Build Reports Page details
  renderClinicalReport(patient);
  
  // 6. Draw scan explorer canvases (if active)
  if (state.activePage === 'scan-explorer') {
    renderAllMRIPlanes();
  }
}
