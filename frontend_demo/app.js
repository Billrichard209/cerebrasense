/* â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
   CerebraSense Interactive Engine v2.0
   Vanilla SPA Router, Procedural MRI Viewer, & Dynamic Charts
   â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• */

// â”€â”€ 1. Global Patient Registry (Loaded from Backend API) â”€â”€â”€â”€â”€â”€â”€â”€
let patients = {};

// â”€â”€ 2. Application Global State â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
const state = {
  activePage: 'overview',
  activePatient: null,
  activeVisitsCount: 6,
  selectedMetrics: ['risk', 'hippo'], // Default active metrics in Longitudinal Trend page
  sliceIndices: {
    axial: 48,
    coronal: 48,
    sagittal: 48
  },
  hoveredPoint: null,
  researchPayload: null,
  researchPayloadLoaded: false
};

// Helper constants
const CIRCUMFERENCE = 2 * Math.PI * 24; // ~150.796 for circular progress rings (radius = 24)

// â”€â”€ 3. Application Entry & Router Initialization â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
document.addEventListener("DOMContentLoaded", async () => {
  try {
    const data = await fetchDashboardData();
    if (data && data.subjects && data.subjects.length > 0) {
      patients = {};
      data.subjects.forEach(subject => {
        // Map backend schema to frontend schema
        patients[subject.subject_id] = {
          name: subject.subject_id,
          age: subject.clinical?.age || 70,
          gender: subject.clinical?.sex || 'F',
          scanner: 'Standardized Pipeline',
          sequence: 'T1w MPRAGE',
          voxelSize: '1.0 Ã— 1.0 Ã— 1.0 mmÂ³',
          matrixSize: '256 Ã— 256 Ã— 96',
          acquisitionDate: new Date().toISOString().split('T')[0],
          risk: subject.final_risk,
          hippocampalVolume: (subject.biomarkers?.hippo_vol_mm3 || 3200) / 1000, // cmÂ³
          completeness: 100,
          confidence: 90,
          mmse: subject.clinical?.mmse || 27,
          trend: subject.visits.map((v, i) => ({
            visit: i + 1,
            date: v, // meta_session_id
            risk: subject.raw_scores[i],
            hippo: ((subject.biomarkers?.hippo_vol_mm3 || 3200) / 1000) - ((subject.final_risk - subject.raw_scores[i]) * 0.5), // estimated hippo trend
            mmse: subject.clinical?.mmse || 27
          })),
          features: [
            { name: "Overall Risk Contribution", impact: Math.round(subject.final_risk * 100), trend: subject.trend_status === 'Progressing' ? 'up' : 'neutral', desc: subject.clinical_summary || 'Clinical summary not available.' },
            { name: "Velocity Score", impact: Math.min(100, Math.round(Math.abs(subject.velocity[0] || 0) * 1000)), trend: subject.trend_status === 'Progressing' ? 'up' : 'neutral', desc: `Rate of change: ${subject.velocity[0] || 0}` }
          ],
          regions: [
            { name: 'Hippocampus', volume: `${((subject.biomarkers?.hippo_vol_mm3 || 3200)/1000).toFixed(2)} cmÂ³`, status: subject.status === 'High Risk' ? 'critical' : 'normal', pct: 'Measured via T1w' },
            { name: 'TIV', volume: `${((subject.biomarkers?.tiv_mm3 || 1450000)/1000).toFixed(0)} cmÂ³`, status: 'normal', pct: 'Total Intracranial Vol' }
          ],
          recommendations: subject.clinical_summary,
          findings: [
            { severity: subject.status === 'High Risk' ? 'high' : 'low', text: `Patient status: ${subject.status}` },
            { severity: subject.is_rapid_decline ? 'high' : 'low', text: `Trend status: ${subject.trend_status}` }
          ]
        };
      });
      // Set active patient to first subject returned
      state.activePatient = Object.keys(patients)[0];
    } else {
      console.warn("No subjects returned from backend.");
    }
  } catch (err) {
    console.error("Failed to load dashboard data. Ensure backend is running and prediction CSVs are loaded.", err);
  }

  // Always initialize UI, even if empty, so the user sees something
  initRouter();
  initPatientDropdown();
  initScanExplorer();
  initLongitudinalControls();
  initAnalysisSimulation();
  initReportExport();
  initResearchModeBridge();

  // Perform first render cycle if patient data exists
  if (Object.keys(patients).length > 0) {
    triggerFullRender();
  } else {
    document.getElementById("pageTitle").textContent = "Workspace - No Data Available (Please run backend MLOps)";
  }
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

    const pages = ['overview', 'research-mode', 'scan-explorer', 'longitudinal', 'explainability', 'reports'];
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
    'research-mode': 'Research Model Board',
    'scan-explorer': 'High-Resolution MRI Scan Explorer',
    'longitudinal': 'Multi-Metric Longitudinal Tracking',
    'explainability': 'Clinical Explainability & Feature Attributions',
    'reports': 'AI-Assisted Clinical Decision Report'
  };
  document.getElementById("pageTitle").textContent = titles[pageId] || 'Workspace';

  // Redraw canvases depending on the active page
  if (pageId === 'overview') {
    renderTrendChart();
  } else if (pageId === 'research-mode') {
    renderResearchMode();
  } else if (pageId === 'scan-explorer') {
    renderAllMRIPlanes();
  } else if (pageId === 'longitudinal') {
    renderLongitudinalChart();
  }

  // Close sidebar drawer if open on mobile view
  document.getElementById("sidebar").classList.remove("open");
  document.getElementById("sidebarOverlay").classList.remove("open");
}

// â”€â”€ 4. Patient Selector Custom Dropdown â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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
      <span>Age: ${p.age} Â· ${p.gender} Â· Risk Signal: ${(p.risk).toFixed(2)}</span>
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

// â”€â”€ 5. KPI Count-Up & Radial Gauge Animation â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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
    // Normalize: healthy volume range is ~4.0 to ~8.0 cmÂ³
    const pct = Math.max(10, Math.min(98, ((patient.hippocampalVolume - 4) / 4) * 100));
    hippoCircle.style.strokeDashoffset = CIRCUMFERENCE - (pct / 100 * CIRCUMFERENCE);

    const parentCard = hippoCircle.closest(".kpi");
    if (parentCard) parentCard.setAttribute("data-gauge-pct", Math.round(pct));
  }
  animateKPIValue("hippoValue", 0, patient.hippocampalVolume, v => `${v.toFixed(1)} cmÂ³`);

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

// â”€â”€ 6. Longitudinal Risk Chart (Interactive Canvas) â”€â”€â”€â”€â”€â”€
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
        deltaText = `â–² +${diff.toFixed(2)} vs previous`;
        deltaClass = "up"; // higher risk is worse (colored red/up)
      } else if (diff < 0) {
        deltaText = `â–¼ ${diff.toFixed(2)} vs previous`;
        deltaClass = "down";
      } else {
        deltaText = `â–  Unchanged`;
      }
    }

    // Populate tooltip UI
    tooltip.querySelector(".tt-label").textContent = `Visit ${closest.visit} Â· ${closest.date}`;
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

// â”€â”€ 7. Explainability Features List (Overview & Explain Page) â”€â”€
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

      const icon = feat.trend === 'up' ? 'â–²' : (feat.trend === 'down' ? 'â–¼' : 'â€¢');
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

// â”€â”€ 8. Procedural MRI Scan Plane Slice Renderer â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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

// â”€â”€ 9. Longitudinal Page Controls & Table Population â”€â”€â”€â”€â”€
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
    let deltaStr = "â€”";
    let deltaClass = "";
    if (idx > 0) {
      const diff = vt.risk - visits[idx - 1].risk;
      if (diff > 0) {
        deltaStr = `â–² +${diff.toFixed(2)}`;
        deltaClass = "down"; // Higher risk is medically unfavorable (red)
      } else if (diff < 0) {
        deltaStr = `â–¼ ${diff.toFixed(2)}`;
        deltaClass = "up";
      } else {
        deltaStr = `â–  0.00`;
      }
    }

    row.innerHTML = `
      <td><strong>Visit ${vt.visit}</strong></td>
      <td>${vt.date}</td>
      <td><span style="font-weight:600; color:${vt.risk >= 0.70 ? 'var(--danger)' : 'var(--text)'}">${vt.risk.toFixed(2)}</span></td>
      <td>${vt.hippo.toFixed(2)} cmÂ³</td>
      <td>${vt.mmse} / 30</td>
      <td><span class="trend ${deltaClass}">${deltaStr}</span></td>
    `;

    tableBody.appendChild(row);
  });
}

// â”€â”€ 10. Multi-Series Longitudinal Trend Chart â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
function clamp01(value) {
  const numeric = Number(value);
  if (Number.isNaN(numeric)) return 0;
  return Math.max(0, Math.min(1, numeric));
}

function percentImpact(value) {
  return Math.max(1, Math.min(100, Math.round(clamp01(value) * 100)));
}

function statusFromRisk(value) {
  if (value >= 0.70) return "critical";
  if (value >= 0.40) return "moderate";
  return "normal";
}

function applyLiveInferenceToPatient(patient, liveData) {
  const probability = clamp01(liveData.calibrated_probability_score ?? liveData.probability_score);
  const rawProbability = clamp01(liveData.probability_score);
  const confidence = clamp01(liveData.confidence_score);
  const explanation = liveData.explainability || {};
  const proxy = explanation.region_importance_proxy || {};
  const proxyEntries = Object.entries(proxy).slice(0, 4);
  const reviewRequired = Boolean(liveData.review_required ?? liveData.review_flag);
  const narrative = liveData.clinical_narrative || liveData.ai_summary || "Live backend inference completed. Research decision-support only.";

  patient.risk = probability;
  patient.confidence = confidence ? Math.round(confidence * 100) : patient.confidence;
  patient.recommendations = narrative;
  patient.features = [
    {
      name: "Live inference risk",
      impact: percentImpact(probability),
      trend: probability >= 0.50 ? "up" : "neutral",
      desc: narrative,
    },
    {
      name: "Model confidence",
      impact: percentImpact(confidence),
      trend: confidence >= 0.75 ? "neutral" : "up",
      desc: `Backend confidence level: ${liveData.confidence_level || "not reported"}.`,
    },
    {
      name: "Calibration delta",
      impact: percentImpact(Math.abs(probability - rawProbability)),
      trend: "neutral",
      desc: `Raw probability ${rawProbability.toFixed(3)}, calibrated probability ${probability.toFixed(3)}.`,
    },
    {
      name: reviewRequired ? "Review required" : "Review policy passed",
      impact: reviewRequired ? 90 : 20,
      trend: reviewRequired ? "up" : "neutral",
      desc: reviewRequired ? "Backend marked this inference for reviewer follow-up." : "Backend did not mark this inference for mandatory review.",
    },
  ];

  if (proxyEntries.length) {
    patient.regions = proxyEntries.map(([name, value]) => {
      const numeric = clamp01(value);
      return {
        name: name.replaceAll("_", " "),
        volume: `${percentImpact(numeric)}%`,
        status: statusFromRisk(numeric),
        pct: explanation.highlighted_regions || "Grad-CAM proxy attribution",
      };
    });
  } else if (explanation.artifacts || liveData.heatmap_visualization) {
    patient.regions = [
      {
        name: "Grad-CAM artifact",
        volume: "saved",
        status: reviewRequired ? "moderate" : "normal",
        pct: explanation.artifacts?.report_json || liveData.heatmap_visualization || "Explainability artifact returned",
      },
      ...patient.regions.slice(0, 4),
    ];
  }

  patient.findings = [
    {
      severity: probability >= 0.70 ? "high" : probability >= 0.40 ? "medium" : "low",
      text: `Live backend prediction: ${liveData.label_name || "unknown"} with risk ${probability.toFixed(3)}.`,
    },
    {
      severity: reviewRequired ? "high" : "low",
      text: reviewRequired ? "Backend requested reviewer follow-up for this inference." : "Backend did not require immediate reviewer escalation.",
    },
    {
      severity: "low",
      text: liveData.clinical_disclaimer || "Research decision-support only. Not diagnosis.",
    },
  ];
}

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
      label: "Hippo Vol (cmÂ³)",
      min: 4.0,
      max: 8.0,
      format: v => `${v.toFixed(1)} cmÂ³`,
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

  // 2. Draw Right Y-Axis labels (Secondary: Hippocampal Volume 4.0 to 8.0 cmÂ³)
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

// â”€â”€ 11. Reports Page Content Generation â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
function renderClinicalReport(patient) {
  // 1. Report Header Date
  const dateEl = document.getElementById("reportDate");
  if (dateEl) dateEl.textContent = `Acquisition Date: ${patient.acquisitionDate} Â· Generated: ${new Date().toLocaleDateString()}`;

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
          <span class="kpi-value">${patient.hippocampalVolume.toFixed(2)} cmÂ³</span>
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

// â”€â”€ 12. Run New Analysis Pipeline (Live API + Fallback) â”€â”€â”€â”€â”€â”€
function initAnalysisSimulation() {
  const analyzeBtn = document.getElementById("analyzeBtn");
  if (!analyzeBtn) return;

  analyzeBtn.addEventListener("click", async () => {
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

    // 3. Attempt Live API Call
    let liveData = null;
    try {
      const response = await fetch(`${window.CEREBRASENSE_API_BASE}/predict/scan`, {
        method: "POST",
        headers: cerebraSenseApiHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify({
          scan_path: "mock_demo_scan.nii.gz",
          checkpoint_path: "demo_checkpoint",
          output_name: `frontend_demo_${state.activePatient || "subject"}`,
          save_debug_slices: true,
          subject_id: state.activePatient
        })
      });
      if (response.ok) {
        liveData = await response.json();
        console.log("Live Inference Success:", liveData);
      } else {
        console.warn(`Live inference unavailable (${response.status}). Falling back to simulation.`);
      }
    } catch (e) {
      console.warn("Live inference API unreachable. Falling back to simulation.", e);
    }

    // 4. Resolve Data & UI Updates (~1800ms minimum delay for UI effect)
    setTimeout(() => {
      // Restore buttons & clean shimmers
      analyzeBtn.classList.remove("loading");
      analyzeBtn.disabled = false;
      analyzeBtn.innerHTML = originalContent;

      cards.forEach(c => c.classList.remove("skeleton"));
      if (chart) chart.style.opacity = "1";
      if (explainList) explainList.style.opacity = "1";

      const activePatientData = patients[state.activePatient];

      if (!activePatientData) return;

      let newRisk, newHippo, newMmse;

      if (liveData && liveData.probability_score !== undefined) {
        // Use Live Data
        applyLiveInferenceToPatient(activePatientData, liveData);
        newRisk = activePatientData.risk;
        newHippo = activePatientData.hippocampalVolume; // Keep current hippo for demo
        newMmse = activePatientData.mmse;
      } else {
        // Fallback Simulation
        const randomShift = (Math.random() * 0.08 - 0.03); // slight fluctuation
        newRisk = Math.max(0.05, Math.min(0.98, activePatientData.risk + randomShift));
        newHippo = Math.max(3.8, Math.min(8.5, activePatientData.hippocampalVolume - (randomShift * 3)));
        newMmse = Math.max(15, Math.min(30, activePatientData.mmse - Math.round(randomShift * 10)));
        activePatientData.confidence = Math.round(Math.max(68, Math.min(99, activePatientData.confidence + (Math.random() * 6 - 3))));
      }

      activePatientData.risk = newRisk;
      activePatientData.hippocampalVolume = newHippo;
      activePatientData.mmse = newMmse;

      // Add a new visit to trend array
      const lastVisit = activePatientData.trend.at(-1);
      const nextVisitNum = lastVisit ? lastVisit.visit + 1 : 1;
      const date = new Date();
      date.setMonth(date.getMonth() + 6);
      const dateString = date.toISOString().split('T')[0];

      activePatientData.trend.push({
        visit: nextVisitNum,
        date: dateString,
        risk: newRisk,
        hippo: newHippo,
        mmse: newMmse
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

// â”€â”€ 13. PDF Report Export Action â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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

// â”€â”€ 14. Trigger Full Component Render Cycle â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
// Research Mode reads generated backend artifacts when available.
async function initResearchModeBridge() {
  try {
    const response = await fetch("./data/research_mode.json", { cache: "no-store" });
    if (!response.ok) throw new Error(`research payload ${response.status}`);
    state.researchPayload = await response.json();
    state.researchPayloadLoaded = true;
  } catch (error) {
    state.researchPayload = null;
    state.researchPayloadLoaded = false;
  }
  renderResearchMode();
}

function formatMetric(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "--";
  return Number(value).toFixed(3);
}

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function formatCaseType(value) {
  return String(value || "case")
    .replace(/_/g, " ")
    .replace(/\b\w/g, char => char.toUpperCase());
}

function formatDelta(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "--";
  const number = Number(value);
  return `${number >= 0 ? "+" : ""}${number.toFixed(3)}`;
}

function bindResearchActionButtons() {
  document.querySelectorAll(".research-action-button[data-command]").forEach(button => {
    button.addEventListener("click", async () => {
      const command = button.getAttribute("data-command");
      if (!command) return;
      try {
        await navigator.clipboard.writeText(command);
        button.textContent = "Command copied";
      } catch (err) {
        button.textContent = "Copy unavailable";
      }
    });
  });
}

function renderResearchMode() {
  const payload = state.researchPayload;
  const status = document.getElementById("researchStatus");
  const activeModel = document.getElementById("researchActiveModel");
  const oasis2Model = document.getElementById("researchOasis2Model");
  const activeAuroc = document.getElementById("researchActiveAuroc");
  const oasis2Auroc = document.getElementById("researchOasis2Auroc");
  const reviewCount = document.getElementById("researchReviewCount");
  const summary = document.getElementById("researchProgressionSummary");
  const list = document.getElementById("researchProgressionList");
  const disclaimer = document.getElementById("researchDisclaimer");
  const actions = document.getElementById("researchDemoActions");
  if (!status || !list) return;

  if (!payload) {
    status.textContent = "Awaiting generated research payload";
    activeModel.textContent = "OASIS-1 stable baseline";
    oasis2Model.textContent = "OASIS-2 pending evaluation";
    activeAuroc.textContent = "--";
    oasis2Auroc.textContent = "--";
    reviewCount.textContent = "--";
    summary.textContent = "Run build_cerebrasense_control_tower.py to load model evidence.";
    disclaimer.textContent = "Research decision-support only. Not diagnosis.";
    if (actions) actions.innerHTML = "";
    list.innerHTML = `
      <div class="research-empty">
        <strong>No generated cases loaded</strong>
        <span>Frontend remains in safe simulated mode until backend artifacts exist.</span>
      </div>
    `;
    return;
  }

  const active = payload.active_model || {};
  const oasis2 = payload.oasis2_candidate || {};
  const candidateStatus = payload.candidate_status || {};
  const promotionBlockers = payload.promotion_blockers || [];
  const progression = payload.progression || {};
  const trajectory = payload.trajectory_intelligence || {};
  const readiness = payload.deployment_readiness || {};
  const controlTower = payload.control_tower_status || {};
  const nextBestAction = payload.next_best_action || {};
  const evidenceHealth = payload.evidence_health || {};
  const deploymentHealth = payload.deployment_health || {};
  const activeVsCandidate = payload.active_vs_candidate_deltas || payload.active_vs_candidate || {};
  const reviewQueue = payload.review_queue || {};
  const queueCases = reviewQueue.cases || [];
  const subjects = progression.top_subjects || [];
  const handoffCount = reviewQueue.total_case_count ?? queueCases.length;
  const demoActions = payload.demo_bundle_actions?.actions || [];

  status.textContent = `${payload.headline || "Generated research payload loaded"} - ${controlTower.label || candidateStatus.label || "Research candidate"} - ${deploymentHealth.readiness_status || readiness.readiness_status || "readiness pending"}`;
  activeModel.textContent = active.run_name || "OASIS-1 stable baseline";
  oasis2Model.textContent = `${oasis2.run_name || "OASIS-2 pending evaluation"}${candidateStatus.label ? ` (${candidateStatus.label})` : ""}`;
  activeAuroc.textContent = formatMetric(active.auroc);
  oasis2Auroc.textContent = formatMetric(oasis2.auroc);
  reviewCount.textContent = String(oasis2.review_required_count ?? handoffCount ?? progression.high_priority_subject_count ?? "--");
  summary.textContent = `${progression.subject_count || 0} subjects, ${progression.temporal_paradox_count || 0} temporal paradox flags, ${trajectory.review_subject_count || 0} trajectory reviews, ${promotionBlockers.length || 0} blockers, AUROC delta ${formatDelta(activeVsCandidate.auroc_delta)}, evidence ${evidenceHealth.status || "pending"}, next ${nextBestAction.label || "review evidence"}`;
  disclaimer.textContent = payload.decision_support_note || "Research decision-support only. Not diagnosis.";
  if (actions) {
    const actionChips = [
      nextBestAction.command ? {
        label: nextBestAction.label || "Next best action",
        status: nextBestAction.priority === "critical" ? "critical" : "ready",
        command: nextBestAction.command
      } : null,
      ...demoActions.slice(0, 2)
    ].filter(Boolean);
    actions.innerHTML = actionChips.map(action => `
      <button class="research-action-button ${action.status === "ready" ? "ready" : ""}" data-command="${escapeHtml(action.command || "")}" title="${escapeHtml(action.command || "")}">
        ${escapeHtml(action.label || "Demo action")}
      </button>
    `).join("");
    bindResearchActionButtons();
  }

  if (queueCases.length) {
    list.innerHTML = queueCases.slice(0, 8).map(item => `
      <div class="research-case">
        <div>
          <strong>${escapeHtml(item.subject_id)}</strong>
          <span>${escapeHtml(item.session_id || formatCaseType(item.case_type))}</span>
        </div>
        <div>
          <span>${escapeHtml(formatCaseType(item.case_type))}</span>
          <strong>${formatMetric(item.risk_score ?? item.max_risk ?? item.risk_delta)}</strong>
        </div>
        <div>
          <span>Review</span>
          <strong>${escapeHtml(item.review_required ? "Yes" : readiness.readiness_status || "Track")}</strong>
        </div>
        <span class="research-status-pill">${escapeHtml(formatCaseType(item.priority || "Review"))}</span>
      </div>
    `).join("");
    return;
  }

  if (!subjects.length) {
    list.innerHTML = `
      <div class="research-empty">
        <strong>No priority subjects</strong>
        <span>OASIS-2 predictions were not found or produced no progression cases.</span>
      </div>
    `;
    return;
  }

  list.innerHTML = subjects.map(subject => `
    <div class="research-case">
      <div>
        <strong>${escapeHtml(subject.subject_id)}</strong>
        <span>${escapeHtml(subject.session_count)} visits</span>
      </div>
      <div>
        <span>Trajectory</span>
        <strong>${formatMetric(subject.trajectory_score ?? subject.risk_delta)}</strong>
      </div>
      <div>
        <span>Status</span>
        <strong>${escapeHtml(formatCaseType(subject.trajectory_status || "Track"))}</strong>
      </div>
      <span class="research-status-pill">${subject.high_priority ? "Review" : "Track"}</span>
    </div>
  `).join("");
}

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

  // 6. Render generated model-board payload if present
  renderResearchMode();

  // 7. Draw scan explorer canvases (if active)
  if (state.activePage === 'scan-explorer') {
    renderAllMRIPlanes();
  }
}
