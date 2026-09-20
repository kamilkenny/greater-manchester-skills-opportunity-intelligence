# GM SkillsFlow - Gold Analytical Marts Checkpoint

**Date:** 20 September 2026  
**Stage:** 7E - Gold Analytical Marts  
**Status:** PASS

## Objective

Create governed business-facing analytical marts from the
dimensionally modelled Gold layer while preventing double-counting,
preserving disclosure status and retaining the distinct reporting
periods used by each official data source.

## Migration

`sql/migrations/005_create_analytical_marts.sql`

## Analytical marts

### mart.skills_supply

Grain:

`borough x apprenticeship academic year`

Verified rows:

**60**

The mart selects only explicit aggregate source records:

- `age_summary = 'Total'`
- `apps_level = 'Total'`
- `sex = 'Total'`

This prevents demographic and apprenticeship-level breakdowns from
being summed together with their published totals.

The mart includes:

- apprenticeship starts
- apprenticeship achievements
- apprenticeship participation
- year-on-year starts change
- year-on-year starts percentage change
- year-on-year achievement change
- year-on-year achievement percentage change
- disclosure status
- latest-period flag

## mart.mbacc_pathway

Grain:

`borough x academic year x MBacc gateway`

Verified rows:

**70**

The mart uses the governed analytical SSA-to-MBacc mapping and only
uses source records where:

- apprenticeship level is `Total`
- sex is `Total`
- ethnicity is `Total`
- SSA is not the aggregate `Total`
- a governed MBacc gateway mapping exists

Suppression-aware aggregation is applied.

A gateway total is returned only when every contributing SSA value is
numerically reportable. Otherwise the aggregate remains null and its
status is recorded as:

`partial_or_suppressed`

This avoids disclosure leakage through aggregation.

## mart.youth_transition

Grain:

`borough x calendar year`

Verified rows:

**80**

The mart combines NEET and education/training participation measures.

It selects:

- `age = '16 to 17'`
- `characteristic_grouping = 'Total'`
- `characteristic = 'Total'`

This prevents the combined 16-to-17 population from being added to
the separate age-16 and age-17 observations.

Measures include:

- NEET count
- not-known count
- NEET or not-known count
- NEET percentage
- not-known percentage
- NEET or not-known percentage
- education/training participation count
- education/training participation percentage
- annual percentage-point changes
- source disclosure status

## mart.borough_opportunity

Grain:

`borough x Nomis APS reporting period`

Verified rows:

**860**

The mart pivots the five governed Nomis labour-market variables:

- employment rate, variable 45
- unemployment rate, variable 84
- economic inactivity rate, variable 111
- RQF4+ rate, variable 1902
- RQF3+ rate, variable 2010

The mart retains the original Nomis reporting period and observation
status for analytical traceability.

## mart.borough_current_snapshot

Grain:

`one row per current Greater Manchester borough`

Verified rows:

**10**

This mart provides a dashboard-ready current intelligence layer while
retaining the actual reporting period for every source domain.

Current source periods are:

- apprenticeship supply: `202526`
- MBacc pathway: `202526`
- youth transition: `2026`
- labour market: `2026-03`, Apr 2025-Mar 2026
- qualifications: `2025-12`, Jan 2025-Dec 2025

The labour-market and qualification periods are deliberately selected
independently.

Employment, unemployment and inactivity are fully reported for all
ten boroughs at `2026-03`.

RQF3+ and RQF4+ are not numerically reported at `2026-03` and have
Nomis status indicating missing values. Their latest fully reported
period is therefore selected independently as `2025-12`.

This prevents asynchronous official statistics from being presented
as though they shared one reporting period.

## MBacc suppression governance

The latest MBacc pathway data contains partial or suppressed
components in the Creative Culture and Sport gateway for some
boroughs.

The analytical mart retains these as null aggregate values with
`partial_or_suppressed` status instead of inferring or reconstructing
suppressed values.

The current snapshot therefore preserves official disclosure
behaviour.

## Verification results

| Mart | Rows | Result |
|---|---:|---|
| `mart.skills_supply` | 60 | PASS |
| `mart.mbacc_pathway` | 70 | PASS |
| `mart.youth_transition` | 80 | PASS |
| `mart.borough_opportunity` | 860 | PASS |
| `mart.borough_current_snapshot` | 10 | PASS |

Latest-period coverage also passed:

| Mart | Latest rows |
|---|---:|
| `mart.skills_supply` | 10 |
| `mart.mbacc_pathway` | 70 |
| `mart.youth_transition` | 10 |
| `mart.borough_opportunity` | 10 |

The corrected current snapshot contains complete values for all ten
boroughs for:

- employment rate
- unemployment rate
- economic inactivity rate
- RQF3+
- RQF4+

## Result

Stage 7E passed structural, temporal, disclosure and semantic
validation.

The Gold layer now contains business-facing marts capable of
supporting borough, youth-transition, apprenticeship, MBacc,
qualification and labour-market analysis without obscuring the
different reporting structures of the underlying official datasets.
