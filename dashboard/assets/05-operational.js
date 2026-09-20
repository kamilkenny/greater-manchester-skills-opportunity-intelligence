(() => {
  if (window.__gmSkillsFlowOperationalLoaded) {
    return;
  }

  window.__gmSkillsFlowOperationalLoaded = true;

  const AUTO_CHECK_MS = 15 * 60 * 1000;

  function explanationFor(card, graph) {
    const combined = (
      (card.textContent || "") +
      " " +
      (graph.id || "")
    ).toLowerCase();

    if (
      combined.includes("neet") ||
      combined.includes("youth transition") ||
      combined.includes("education participation")
    ) {
      return (
        "This visual compares youth participation and NEET outcomes " +
        "across Greater Manchester. Higher NEET rates indicate a " +
        "greater challenge in supporting young people into education, " +
        "employment or training."
      );
    }

    if (
      combined.includes("employment") ||
      combined.includes("unemployment") ||
      combined.includes("inactivity") ||
      combined.includes("labour")
    ) {
      return (
        "This visual compares the latest labour market position across " +
        "Greater Manchester. Read the rates alongside the reporting " +
        "period because employment, unemployment and inactivity describe " +
        "different parts of the working age population."
      );
    }

    if (
      combined.includes("rqf") ||
      combined.includes("qualification")
    ) {
      return (
        "This visual shows qualification attainment in the working age " +
        "population. RQF3+ indicates advanced secondary level and above, " +
        "while RQF4+ represents higher level qualifications and above."
      );
    }

    if (
      combined.includes("apprentice")
    ) {
      return (
        "This visual shows apprenticeship activity using the latest " +
        "published academic year. Differences between boroughs should be " +
        "considered alongside population size, industrial structure and " +
        "the local training market."
      );
    }

    if (
      combined.includes("mbacc") ||
      combined.includes("pathway") ||
      combined.includes("gateway")
    ) {
      return (
        "This visual links the selected borough's skills evidence to the " +
        "Greater Manchester Baccalaureate pathway framework. It is an " +
        "analytical view of local opportunity, not an individual course " +
        "recommendation."
      );
    }

    if (
      combined.includes("opportunity") ||
      combined.includes("borough")
    ) {
      return (
        "This visual compares Greater Manchester boroughs using the " +
        "latest validated indicators available for each official " +
        "statistical series. Reporting periods may differ between sources."
      );
    }

    return (
      "This visual uses the latest validated GM SkillsFlow snapshot. " +
      "Use the accompanying reporting period when interpreting differences " +
      "between indicators and places."
    );
  }

  function enhanceCharts() {
    const graphs = document.querySelectorAll(
      ".chart-card .dash-graph, " +
      ".mbacc-chart-panel .dash-graph, " +
      ".trend-chart-panel .dash-graph"
    );

    graphs.forEach((graph) => {
      const card =
        graph.closest(".chart-card") ||
        graph.closest(".mbacc-chart-panel") ||
        graph.closest(".trend-chart-panel");

      if (!card) {
        return;
      }

      if (card.querySelector(".visual-explainer")) {
        return;
      }

      const wrapper = document.createElement("div");
      wrapper.className = "visual-explainer";

      const title = document.createElement("span");
      title.className = "visual-explainer-title";
      title.textContent = "What this shows";

      const explanation = document.createElement("p");
      explanation.className = "visual-explainer-text";
      explanation.textContent = explanationFor(
        card,
        graph
      );

      const source = document.createElement("p");
      source.className = "visual-source-note";
      source.textContent =
        "Source: official published statistics processed through " +
        "GM SkillsFlow. Suppressed or unavailable official values " +
        "remain unavailable and are not estimated.";

      wrapper.appendChild(title);
      wrapper.appendChild(explanation);
      wrapper.appendChild(source);

      card.appendChild(wrapper);
    });
  }

  async function checkLatestSnapshot(manual) {
    const button = document.getElementById(
      "refresh-data-button"
    );

    const message = document.getElementById(
      "refresh-data-message"
    );

    if (manual && button) {
      button.disabled = true;
      button.textContent = "Refreshing...";
    }

    if (manual && message) {
      message.textContent =
        "Checking the latest validated published snapshot...";
      message.classList.remove(
        "refresh-success",
        "refresh-error"
      );
    }

    try {
      const response = await fetch(
        "/refresh-data",
        {
          method: "POST",
          headers: {
            "Accept": "application/json"
          }
        }
      );

      const result = await response.json();

      if (!response.ok || !result.ok) {
        throw new Error(
          result.message || "Refresh failed"
        );
      }

      if (result.changed) {
        if (message) {
          message.textContent =
            "New validated snapshot found. Updating dashboard...";
          message.classList.add(
            "refresh-success"
          );
        }

        window.setTimeout(() => {
          window.location.reload();
        }, 450);

        return;
      }

      if (manual && message) {
        message.textContent =
          "Already showing the latest published snapshot.";
        message.classList.add(
          "refresh-success"
        );
      }

    } catch (error) {
      if (manual && message) {
        message.textContent =
          "Refresh could not complete. Current validated data remain active.";
        message.classList.add(
          "refresh-error"
        );
      }

      console.error(
        "GM SkillsFlow refresh error:",
        error
      );

    } finally {
      if (manual && button) {
        button.disabled = false;
        button.textContent = "Refresh data";
      }
    }
  }

  document.addEventListener(
    "click",
    (event) => {
      const button = event.target.closest(
        "#refresh-data-button"
      );

      if (!button) {
        return;
      }

      checkLatestSnapshot(true);
    }
  );

  const observer = new MutationObserver(() => {
    enhanceCharts();
  });

  observer.observe(
    document.documentElement,
    {
      childList: true,
      subtree: true
    }
  );

  window.setInterval(
    () => {
      checkLatestSnapshot(false);
    },
    AUTO_CHECK_MS
  );

  enhanceCharts();
})();
