# GM SkillsFlow - Gold Fact Model Checkpoint

**Date:** 20 September 2026  
**Stage:** 7D - Gold Fact Dimensionalisation  
**Status:** PASS

## Objective

Complete the Gold star-schema fact model by introducing governed
surrogate-key relationships between the analytical fact tables and
their dimensions while preserving source lineage, disclosure status
and existing row counts.

## Fabric artefact

- Notebook: `nb_gold_fact_model`
- Notebook ID: `0d0e79c8-a827-4d52-b96c-87b46416eec7`
- Successful job ID: `378cca36-a90b-43d8-8b6d-4fb4bb89baa3`
- Status: `Completed`
- Failure reason: `None`

## Gold schema migration

Migration:

`sql/migrations/004_dimensionalise_gold_facts.sql`

The migration introduced nullable surrogate-key columns to the
existing Gold fact tables before governed population by the Fabric
notebook.

### fact.apprenticeship_lad

- `borough_key`
- `time_period_key`
- `apprenticeship_level_key`

### fact.apprenticeship_detail

- `borough_key`
- `time_period_key`
- `apprenticeship_level_key`
- `ssa_subject_key`
- `gateway_key`

### fact.neet

- `borough_key`
- `time_period_key`

### fact.participation

- `borough_key`
- `time_period_key`

### fact.labour_market_aps

- `borough_key`
- `labour_market_period_key`
- `labour_market_variable_key`

## New Gold dimensions

| Dimension | Rows |
|---|---:|
| `dim.labour_market_period` | 86 |
| `dim.labour_market_variable` | 5 |

Nomis labour-market periods are deliberately modelled separately
from the DfE education time-period dimension because the two sources
use different temporal structures.

## Fact reconciliation

| Fact | Verified rows |
|---|---:|
| `fact.apprenticeship_lad` | 2,880 |
| `fact.apprenticeship_detail` | 11,760 |
| `fact.neet` | 1,754 |
| `fact.participation` | 1,755 |
| `fact.labour_market_aps` | 4,300 |

All row counts were preserved after dimensionalisation.

## Required-key validation

All required Gold surrogate-key relationships returned zero
unresolved rows.

This includes:

- borough relationships across all five facts
- DfE time-period relationships
- apprenticeship-level relationships
- SSA subject relationships
- Nomis labour-market period relationships
- Nomis labour-market variable relationships

## MBacc governance

The governed analytical SSA-to-MBacc mapping produced:

- MBacc-mapped apprenticeship-detail rows: **8,400**
- intentionally unmapped rows: **3,360**
- unresolved SSA rows: **0**
- invalid MBacc gateway relationships: **0**

Null `gateway_key` values are therefore retained where the governed
crosswalk classifies a subject as cross-cutting, having no direct
mapping, or being an excluded aggregate. They are not treated as
failed foreign-key resolution.

## Nomis dimensional cardinality

`fact.labour_market_aps` successfully resolves to:

- 86 labour-market period keys
- 5 labour-market variable keys
- 10 Greater Manchester borough keys

## SCD position

The Gold dimensional core contains SCD Type 2-ready fields for the
governed dimensions.

Full Type 2 historical change-merging logic remains a later
implementation step and is not claimed as complete at this
checkpoint.

The source configuration design continues to use the Type 4 pattern:

- current state: `ctl.source_config`
- historical state: `hist.source_config`

## Result

Stage 7D passed all Warehouse reconciliation, key-resolution,
cardinality and governance checks.

The Gold layer now contains a governed dimensional core and
dimensionally linked fact model suitable for downstream analytical
marts and semantic modelling.
