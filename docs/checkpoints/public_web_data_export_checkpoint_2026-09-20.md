# GM SkillsFlow - Public Web Data Export Checkpoint

**Date:** 20 September 2026  
**Stage:** 8B - Fabric to Public Web Data  
**Status:** PASS

## Objective

Create a public-serving analytical data layer for the GM SkillsFlow
web application.

The public application does not connect directly to the Fabric
Warehouse. Governed Gold marts are exported into static JSON assets
for secure and fast web delivery.

## Export process

Script:

`scripts/export_public_dashboard_data.py`

Source:

Microsoft Fabric Gold Warehouse analytical marts and KPI serving
views.

Destination:

`web/data/`

## Public datasets

| File | Rows |
|---|---:|
| `borough-current.json` | 10 |
| `borough-kpis.json` | 120 |
| `kpi-definitions.json` | 12 |
| `skills-supply.json` | 60 |
| `mbacc-pathways.json` | 70 |
| `youth-transition.json` | 80 |
| `borough-opportunity.json` | 860 |

Additional metadata is written to:

`web/data/metadata.json`

## Current reporting periods

- Apprenticeships: 2025/26
- Youth transition: 2026
- Labour market: Apr 2025-Mar 2026
- Qualifications: Jan-Dec 2025

The web-serving data retains the actual period associated with each
indicator rather than forcing different official statistics into one
reporting period.

## Disclosure governance

Suppressed and unavailable official statistics remain null.

The public extract does not reconstruct suppressed values.

## Security boundary

The browser receives only governed public analytical extracts.

The following are not exposed to the web application:

- Fabric access tokens
- tenant authentication
- SQL credentials
- Warehouse connection strings
- Bronze raw data
- Silver engineering data

## Delivery architecture

Microsoft Fabric
→ Gold Warehouse
→ governed analytical marts
→ KPI serving layer
→ Python public-data export
→ JSON
→ Plotly.js web application
→ Cloudflare

## Result

Stage 8B passed all row-count and JSON validation checks.

The project is ready for the public Plotly.js application.
