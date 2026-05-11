const baseline = {
  trend: [0.58, 0.61, 0.65, 0.69, 0.70, 0.74],
  risk: 0.74,
  hippocampalVolume: 5.8,
  completeness: 96,
  confidence: 88,
  features: [
    { name: "Hippocampal asymmetry", impact: 82 },
    { name: "Ventricular enlargement", impact: 71 },
    { name: "Temporal lobe thinning", impact: 64 },
    { name: "Global cortical pattern", impact: 57 },
  ],
};

const clamp = (value, min, max) => Math.min(max, Math.max(min, value));

function jitter(value, amount = 0.04) {
  return clamp(value + (Math.random() * 2 - 1) * amount, 0.3, 0.98);
}

function drawTrend(values) {
  const canvas = document.getElementById("trendChart");
  const ctx = canvas.getContext("2d");
  const width = canvas.width;
  const height = canvas.height;
  const padding = 28;

  ctx.clearRect(0, 0, width, height);

  ctx.strokeStyle = "rgba(255,255,255,0.12)";
  ctx.lineWidth = 1;
  for (let i = 0; i < 4; i += 1) {
    const y = padding + (i * (height - padding * 2)) / 3;
    ctx.beginPath();
    ctx.moveTo(padding, y);
    ctx.lineTo(width - padding, y);
    ctx.stroke();
  }

  const points = values.map((point, index) => {
    const x = padding + (index * (width - padding * 2)) / (values.length - 1);
    const y = height - padding - (point - 0.45) * 300;
    return { x, y };
  });

  const gradient = ctx.createLinearGradient(0, 0, width, 0);
  gradient.addColorStop(0, "#8d7dff");
  gradient.addColorStop(1, "#2dd4bf");

  ctx.lineWidth = 4;
  ctx.strokeStyle = gradient;
  ctx.beginPath();
  points.forEach((point, idx) => {
    if (idx === 0) ctx.moveTo(point.x, point.y);
    else ctx.lineTo(point.x, point.y);
  });
  ctx.stroke();

  points.forEach((point) => {
    ctx.fillStyle = "#090b14";
    ctx.beginPath();
    ctx.arc(point.x, point.y, 5.8, 0, Math.PI * 2);
    ctx.fill();

    ctx.strokeStyle = "#9f93ff";
    ctx.lineWidth = 2;
    ctx.stroke();
  });
}

function renderFeatures(features) {
  const list = document.getElementById("featureList");
  list.innerHTML = "";

  features.forEach((feature) => {
    const item = document.createElement("li");
    item.innerHTML = `
      <div class="feature-row">
        <span>${feature.name}</span>
        <strong>${feature.impact}%</strong>
      </div>
      <div class="bar"><span style="width: ${feature.impact}%"></span></div>
    `;
    list.appendChild(item);
  });
}

function rerender(data) {
  document.getElementById("riskValue").textContent = data.risk.toFixed(2);
  document.getElementById("hippoValue").textContent = `${data.hippocampalVolume.toFixed(1)} cm³`;
  document.getElementById("dataValue").textContent = `${data.completeness}%`;
  document.getElementById("confValue").textContent = `${data.confidence}%`;
  drawTrend(data.trend);
  renderFeatures(data.features);
}

function mutate() {
  const trend = baseline.trend.map((point) => jitter(point, 0.03));
  const risk = trend.at(-1);
  const features = baseline.features
    .map((feature) => ({ ...feature, impact: Math.round(clamp(feature.impact + (Math.random() * 16 - 8), 35, 95)) }))
    .sort((a, b) => b.impact - a.impact);

  return {
    trend,
    risk,
    hippocampalVolume: clamp(baseline.hippocampalVolume + (Math.random() * 0.5 - 0.3), 4.9, 6.4),
    completeness: Math.round(clamp(baseline.completeness + (Math.random() * 6 - 3), 88, 100)),
    confidence: Math.round(clamp(baseline.confidence + (Math.random() * 7 - 4), 72, 97)),
    features,
  };
}

document.getElementById("refreshBtn").addEventListener("click", () => {
  rerender(mutate());
});

rerender(baseline);
