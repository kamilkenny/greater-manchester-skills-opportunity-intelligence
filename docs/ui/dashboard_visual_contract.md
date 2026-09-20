# GM SkillsFlow Dashboard Visual Contract

The existing tested GM SkillsFlow web prototype is the visual specification
for the production Plotly Dash application.

The Dash migration changes the runtime and data-serving architecture, not
the established visual identity.

## Shared design

- Dark navy sticky header
- GM brand mark and GM SkillsFlow identity
- "Designed and modelled by Kamil Ridwan" credit
- Overview
- Borough Explorer
- MBacc Pathways
- Trends
- Data & Methodology
- Light grey analytical canvas
- White rounded chart panels
- Blue, cyan, teal, amber and red analytical palette
- Existing responsive styling
- Compact dark footer

## Overview

Retain:

- large gradient hero;
- "Connecting skills supply with economic opportunity";
- public data refresh information;
- four coloured summary cards;
- current borough comparison selector and chart;
- youth transition chart;
- labour market chart.

## Borough Explorer

Retain:

- page hero;
- borough selector;
- KPI cards;
- current labour-market profile;
- RQF attainment chart.

## MBacc Pathways

Retain:

- page hero;
- borough selector;
- seven MBacc gateways;
- apprenticeship starts and achievements;
- disclosure note.

## Trends

Retain:

- page hero;
- borough selector;
- indicator group selector;
- historical line chart;
- reporting-period note.

## Data & Methodology

Retain:

- six methodology cards;
- reporting-period panel;
- source explanation;
- MBacc mapping explanation;
- disclosure governance.

## Runtime change

Old:

static HTML -> local JSON -> browser JavaScript

Production:

Plotly Dash -> SnapshotStore -> Azure Blob manifest ->
active slot -> latest validated Fabric publication

If a new publication fails, the application continues to display the
last validated snapshot.
