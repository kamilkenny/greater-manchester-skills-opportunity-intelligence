# GM SkillsFlow

**Greater Manchester Skills & Opportunity Intelligence Platform**

GM SkillsFlow is an end-to-end analytics engineering project connecting
education, apprenticeships, skills supply and labour market opportunity
across Greater Manchester.

## Central Question

How effectively are Greater Manchester's education and skills pathways
connecting residents to the opportunities emerging across the city
region, and where are the gaps across its ten boroughs?

## Geographic Coverage

The platform covers:

- Bolton
- Bury
- Manchester
- Oldham
- Rochdale
- Salford
- Stockport
- Tameside
- Trafford
- Wigan

## Core Data Sources

| ID | Source | Provider | Acquisition |
|---|---|---|---|
| SRC01 | Apprenticeships Local Authority | DfE | Direct CSV |
| SRC02 | Detailed Apprenticeships | DfE | Direct CSV |
| SRC03 | NEET | DfE | Direct CSV |
| SRC04 | Education and Training Participation | DfE | Direct CSV |
| SRC05 | Annual Population Survey | ONS Nomis | REST API |
| SRC06 | MBacc Gateway Reference | GMCA | Controlled reference |

Source feasibility evidence is retained in
`docs/source_feasibility_register.csv`.

## Target Architecture

Public data sources flow through:

Microsoft Fabric Data Factory

→ Bronze Lakehouse

→ PySpark transformation and data quality

→ Silver Lakehouse

→ MBacc mapping layer

→ Gold Fabric Warehouse

→ Fabric Semantic Model / Power BI

and

→ Curated Parquet / JSON serving layer

→ Plotly Dash public application

## Planned Analytical Domains

GM SkillsFlow will support analysis of:

- apprenticeship starts, participation and achievements
- apprenticeship pathways by subject, level, sex and ethnicity
- NEET outcomes
- education and training participation
- employment
- unemployment
- economic inactivity
- RQF Level 3+ qualification share
- RQF Level 4+ qualification share
- MBacc gateway alignment
- borough-level skills and opportunity patterns
- platform health and data quality

## Engineering Principles

The platform is designed around:

- metadata-driven ingestion
- Bronze, Silver and Gold architecture
- immutable source history
- GSS geography business keys
- explicit disclosure-status handling
- automated data quality gates
- version-controlled reference mappings
- slowly changing dimensions where appropriate
- reusable metric definitions
- testing and CI/CD
- observability and auditability

## Repository Structure

| Path | Purpose |
|---|---|
| `.github/workflows/` | CI/CD workflows |
| `architecture/` | Architecture decisions and diagrams |
| `config/reference/` | Controlled reference data |
| `docs/` | Project and source documentation |
| `fabric/` | Fabric notebooks, pipelines and semantic assets |
| `src/gm_skills/` | Python engineering code |
| `sql/` | Warehouse modelling and quality SQL |
| `dashboard/` | Plotly Dash application |
| `tests/` | Unit, integration and data quality tests |

## Project Status

- Stage 0.1 Product definition: Complete
- Stage 0.2 Source feasibility: Complete
- Stage 1 Project foundation: In progress

All six core MVP sources have passed initial feasibility validation.

## Data Handling

DfE disclosure values such as `low`, `c` and `z` are not interpreted as
numeric zero.

The analytical model will retain both the original source value and an
explicit value-status classification.

Nomis labour-market and qualification indicators use different reporting
period structures. Their original period definitions will therefore be
preserved.

## Disclaimer

This is an independent research and portfolio project.

It is not an official Greater Manchester Combined Authority, Department
for Education, Office for National Statistics or Nomis service.
