(() => {
  if (window.__gmSkillsPlotlyLayoutFixesLoaded) {
    return;
  }

  window.__gmSkillsPlotlyLayoutFixesLoaded = true;

  function relayoutPlots() {
    if (!window.Plotly) {
      return;
    }

    const plots = document.querySelectorAll(".js-plotly-plot");

    plots.forEach((plot) => {
      try {
        window.Plotly.relayout(plot, {
          "margin.t": 50,
          "margin.b": 70,
          "margin.l": 75,
          "margin.r": 30,
          "xaxis.automargin": true,
          "yaxis.automargin": true,
          "xaxis.title.standoff": 14,
          "yaxis.title.standoff": 14
        });
      } catch (err) {
        console.error("Plot relayout skipped", err);
      }
    });
  }

  const observer = new MutationObserver(() => {
    window.setTimeout(relayoutPlots, 250);
  });

  observer.observe(document.documentElement, {
    childList: true,
    subtree: true
  });

  window.addEventListener("load", () => {
    window.setTimeout(relayoutPlots, 400);
  });

  window.addEventListener("resize", () => {
    window.setTimeout(relayoutPlots, 250);
  });
})();
