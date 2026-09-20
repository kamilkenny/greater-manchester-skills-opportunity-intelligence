"use strict";

/* =========================================================
   Shared split horizontal bar chart
   ========================================================= */

window.GMSkillsEnhancements = {
  renderSplitHorizontalComparison
};

function renderSplitHorizontalComparison(options) {
  const {
    containerId,
    rows,
    labelKey,
    leftKey,
    rightKey,
    leftTitle,
    rightTitle,
    leftHint,
    rightHint,
    leftColour,
    rightColour,
    leftSuffix = "%",
    rightSuffix = "%",
    sortMode = "left-asc"
  } = options;

  const chart = document.getElementById(containerId);
  if (!chart || !rows || !rows.length || typeof Plotly === "undefined") {
    return;
  }

  const cleaned = rows
    .map((row) => ({
      label: row[labelKey],
      leftValue: Number(row[leftKey]),
      rightValue: Number(row[rightKey])
    }))
    .filter((row) =>
      row.label &&
      Number.isFinite(row.leftValue) &&
      Number.isFinite(row.rightValue)
    );

  if (!cleaned.length) {
    chart.innerHTML = "<p>No data available.</p>";
    return;
  }

  cleaned.sort((a, b) => {
    if (sortMode === "left-asc") return a.leftValue - b.leftValue;
    if (sortMode === "left-desc") return b.leftValue - a.leftValue;
    if (sortMode === "right-asc") return a.rightValue - b.rightValue;
    return b.rightValue - a.rightValue;
  });

  const labels = cleaned.map((d) => d.label);
  const leftValues = cleaned.map((d) => d.leftValue);
  const rightValues = cleaned.map((d) => d.rightValue);

  const leftMin = Math.min(...leftValues);
  const leftMax = Math.max(...leftValues);
  const rightMin = Math.min(...rightValues);
  const rightMax = Math.max(...rightValues);

  const leftPad = Math.max((leftMax - leftMin) * 0.15, 0.5);
  const rightPad = Math.max((rightMax - rightMin) * 0.15, 0.8);

  const leftTrace = {
    type: "bar",
    orientation: "h",
    x: leftValues,
    y: labels,
    xaxis: "x",
    yaxis: "y",
    marker: {
      color: leftColour,
      line: { color: "rgba(0,0,0,0.08)", width: 1 }
    },
    text: leftValues.map((v) => `${v.toFixed(1)}${leftSuffix}`),
    textposition: "outside",
    cliponaxis: false,
    hovertemplate: "%{y}<br>" + leftTitle + ": %{x:.1f}" + leftSuffix + "<extra></extra>",
    name: leftTitle
  };

  const rightTrace = {
    type: "bar",
    orientation: "h",
    x: rightValues,
    y: labels,
    xaxis: "x2",
    yaxis: "y2",
    marker: {
      color: rightColour,
      line: { color: "rgba(0,0,0,0.08)", width: 1 }
    },
    text: rightValues.map((v) => `${v.toFixed(1)}${rightSuffix}`),
    textposition: "outside",
    cliponaxis: false,
    hovertemplate: "%{y}<br>" + rightTitle + ": %{x:.1f}" + rightSuffix + "<extra></extra>",
    name: rightTitle
  };

  const layout = {
    height: 620,
    margin: { t: 110, r: 46, b: 58, l: 160 },
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(0,0,0,0)",
    showlegend: false,
    bargap: 0.32,
    font: {
      family: "Inter, Segoe UI, Arial, sans-serif",
      size: 13,
      color: "#17324d"
    },

    xaxis: {
      domain: [0.00, 0.43],
      range: [leftMin - leftPad, leftMax + leftPad],
      zeroline: false,
      showgrid: true,
      gridcolor: "rgba(160,180,200,0.22)",
      fixedrange: true,
      title: { text: leftTitle + " (%)", standoff: 16 }
    },
    yaxis: {
      domain: [0, 1],
      autorange: "reversed",
      automargin: true,
      showgrid: false,
      tickfont: { size: 13 },
      fixedrange: true
    },

    xaxis2: {
      domain: [0.57, 1.00],
      range: [rightMin - rightPad, rightMax + rightPad],
      zeroline: false,
      showgrid: true,
      gridcolor: "rgba(160,180,200,0.22)",
      fixedrange: true,
      title: { text: rightTitle + " (%)", standoff: 16 }
    },
    yaxis2: {
      domain: [0, 1],
      anchor: "x2",
      matches: "y",
      autorange: "reversed",
      showticklabels: false,
      showgrid: false,
      fixedrange: true
    },

    annotations: [
      {
        xref: "paper",
        yref: "paper",
        x: 0.205,
        y: 1.12,
        text: `<b>${leftTitle}</b>`,
        showarrow: false,
        font: { size: 18, color: "#b3473c" }
      },
      {
        xref: "paper",
        yref: "paper",
        x: 0.205,
        y: 1.065,
        text: leftHint,
        showarrow: false,
        font: { size: 12, color: "#b3473c" }
      },
      {
        xref: "paper",
        yref: "paper",
        x: 0.795,
        y: 1.12,
        text: `<b>${rightTitle}</b>`,
        showarrow: false,
        font: { size: 18, color: "#007a78" }
      },
      {
        xref: "paper",
        yref: "paper",
        x: 0.795,
        y: 1.065,
        text: rightHint,
        showarrow: false,
        font: { size: 12, color: "#007a78" }
      }
    ]
  };

  Plotly.newPlot(chart, [leftTrace, rightTrace], layout, {
    responsive: true,
    displayModeBar: false
  });
}
