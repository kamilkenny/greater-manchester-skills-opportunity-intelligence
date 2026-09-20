"use strict";


const state = {
  current: [],
  kpis: [],
  definitions: [],
  skills: [],
  mbacc: [],
  youth: [],
  opportunity: [],
  metadata: {},
};


const plotConfig = {
  responsive: true,
  displaylogo: false,
  modeBarButtonsToRemove: [
    "lasso2d",
    "select2d",
  ],
};


const baseLayout = {
  paper_bgcolor: "rgba(0,0,0,0)",
  plot_bgcolor: "rgba(0,0,0,0)",

  font: {
    family:
      "Inter, Segoe UI, sans-serif",
    color: "#425466",
    size: 12,
  },

  margin: {
    l: 55,
    r: 20,
    t: 25,
    b: 60,
  },

  xaxis: {
    gridcolor: "#e8eef2",
    zeroline: false,
  },

  yaxis: {
    gridcolor: "#e8eef2",
    zeroline: false,
  },

  legend: {
    orientation: "h",
    y: -0.2,
  },
};


async function loadJson(path) {
  const response = await fetch(path);

  if (!response.ok) {
    throw new Error(
      `Unable to load ${path}: ${response.status}`
    );
  }

  return response.json();
}


function numberFormat(value, unit = "") {
  if (
    value === null ||
    value === undefined ||
    Number.isNaN(Number(value))
  ) {
    return "Not published";
  }

  const number = Number(value);

  if (unit === "percent") {
    return `${number.toFixed(1)}%`;
  }

  return new Intl.NumberFormat(
    "en-GB",
    {
      maximumFractionDigits: 0,
    }
  ).format(number);
}


function academicPeriod(value) {
  const text = String(value || "");

  if (text.length === 6) {
    return `${text.slice(0, 4)}/${text.slice(4)}`;
  }

  return text;
}


function definitionMap() {
  return Object.fromEntries(
    state.definitions.map(
      item => [item.kpi_code, item]
    )
  );
}


function boroughNames() {
  return [
    ...new Set(
      state.current.map(
        item => item.borough_name
      )
    ),
  ].sort();
}


function fillBoroughSelect(id) {
  const element = document.getElementById(id);

  element.innerHTML = boroughNames()
    .map(
      name =>
        `<option value="${name}">${name}</option>`
    )
    .join("");

  if (boroughNames().includes("Manchester")) {
    element.value = "Manchester";
  }
}


function setNavigation() {
  document
    .querySelectorAll(".nav-link")
    .forEach(button => {

      button.addEventListener(
        "click",
        () => {

          document
            .querySelectorAll(".nav-link")
            .forEach(
              item =>
                item.classList.remove("active")
            );

          document
            .querySelectorAll(".page-section")
            .forEach(
              section =>
                section.classList.remove("active")
            );

          button.classList.add("active");

          document
            .getElementById(
              button.dataset.section
            )
            .classList.add("active");

          window.scrollTo({
            top: 0,
            behavior: "smooth",
          });

          setTimeout(
            () => {
              window.dispatchEvent(
                new Event("resize")
              );
            },
            100
          );
        }
      );

    });
}


function buildOverviewCards() {
  const periods =
    state.metadata.reporting_periods || {};

  const cards = [
    {
      label: "Greater Manchester",
      value: "10",
      detail: "boroughs",
    },
    {
      label: "Current KPI layer",
      value: String(
        new Set(
          state.kpis.map(
            row => row.kpi_code
          )
        ).size
      ),
      detail: "governed indicators",
    },
    {
      label: "MBacc framework",
      value: "7",
      detail: "analytical gateways",
    },
    {
      label: "Latest apprenticeships",
      value: periods.apprenticeships || "2025/26",
      detail: "academic year",
    },
  ];

  document.getElementById(
    "overview-stats"
  ).innerHTML = cards
    .map(
      card => `
        <article class="stat-card">
          <div class="stat-label">
            ${card.label}
          </div>

          <div class="stat-value">
            ${card.value}
          </div>

          <div class="stat-detail">
            ${card.detail}
          </div>
        </article>
      `
    )
    .join("");
}


function buildOverviewKpiSelector() {
  const defs = definitionMap();

  const selector =
    document.getElementById("overview-kpi");

  selector.innerHTML = state.definitions
    .map(
      item => `
        <option value="${item.kpi_code}">
          ${item.kpi_name}
        </option>
      `
    )
    .join("");

  selector.value = "EMPLOYMENT_RATE";

  selector.addEventListener(
    "change",
    () => {
      drawOverviewComparison(
        selector.value
      );
    }
  );

  drawOverviewComparison(
    selector.value
  );
}


function drawOverviewComparison(kpiCode) {
  const defs = definitionMap();

  const definition = defs[kpiCode];

  const rows = state.kpis
    .filter(
      row =>
        row.kpi_code === kpiCode
    )
    .sort(
      (a, b) =>
        (
          Number(a.kpi_value) || -Infinity
        )
        -
        (
          Number(b.kpi_value) || -Infinity
        )
    );

  Plotly.react(
    "overview-chart",
    [
      {
        type: "bar",
        orientation: "h",

        x: rows.map(
          row => row.kpi_value
        ),

        y: rows.map(
          row => row.borough_name
        ),

        text: rows.map(
          row =>
            numberFormat(
              row.kpi_value,
              definition.unit_name
            )
        ),

        textposition: "outside",

        hovertemplate:
          "<b>%{y}</b><br>" +
          "%{text}<extra></extra>",

        marker: {
          color: "#0077b6",
        },
      },
    ],
    {
      ...baseLayout,

      height: 470,

      xaxis: {
        ...baseLayout.xaxis,
        title:
          definition.unit_name === "percent"
            ? "Percent"
            : "Count",
      },

      yaxis: {
        ...baseLayout.yaxis,
        automargin: true,
      },

      showlegend: false,
    },
    plotConfig
  );

  const period =
    rows.find(
      row => row.period_name
    )?.period_name || "";

  document.getElementById(
    "overview-period"
  ).textContent =
    `${definition.kpi_name}. Reporting period: ${period}.`;
}


function drawOverviewYouth() {
  const rows = state.current
    .slice()
    .sort(
      (a, b) =>
        Number(a.neet_percent)
        - Number(b.neet_percent)
    );

  Plotly.react(
    "overview-youth-chart",
    [
      {
        type: "bar",
        x: rows.map(
          row => row.borough_name
        ),
        y: rows.map(
          row => row.neet_percent
        ),
        name: "NEET",
        marker: {
          color: "#c85151",
        },
        hovertemplate:
          "<b>%{x}</b><br>" +
          "NEET: %{y:.1f}%<extra></extra>",
      },
      {
        type: "bar",
        x: rows.map(
          row => row.borough_name
        ),
        y: rows.map(
          row =>
            row.education_training_percent
        ),
        name: "Education / training",
        marker: {
          color: "#1d8f78",
        },
        hovertemplate:
          "<b>%{x}</b><br>" +
          "Education / training: " +
          "%{y:.1f}%<extra></extra>",
      },
    ],
    {
      ...baseLayout,
      height: 400,
      barmode: "group",

      yaxis: {
        ...baseLayout.yaxis,
        title: "Percent",
      },

      xaxis: {
        tickangle: -35,
      },
    },
    plotConfig
  );
}


function drawOverviewLabour() {
  const rows = state.current
    .slice()
    .sort(
      (a, b) =>
        Number(b.employment_rate)
        - Number(a.employment_rate)
    );

  Plotly.react(
    "overview-labour-chart",
    [
      {
        type: "bar",

        x: rows.map(
          row => row.borough_name
        ),

        y: rows.map(
          row => row.employment_rate
        ),

        name: "Employment",

        marker: {
          color: "#0077b6",
        },
      },
      {
        type: "bar",

        x: rows.map(
          row => row.borough_name
        ),

        y: rows.map(
          row =>
            row.economic_inactivity_rate
        ),

        name: "Economic inactivity",

        marker: {
          color: "#d68c1f",
        },
      },
    ],
    {
      ...baseLayout,
      height: 400,
      barmode: "group",

      yaxis: {
        ...baseLayout.yaxis,
        title: "Percent",
      },

      xaxis: {
        tickangle: -35,
      },
    },
    plotConfig
  );
}


function buildBoroughExplorer() {
  const select =
    document.getElementById(
      "borough-select"
    );

  select.addEventListener(
    "change",
    () => renderBorough(select.value)
  );

  renderBorough(select.value);
}


function renderBorough(name) {
  const defs = definitionMap();

  const rows = state.kpis.filter(
    row => row.borough_name === name
  );

  const featured = [
    "APP_STARTS",
    "NEET_RATE",
    "EDU_TRAINING_RATE",
    "EMPLOYMENT_RATE",
    "UNEMPLOYMENT_RATE",
    "INACTIVITY_RATE",
    "RQF3_PLUS_RATE",
    "RQF4_PLUS_RATE",
  ];

  document.getElementById(
    "borough-kpi-grid"
  ).innerHTML = featured
    .map(code => {

      const row = rows.find(
        item => item.kpi_code === code
      );

      const def = defs[code];

      const statusClass =
        row?.kpi_value === null
          ? "suppressed"
          : "";

      return `
        <article class="kpi-card">

          <div class="kpi-domain">
            ${def.domain_name}
          </div>

          <div class="kpi-name">
            ${def.kpi_name}
          </div>

          <div class="kpi-value">
            ${numberFormat(
              row?.kpi_value,
              def.unit_name
            )}
          </div>

          <div class="kpi-period">
            ${row?.period_name || ""}
          </div>

          <div
            class="kpi-status ${statusClass}"
          >
            ${row?.value_status || "unavailable"}
          </div>

        </article>
      `;
    })
    .join("");

  const current = state.current.find(
    row => row.borough_name === name
  );

  Plotly.react(
    "borough-labour-chart",
    [
      {
        type: "bar",

        x: [
          "Employment",
          "Unemployment",
          "Inactivity",
        ],

        y: [
          current.employment_rate,
          current.unemployment_rate,
          current.economic_inactivity_rate,
        ],

        text: [
          `${Number(
            current.employment_rate
          ).toFixed(1)}%`,

          `${Number(
            current.unemployment_rate
          ).toFixed(1)}%`,

          `${Number(
            current.economic_inactivity_rate
          ).toFixed(1)}%`,
        ],

        textposition: "outside",

        marker: {
          color: [
            "#0077b6",
            "#c85151",
            "#d68c1f",
          ],
        },
      },
    ],
    {
      ...baseLayout,
      height: 390,

      yaxis: {
        ...baseLayout.yaxis,
        title: "Percent",
      },

      showlegend: false,
    },
    plotConfig
  );


  Plotly.react(
    "borough-qualification-chart",
    [
      {
        type: "bar",

        x: [
          "RQF3+",
          "RQF4+",
        ],

        y: [
          current.rqf3_plus_rate,
          current.rqf4_plus_rate,
        ],

        text: [
          `${Number(
            current.rqf3_plus_rate
          ).toFixed(1)}%`,

          `${Number(
            current.rqf4_plus_rate
          ).toFixed(1)}%`,
        ],

        textposition: "outside",

        marker: {
          color: [
            "#00a6c7",
            "#1d8f78",
          ],
        },
      },
    ],
    {
      ...baseLayout,
      height: 390,

      yaxis: {
        ...baseLayout.yaxis,
        title: "Percent",
      },

      showlegend: false,
    },
    plotConfig
  );
}


function buildPathways() {
  const select =
    document.getElementById(
      "pathway-borough-select"
    );

  select.addEventListener(
    "change",
    () => drawPathways(select.value)
  );

  drawPathways(select.value);
}


function drawPathways(name) {
  const rows = state.mbacc
    .filter(
      row =>
        row.borough_name === name
        &&
        Number(row.is_latest_period) === 1
    )
    .sort(
      (a, b) =>
        a.gateway_code.localeCompare(
          b.gateway_code
        )
    );

  Plotly.react(
    "pathway-chart",
    [
      {
        type: "bar",
        orientation: "h",

        name: "Starts",

        y: rows.map(
          row => row.gateway_name
        ),

        x: rows.map(
          row => row.apprenticeship_starts
        ),

        customdata: rows.map(
          row =>
            row.apprenticeship_starts_status
        ),

        hovertemplate:
          "<b>%{y}</b><br>" +
          "Starts: %{x}<br>" +
          "Status: %{customdata}" +
          "<extra></extra>",

        marker: {
          color: "#0077b6",
        },
      },

      {
        type: "bar",
        orientation: "h",

        name: "Achievements",

        y: rows.map(
          row => row.gateway_name
        ),

        x: rows.map(
          row =>
            row.apprenticeship_achievements
        ),

        customdata: rows.map(
          row =>
            row.apprenticeship_achievements_status
        ),

        hovertemplate:
          "<b>%{y}</b><br>" +
          "Achievements: %{x}<br>" +
          "Status: %{customdata}" +
          "<extra></extra>",

        marker: {
          color: "#1d8f78",
        },
      },
    ],
    {
      ...baseLayout,

      height: 560,
      barmode: "group",

      xaxis: {
        ...baseLayout.xaxis,
        title: "Apprenticeships",
      },

      yaxis: {
        ...baseLayout.yaxis,
        automargin: true,
      },
    },
    plotConfig
  );
}


function buildTrends() {
  const borough =
    document.getElementById(
      "trend-borough-select"
    );

  const domain =
    document.getElementById(
      "trend-domain-select"
    );

  const redraw = () => {
    drawTrend(
      borough.value,
      domain.value
    );
  };

  borough.addEventListener(
    "change",
    redraw
  );

  domain.addEventListener(
    "change",
    redraw
  );

  redraw();
}


function drawTrend(name, domain) {
  let traces = [];
  let note = "";
  let yTitle = "";

  if (domain === "apprenticeships") {

    const rows = state.skills
      .filter(
        row => row.borough_name === name
      )
      .sort(
        (a, b) =>
          String(a.time_period)
            .localeCompare(
              String(b.time_period)
            )
      );

    const x = rows.map(
      row =>
        academicPeriod(row.time_period)
    );

    traces = [
      {
        type: "scatter",
        mode: "lines+markers",
        name: "Starts",
        x,
        y: rows.map(
          row =>
            row.apprenticeship_starts
        ),
      },
      {
        type: "scatter",
        mode: "lines+markers",
        name: "Achievements",
        x,
        y: rows.map(
          row =>
            row.apprenticeship_achievements
        ),
      },
      {
        type: "scatter",
        mode: "lines+markers",
        name: "Participation",
        x,
        y: rows.map(
          row =>
            row.apprenticeship_participation
        ),
      },
    ];

    yTitle = "Apprenticeships";
    note =
      "Department for Education academic-year series.";
  }


  if (domain === "youth") {

    const rows = state.youth
      .filter(
        row => row.borough_name === name
      )
      .sort(
        (a, b) =>
          Number(a.time_period)
          - Number(b.time_period)
      );

    const x = rows.map(
      row => row.time_period
    );

    traces = [
      {
        type: "scatter",
        mode: "lines+markers",
        name: "NEET",
        x,
        y: rows.map(
          row => row.neet_percent
        ),
      },
      {
        type: "scatter",
        mode: "lines+markers",
        name: "Education / training",
        x,
        y: rows.map(
          row =>
            row.education_training_percent
        ),
      },
    ];

    yTitle = "Percent";

    note =
      "Headline 16-to-17 calendar-year measures.";
  }


  if (domain === "labour") {

    const rows = state.opportunity
      .filter(
        row =>
          row.borough_name === name
          &&
          row.employment_rate !== null
      )
      .sort(
        (a, b) =>
          String(a.date)
            .localeCompare(
              String(b.date)
            )
      );

    const x = rows.map(
      row => row.date
    );

    traces = [
      {
        type: "scatter",
        mode: "lines",
        name: "Employment",
        x,
        y: rows.map(
          row => row.employment_rate
        ),
      },
      {
        type: "scatter",
        mode: "lines",
        name: "Unemployment",
        x,
        y: rows.map(
          row => row.unemployment_rate
        ),
      },
      {
        type: "scatter",
        mode: "lines",
        name: "Economic inactivity",
        x,
        y: rows.map(
          row =>
            row.economic_inactivity_rate
        ),
      },
    ];

    yTitle = "Percent";

    note =
      "ONS Nomis Annual Population Survey rolling-period series.";
  }


  if (domain === "qualifications") {

    const rows = state.opportunity
      .filter(
        row =>
          row.borough_name === name
          &&
          row.rqf3_plus_rate !== null
      )
      .sort(
        (a, b) =>
          String(a.date)
            .localeCompare(
              String(b.date)
            )
      );

    const x = rows.map(
      row => row.date
    );

    traces = [
      {
        type: "scatter",
        mode: "lines+markers",
        name: "RQF3+",
        x,
        y: rows.map(
          row => row.rqf3_plus_rate
        ),
      },
      {
        type: "scatter",
        mode: "lines+markers",
        name: "RQF4+",
        x,
        y: rows.map(
          row => row.rqf4_plus_rate
        ),
      },
    ];

    yTitle = "Percent";

    note =
      "ONS Nomis qualification attainment series.";
  }


  Plotly.react(
    "trend-chart",
    traces,
    {
      ...baseLayout,

      height: 540,

      yaxis: {
        ...baseLayout.yaxis,
        title: yTitle,
      },

      xaxis: {
        ...baseLayout.xaxis,
        title: "Reporting period",
      },

      hovermode: "x unified",
    },
    plotConfig
  );

  document.getElementById(
    "trend-note"
  ).textContent = note;
}


function buildMethodology() {
  const periods =
    state.metadata.reporting_periods || {};

  const items = [
    [
      "Apprenticeships",
      periods.apprenticeships,
    ],
    [
      "Youth transition",
      periods.youth_transition,
    ],
    [
      "Labour market",
      periods.labour_market,
    ],
    [
      "Qualifications",
      periods.qualifications,
    ],
  ];

  document.getElementById(
    "methodology-periods"
  ).innerHTML = items
    .map(
      ([label, value]) => `
        <div class="period-item">
          <strong>${label}</strong>
          <span>${value || "Not available"}</span>
        </div>
      `
    )
    .join("");
}


function setRefreshText() {
  const value =
    state.metadata.exported_at_utc;

  if (!value) {
    return;
  }

  const date = new Date(value);

  document.getElementById(
    "hero-refresh"
  ).textContent =
    `Public data refreshed ${date.toLocaleString(
      "en-GB",
      {
        dateStyle: "medium",
        timeStyle: "short",
        timeZone: "UTC",
      }
    )} UTC`;
}


async function initialise() {

  try {

    [
      state.current,
      state.kpis,
      state.definitions,
      state.skills,
      state.mbacc,
      state.youth,
      state.opportunity,
      state.metadata,
    ] = await Promise.all([
      loadJson(
        "data/borough-current.json"
      ),
      loadJson(
        "data/borough-kpis.json"
      ),
      loadJson(
        "data/kpi-definitions.json"
      ),
      loadJson(
        "data/skills-supply.json"
      ),
      loadJson(
        "data/mbacc-pathways.json"
      ),
      loadJson(
        "data/youth-transition.json"
      ),
      loadJson(
        "data/borough-opportunity.json"
      ),
      loadJson(
        "data/metadata.json"
      ),
    ]);


    setNavigation();

    fillBoroughSelect(
      "borough-select"
    );

    fillBoroughSelect(
      "pathway-borough-select"
    );

    fillBoroughSelect(
      "trend-borough-select"
    );


    buildOverviewCards();
    buildOverviewKpiSelector();

    drawOverviewYouth();
    drawOverviewLabour();

    buildBoroughExplorer();
    buildPathways();
    buildTrends();
    buildMethodology();

    setRefreshText();


    document
      .getElementById(
        "loading-overlay"
      )
      .classList.add("hidden");

  } catch (error) {

    console.error(error);

    document.getElementById(
      "loading-overlay"
    ).innerHTML = `
      <strong>
        GM SkillsFlow could not load.
      </strong>

      <span>
        ${error.message}
      </span>
    `;

  }
}


initialise();



/* ============================================================
   Scatter label helpers
   ============================================================ */

function getYouthTransitionLabelPosition(name) {
  const map = {
    "Trafford": "top center",
    "Stockport": "top center",
    "Oldham": "top center",
    "Bolton": "top right",
    "Bury": "middle right",
    "Tameside": "top left",
    "Wigan": "top center",
    "Rochdale": "middle right",
    "Manchester": "middle right",
    "Salford": "top center"
  };
  return map[name] || "top center";
}

function getLabourMarketLabelPosition(name) {
  const map = {
    "Trafford": "top center",
    "Manchester": "top center",
    "Stockport": "top center",
    "Tameside": "top center",
    "Wigan": "top center",
    "Salford": "top center",
    "Bury": "bottom center",
    "Bolton": "top center",
    "Rochdale": "top center",
    "Oldham": "top center"
  };
  return map[name] || "top center";
}

function buildTextPositions(names, chooser) {
  return names.map((name) => chooser(name));
}

