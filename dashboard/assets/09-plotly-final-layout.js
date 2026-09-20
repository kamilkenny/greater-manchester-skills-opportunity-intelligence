(() => {
  if (window.__gmSkillsPlotlyFinalLayoutLoaded) {
    return;
  }

  window.__gmSkillsPlotlyFinalLayoutLoaded = true;

  function fixPlotLayout(plot) {
    if (!window.Plotly || !plot) {
      return;
    }

    try {
      const fullData = plot.data || [];
      const hasLegend = fullData.length > 1;

      const layoutUpdate = {
        "margin.t": hasLegend ? 90 : 55,
        "margin.b": 95,
        "margin.l": 110,
        "margin.r": 35,
        "xaxis.automargin": true,
        "yaxis.automargin": true,
        "xaxis.title.standoff": 16,
        "yaxis.title.standoff": 16
      };

      if (hasLegend) {
        layoutUpdate["showlegend"] = true;
        layoutUpdate["legend.orientation"] = "h";
        layoutUpdate["legend.yanchor"] = "bottom";
        layoutUpdate["legend.y"] = 1.08;
        layoutUpdate["legend.xanchor"] = "left";
        layoutUpdate["legend.x"] = 0;
      }

      window.Plotly.relayout(plot, layoutUpdate);
    } catch (err) {
      console.error("Plot relayout failed", err);
    }
  }

  function applyToAllPlots() {
    document
      .querySelectorAll(".js-plotly-plot")
      .forEach((plot) => fixPlotLayout(plot));
  }

  const observer = new MutationObserver(() => {
    window.setTimeout(applyToAllPlots, 250);
  });

  observer.observe(document.documentElement, {
    childList: true,
    subtree: true
  });

  window.addEventListener("load", () => {
    window.setTimeout(applyToAllPlots, 500);
  });

  window.addEventListener("resize", () => {
    window.setTimeout(applyToAllPlots, 300);
  });
})();
