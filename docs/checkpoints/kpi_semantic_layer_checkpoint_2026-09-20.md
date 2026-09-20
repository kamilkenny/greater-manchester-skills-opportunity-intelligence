# GM SkillsFlow - KPI Semantic Layer Checkpoint

**Date:** 20 September 2026  
**Stage:** 7F - KPI Semantic Serving Layer  
**Status:** PASS

## Objective

Create a governed KPI serving layer over the validated Gold analytical
marts for consumption by the public web dashboard and, later, Power BI.

## Migration

`sql/migrations/006_create_kpi_semantic_layer.sql`

## Objects

### mart.kpi_definition

Verified KPI definitions: **12**

The metadata layer documents:

- KPI code
- KPI name
- analytical domain
- unit
- source
- period type
- business definition
- interpretation guidance

No composite borough score is created.

### mart.borough_kpi_current

Grain:

`borough x KPI`

Verified observations: **120**

Coverage:

- 10 Greater Manchester boroughs
- 12 KPIs

## KPI coverage

- APP_STARTS
- APP_ACHIEVEMENTS
- APP_PARTICIPATION
- MBACC_STARTS
- MBACC_ACHIEVEMENTS
- NEET_RATE
- EDU_TRAINING_RATE
- EMPLOYMENT_RATE
- UNEMPLOYMENT_RATE
- INACTIVITY_RATE
- RQF3_PLUS_RATE
- RQF4_PLUS_RATE

## Period governance

The serving layer retains the actual reporting period associated with
each indicator.

Current periods include:

- Apprenticeships: 2025/26 academic year
- Youth transition: 2026 calendar year
- Labour market: Apr 2025-Mar 2026
- Qualifications: Jan-Dec 2025

This prevents indicators from different statistical reporting cycles
from being presented as though they referred to the same period.

## Disclosure governance

MBacc aggregates retain null values where source suppression prevents a
fully reportable aggregate.

Current semantic-layer coverage:

- MBACC_STARTS: 7 numeric borough values
- MBACC_ACHIEVEMENTS: 7 numeric borough values

The remaining values preserve governed disclosure status.

## Verification

- KPI definitions: 12 - PASS
- KPI observations: 120 - PASS
- Boroughs: 10 - PASS
- Distinct KPIs: 12 - PASS
- Period profile: PASS

## Delivery decision

The KPI semantic layer will first serve the public Plotly Dash web
application.

Power BI development is intentionally deferred until after the public
web platform is complete and deployed.
