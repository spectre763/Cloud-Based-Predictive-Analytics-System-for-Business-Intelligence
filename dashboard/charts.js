// ─── charts.js ────────────────────────────────────────────────────────────────
// All Chart.js chart definitions — imported and controlled by app.js
// ─────────────────────────────────────────────────────────────────────────────

export const CHART_DEFAULTS = {
  responsive:          true,
  maintainAspectRatio: false,
  animation:           { duration: 900, easing: "easeOutQuart" },
  plugins: {
    legend: { display: false },
    tooltip: {
      backgroundColor: "#1C1C32",
      borderColor:     "rgba(255,255,255,0.08)",
      borderWidth:     1,
      titleColor:      "#E2E8F0",
      bodyColor:       "#94A3B8",
      padding:         12,
      cornerRadius:    8,
      titleFont:       { weight: "700", size: 12 },
    }
  },
  scales: {
    x: {
      grid:  { color: "rgba(255,255,255,0.04)", drawBorder: false },
      ticks: { color: "#64748B", maxRotation: 30, font: { size: 10 } },
    },
    y: {
      grid:  { color: "rgba(255,255,255,0.04)", drawBorder: false },
      ticks: { color: "#64748B", font: { size: 10 } },
    },
  },
};

// Gradient helper
function makeGradient(ctx, top, bottom) {
  const g = ctx.createLinearGradient(0, 0, 0, ctx.canvas.height);
  g.addColorStop(0,   top);
  g.addColorStop(1,   bottom);
  return g;
}

// ─── Revenue Trend Line ───────────────────────────────────────────────────────
export function buildRevenueTrendChart(canvasId, labels, revenue, profit) {
  const ctx = document.getElementById(canvasId).getContext("2d");
  const revGrad  = makeGradient(ctx, "rgba(79,142,247,0.35)", "rgba(79,142,247,0.0)");
  const profGrad = makeGradient(ctx, "rgba(16,185,129,0.2)",  "rgba(16,185,129,0.0)");

  return new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: "Revenue",
          data:  revenue,
          borderColor: "#4F8EF7",
          borderWidth: 3,
          backgroundColor: revGrad,
          fill: true,
          tension: 0.45,
          pointRadius: 3,
          pointHoverRadius: 7,
          pointBackgroundColor: "#4F8EF7",
        },
        {
          label: "Profit",
          data:  profit,
          borderColor: "#10B981",
          borderWidth: 2,
          borderDash: [6, 4],
          backgroundColor: profGrad,
          fill: true,
          tension: 0.45,
          pointRadius: 2,
          pointHoverRadius: 5,
          pointBackgroundColor: "#10B981",
        }
      ],
    },
    options: {
      ...CHART_DEFAULTS,
      plugins: {
        ...CHART_DEFAULTS.plugins,
        legend: {
          display: true,
          position: "top",
          labels: { color: "#94A3B8", usePointStyle: true, pointStyleWidth: 8, font: { size: 11 } }
        },
        tooltip: {
          ...CHART_DEFAULTS.plugins.tooltip,
          callbacks: { label: ctx => ` $${ctx.parsed.y.toLocaleString()}` },
        }
      },
      scales: {
        x: CHART_DEFAULTS.scales.x,
        y: {
          ...CHART_DEFAULTS.scales.y,
          ticks: {
            ...CHART_DEFAULTS.scales.y.ticks,
            callback: v => "$" + (v >= 1e6 ? (v/1e6).toFixed(1)+"M" : (v/1e3).toFixed(0)+"K"),
          },
        },
      },
    },
  });
}

// ─── Forecast Chart ───────────────────────────────────────────────────────────
export function buildForecastChart(canvasId, histLabels, histData, fcLabels, fcBase, fcPess, fcOpt, fcUpper, fcLower) {
  const allLabels = [...histLabels, ...fcLabels];
  const histNulls = new Array(histLabels.length).fill(null);
  const fcNulls   = new Array(histLabels.length).fill(null);
  const ctx = document.getElementById(canvasId).getContext("2d");

  return new Chart(ctx, {
    type: "line",
    data: {
      labels: allLabels,
      datasets: [
        // Confidence band (upper)
        {
          label: "Upper",
          data:  [...histNulls, ...fcUpper],
          borderColor:     "rgba(79,142,247,0)",
          backgroundColor: "rgba(79,142,247,0.08)",
          fill: "+1",
          tension: 0.4, pointRadius: 0,
        },
        // Confidence band (lower)
        {
          label: "Lower",
          data:  [...histNulls, ...fcLower],
          borderColor:     "rgba(79,142,247,0)",
          backgroundColor: "rgba(79,142,247,0.08)",
          fill: false,
          tension: 0.4, pointRadius: 0,
        },
        // Historical
        {
          label: "Historical",
          data:  [...histData, histData[histData.length-1]],
          borderColor: "#4F8EF7", borderWidth: 3,
          backgroundColor: "transparent",
          tension: 0.4, pointRadius: 3, pointHoverRadius: 7,
          pointBackgroundColor: "#4F8EF7",
        },
        // Base forecast
        {
          label: "Base",
          data:  [...fcNulls, histData[histData.length-1], ...fcBase],
          borderColor: "#22D3EE", borderWidth: 2.5,
          borderDash: [8, 4],
          backgroundColor: "transparent",
          tension: 0.4, pointRadius: 4,
          pointStyle: "rectRot",
          pointBackgroundColor: "#22D3EE",
        },
        // Pessimistic
        {
          label: "Pessimistic",
          data:  [...fcNulls, histData[histData.length-1], ...fcPess],
          borderColor: "#F43F5E", borderWidth: 1.5,
          borderDash: [4, 4],
          backgroundColor: "transparent",
          tension: 0.4, pointRadius: 3, pointBackgroundColor: "#F43F5E",
        },
        // Optimistic
        {
          label: "Optimistic",
          data:  [...fcNulls, histData[histData.length-1], ...fcOpt],
          borderColor: "#10B981", borderWidth: 1.5,
          borderDash: [4, 4],
          backgroundColor: "transparent",
          tension: 0.4, pointRadius: 3, pointBackgroundColor: "#10B981",
        },
      ],
    },
    options: {
      ...CHART_DEFAULTS,
      plugins: {
        ...CHART_DEFAULTS.plugins,
        legend: {
          display: true, position: "top",
          labels: { color: "#94A3B8", usePointStyle: true, font: { size: 11 },
            filter: item => !["Upper","Lower"].includes(item.text),
          },
        },
        tooltip: {
          ...CHART_DEFAULTS.plugins.tooltip,
          callbacks: { label: ctx => ` ${ctx.dataset.label}: $${ctx.parsed.y?.toLocaleString() ?? "—"}` },
        },
        annotation: {
          annotations: {
            forecastLine: {
              type: "line",
              xMin: histLabels.length,
              xMax: histLabels.length,
              borderColor: "rgba(255,255,255,0.15)",
              borderWidth: 1,
              borderDash: [5, 5],
              label: { content: "Forecast →", display: true, color: "#64748B", font: { size: 10 } },
            }
          }
        }
      },
      scales: {
        x: CHART_DEFAULTS.scales.x,
        y: {
          ...CHART_DEFAULTS.scales.y,
          ticks: {
            ...CHART_DEFAULTS.scales.y.ticks,
            callback: v => v == null ? "" : "$" + (v/1e3).toFixed(0)+"K",
          },
        },
      },
    },
  });
}

// ─── KPI Sparklines ───────────────────────────────────────────────────────────
export function buildSparkline(canvasId, data, color = "#4F8EF7") {
  const ctx = document.getElementById(canvasId).getContext("2d");
  const grad = makeGradient(ctx, color + "44", color + "00");

  return new Chart(ctx, {
    type: "line",
    data: {
      labels: data.map((_, i) => i),
      datasets: [{ data, borderColor: color, borderWidth: 2, backgroundColor: grad, fill: true, tension: 0.4, pointRadius: 0 }],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      animation: { duration: 700 },
      plugins: { legend: { display: false }, tooltip: { enabled: false } },
      scales: {
        x: { display: false },
        y: { display: false },
      },
    },
  });
}

// ─── Segment Donut ────────────────────────────────────────────────────────────
export function buildSegmentDonut(canvasId, labels, values) {
  const COLORS = ["#10B981","#4F8EF7","#9B6FEA","#F59E0B","#F43F5E"];
  const ctx = document.getElementById(canvasId).getContext("2d");

  return new Chart(ctx, {
    type: "doughnut",
    data: {
      labels,
      datasets: [{
        data: values,
        backgroundColor: COLORS,
        borderColor: "#07070F",
        borderWidth: 3,
        hoverOffset: 8,
      }],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      cutout: "62%",
      animation: { duration: 900, animateScale: true },
      plugins: {
        legend: {
          display: true, position: "right",
          labels: { color: "#94A3B8", usePointStyle: true, font: { size: 11 }, padding: 14 },
        },
        tooltip: { ...CHART_DEFAULTS.plugins.tooltip },
      },
    },
  });
}

// ─── Revenue by Category Bar ──────────────────────────────────────────────────
export function buildCategoryBar(canvasId, labels, values) {
  const ctx = document.getElementById(canvasId).getContext("2d");
  const grad = makeGradient(ctx, "#9B6FEA", "#4F8EF7");

  return new Chart(ctx, {
    type: "bar",
    data: {
      labels,
      datasets: [{
        data: values,
        backgroundColor: grad,
        borderRadius: 6,
        borderSkipped: false,
      }],
    },
    options: {
      ...CHART_DEFAULTS,
      indexAxis: "y",
      plugins: {
        ...CHART_DEFAULTS.plugins,
        tooltip: {
          ...CHART_DEFAULTS.plugins.tooltip,
          callbacks: { label: ctx => ` $${ctx.parsed.x.toLocaleString()}` },
        },
      },
      scales: {
        x: {
          ...CHART_DEFAULTS.scales.x,
          ticks: { color: "#64748B", callback: v => "$"+(v/1e3).toFixed(0)+"K", font: { size: 10 } },
        },
        y: { ...CHART_DEFAULTS.scales.y },
      },
    },
  });
}

// ─── Anomaly Time-Series ──────────────────────────────────────────────────────
export function buildAnomalyChart(canvasId, labels, values, anomalyIdxs) {
  const ctx   = document.getElementById(canvasId).getContext("2d");
  const grad  = makeGradient(ctx, "rgba(79,142,247,0.3)", "rgba(79,142,247,0.0)");

  const pointColors = labels.map((_, i) =>
    anomalyIdxs.includes(i) ? "#F43F5E" : "#4F8EF7"
  );
  const pointSizes = labels.map((_, i) =>
    anomalyIdxs.includes(i) ? 9 : 3
  );

  return new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [{
        label: "Revenue",
        data:  values,
        borderColor: "#4F8EF7",
        borderWidth: 2.5,
        backgroundColor: grad,
        fill: true, tension: 0.4,
        pointRadius:          pointSizes,
        pointHoverRadius:     10,
        pointBackgroundColor: pointColors,
        pointBorderColor:     pointColors.map(c => c === "#F43F5E" ? "white" : c),
        pointBorderWidth:     pointColors.map(c => c === "#F43F5E" ? 2 : 0),
      }],
    },
    options: {
      ...CHART_DEFAULTS,
      plugins: {
        ...CHART_DEFAULTS.plugins,
        tooltip: {
          ...CHART_DEFAULTS.plugins.tooltip,
          callbacks: {
            label: ctx => {
              const v = ctx.parsed.y;
              const flag = anomalyIdxs.includes(ctx.dataIndex) ? " ⚠️ ANOMALY" : "";
              return ` $${v.toLocaleString()}${flag}`;
            }
          },
        },
      },
      scales: {
        x: CHART_DEFAULTS.scales.x,
        y: {
          ...CHART_DEFAULTS.scales.y,
          ticks: { ...CHART_DEFAULTS.scales.y.ticks, callback: v => "$"+(v/1e3).toFixed(0)+"K" },
        },
      },
    },
  });
}

// ─── NPS Gauge (semi-circle using doughnut) ───────────────────────────────────
export function buildNPSGauge(canvasId, value, max = 80) {
  const pct  = value / max;
  const ctx  = document.getElementById(canvasId).getContext("2d");
  const fill = pct > 0.7 ? "#10B981" : pct > 0.4 ? "#4F8EF7" : "#F43F5E";

  return new Chart(ctx, {
    type: "doughnut",
    data: {
      datasets: [{
        data: [value, max - value],
        backgroundColor: [fill, "rgba(255,255,255,0.05)"],
        borderWidth: 0,
        circumference: 240,
        rotation: -120,
      }],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      cutout: "75%",
      animation: { duration: 1100, animateRotate: true },
      plugins: { legend: { display: false }, tooltip: { enabled: false } },
    },
    plugins: [{
      id: "gaugeText",
      afterDraw(chart) {
        const { ctx, chartArea: { width, height, top } } = chart;
        ctx.save();
        ctx.font = "bold 26px Inter";
        ctx.fillStyle = "#E2E8F0";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(Math.round(value), width/2, top + height * 0.62);
        ctx.font = "12px Inter";
        ctx.fillStyle = "#64748B";
        ctx.fillText("NPS Score", width/2, top + height * 0.80);
        ctx.restore();
      }
    }],
  });
}

// ─── Churn Trend ─────────────────────────────────────────────────────────────
export function buildChurnTrend(canvasId, labels, churn, cac) {
  const ctx = document.getElementById(canvasId).getContext("2d");

  return new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: "Churn %",
          data:  churn,
          borderColor: "#F43F5E", borderWidth: 2,
          backgroundColor: "transparent",
          tension: 0.4, pointRadius: 2, yAxisID: "y",
        },
        {
          label: "CAC ($)",
          data:  cac,
          borderColor: "#F59E0B", borderWidth: 2,
          borderDash: [6, 4],
          backgroundColor: "transparent",
          tension: 0.4, pointRadius: 2, yAxisID: "y2",
        },
      ],
    },
    options: {
      ...CHART_DEFAULTS,
      plugins: {
        ...CHART_DEFAULTS.plugins,
        legend: {
          display: true, position: "top",
          labels: { color: "#94A3B8", usePointStyle: true, font: { size: 10 } },
        },
      },
      scales: {
        x: { ...CHART_DEFAULTS.scales.x },
        y:  { ...CHART_DEFAULTS.scales.y, position: "left",  ticks: { color: "#F43F5E", callback: v => v+"%", font: { size: 9 } } },
        y2: { ...CHART_DEFAULTS.scales.y, position: "right", ticks: { color: "#F59E0B", callback: v => "$"+v, font: { size: 9 } }, grid: { display: false } },
      },
    },
  });
}

// ─── Feature Importance Bar ───────────────────────────────────────────────────
export function buildFeatureImportance(canvasId, features, values) {
  const ctx = document.getElementById(canvasId).getContext("2d");
  const barColors = values.map((v, i) => {
    const t = i / (values.length - 1);
    return `hsl(${230 - t*50}, 80%, ${55 + t*15}%)`;
  });

  return new Chart(ctx, {
    type: "bar",
    data: {
      labels: features,
      datasets: [{
        data: values.map(v => v * 100),
        backgroundColor: barColors,
        borderRadius: 5,
        borderSkipped: false,
      }],
    },
    options: {
      ...CHART_DEFAULTS,
      indexAxis: "y",
      plugins: {
        ...CHART_DEFAULTS.plugins,
        tooltip: {
          ...CHART_DEFAULTS.plugins.tooltip,
          callbacks: { label: ctx => ` ${ctx.parsed.x.toFixed(1)}% importance` },
        },
      },
      scales: {
        x: { ...CHART_DEFAULTS.scales.x, ticks: { color: "#64748B", callback: v => v+"%", font: { size: 9 } } },
        y: { ...CHART_DEFAULTS.scales.y },
      },
    },
  });
}
