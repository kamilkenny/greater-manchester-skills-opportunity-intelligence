/*
GM SkillsFlow
Migration 006: KPI semantic serving layer

Creates governed KPI metadata and a long-format current borough KPI
view suitable for Power BI, dashboard and API consumption.

No composite borough score is created.
*/


DROP VIEW IF EXISTS mart.borough_kpi_current;
GO

DROP VIEW IF EXISTS mart.kpi_definition;
GO


/* ============================================================
   KPI DEFINITIONS
   ============================================================ */

CREATE VIEW mart.kpi_definition
AS

SELECT *
FROM
(
    VALUES

    (
        'APP_STARTS',
        'Apprenticeship Starts',
        'Skills Supply',
        'count',
        'DfE Apprenticeships',
        'academic_year',
        'Number of apprenticeship starts.',
        'contextual'
    ),

    (
        'APP_ACHIEVEMENTS',
        'Apprenticeship Achievements',
        'Skills Supply',
        'count',
        'DfE Apprenticeships',
        'academic_year',
        'Number of apprenticeship achievements.',
        'contextual'
    ),

    (
        'APP_PARTICIPATION',
        'Apprenticeship Participation',
        'Skills Supply',
        'count',
        'DfE Apprenticeships',
        'academic_year',
        'Number participating in apprenticeships.',
        'contextual'
    ),

    (
        'MBACC_STARTS',
        'MBacc-mapped Apprenticeship Starts',
        'MBacc Pathways',
        'count',
        'DfE Apprenticeships + governed MBacc crosswalk',
        'academic_year',
        'Apprenticeship starts mapped to governed MBacc pathways.',
        'contextual'
    ),

    (
        'MBACC_ACHIEVEMENTS',
        'MBacc-mapped Apprenticeship Achievements',
        'MBacc Pathways',
        'count',
        'DfE Apprenticeships + governed MBacc crosswalk',
        'academic_year',
        'Apprenticeship achievements mapped to governed MBacc pathways.',
        'contextual'
    ),

    (
        'NEET_RATE',
        'NEET Rate',
        'Youth Transition',
        'percent',
        'DfE NEET',
        'calendar_year',
        'Percentage of young people aged 16 to 17 recorded as NEET.',
        'lower_is_generally_favourable'
    ),

    (
        'EDU_TRAINING_RATE',
        'Education and Training Participation Rate',
        'Youth Transition',
        'percent',
        'DfE Participation',
        'calendar_year',
        'Percentage of young people aged 16 to 17 participating in education or training.',
        'higher_is_generally_favourable'
    ),

    (
        'EMPLOYMENT_RATE',
        'Employment Rate',
        'Labour Market',
        'percent',
        'ONS Nomis APS',
        'rolling_annual',
        'Employment rate for people aged 16 to 64.',
        'higher_is_generally_favourable'
    ),

    (
        'UNEMPLOYMENT_RATE',
        'Unemployment Rate',
        'Labour Market',
        'percent',
        'ONS Nomis APS',
        'rolling_annual',
        'Unemployment rate for people aged 16 to 64.',
        'lower_is_generally_favourable'
    ),

    (
        'INACTIVITY_RATE',
        'Economic Inactivity Rate',
        'Labour Market',
        'percent',
        'ONS Nomis APS',
        'rolling_annual',
        'Economic inactivity rate for people aged 16 to 64.',
        'contextual'
    ),

    (
        'RQF3_PLUS_RATE',
        'RQF3+ Qualification Rate',
        'Qualifications',
        'percent',
        'ONS Nomis APS',
        'calendar_year',
        'Percentage of people aged 16 to 64 qualified to RQF level 3 or above.',
        'higher_is_generally_favourable'
    ),

    (
        'RQF4_PLUS_RATE',
        'RQF4+ Qualification Rate',
        'Qualifications',
        'percent',
        'ONS Nomis APS',
        'calendar_year',
        'Percentage of people aged 16 to 64 qualified to RQF level 4 or above.',
        'higher_is_generally_favourable'
    )

) AS k
(
    kpi_code,
    kpi_name,
    domain_name,
    unit_name,
    source_name,
    period_type,
    definition,
    interpretation
);
GO


/* ============================================================
   CURRENT BOROUGH KPI SERVING VIEW

   Grain:
       borough x KPI

   Period information is retained per KPI.
   ============================================================ */

CREATE VIEW mart.borough_kpi_current
AS

SELECT
    borough_key,
    borough_code,
    borough_name,

    'APP_STARTS' AS kpi_code,
    CAST(apprenticeship_starts AS FLOAT) AS kpi_value,
    apprenticeship_starts_status AS value_status,
    apprenticeship_period AS period_code,
    'Academic year ' + apprenticeship_period AS period_name

FROM mart.borough_current_snapshot

UNION ALL

SELECT
    borough_key,
    borough_code,
    borough_name,

    'APP_ACHIEVEMENTS',
    CAST(apprenticeship_achievements AS FLOAT),
    apprenticeship_achievements_status,
    apprenticeship_period,
    'Academic year ' + apprenticeship_period

FROM mart.borough_current_snapshot

UNION ALL

SELECT
    borough_key,
    borough_code,
    borough_name,

    'APP_PARTICIPATION',
    CAST(apprenticeship_participation AS FLOAT),
    apprenticeship_participation_status,
    apprenticeship_period,
    'Academic year ' + apprenticeship_period

FROM mart.borough_current_snapshot

UNION ALL

SELECT
    borough_key,
    borough_code,
    borough_name,

    'MBACC_STARTS',
    CAST(mbacc_mapped_starts AS FLOAT),
    mbacc_mapped_starts_status,
    mbacc_period,
    'Academic year ' + mbacc_period

FROM mart.borough_current_snapshot

UNION ALL

SELECT
    borough_key,
    borough_code,
    borough_name,

    'MBACC_ACHIEVEMENTS',
    CAST(mbacc_mapped_achievements AS FLOAT),
    mbacc_mapped_achievements_status,
    mbacc_period,
    'Academic year ' + mbacc_period

FROM mart.borough_current_snapshot

UNION ALL

SELECT
    borough_key,
    borough_code,
    borough_name,

    'NEET_RATE',
    CAST(neet_percent AS FLOAT),
    neet_percent_status,
    youth_transition_period,
    'Calendar year ' + youth_transition_period

FROM mart.borough_current_snapshot

UNION ALL

SELECT
    borough_key,
    borough_code,
    borough_name,

    'EDU_TRAINING_RATE',
    CAST(education_training_percent AS FLOAT),
    education_training_percent_status,
    youth_transition_period,
    'Calendar year ' + youth_transition_period

FROM mart.borough_current_snapshot

UNION ALL

SELECT
    borough_key,
    borough_code,
    borough_name,

    'EMPLOYMENT_RATE',
    CAST(employment_rate AS FLOAT),
    employment_rate_status,
    labour_market_period,
    labour_market_period_name

FROM mart.borough_current_snapshot

UNION ALL

SELECT
    borough_key,
    borough_code,
    borough_name,

    'UNEMPLOYMENT_RATE',
    CAST(unemployment_rate AS FLOAT),
    unemployment_rate_status,
    labour_market_period,
    labour_market_period_name

FROM mart.borough_current_snapshot

UNION ALL

SELECT
    borough_key,
    borough_code,
    borough_name,

    'INACTIVITY_RATE',
    CAST(economic_inactivity_rate AS FLOAT),
    economic_inactivity_rate_status,
    labour_market_period,
    labour_market_period_name

FROM mart.borough_current_snapshot

UNION ALL

SELECT
    borough_key,
    borough_code,
    borough_name,

    'RQF3_PLUS_RATE',
    CAST(rqf3_plus_rate AS FLOAT),
    rqf3_plus_rate_status,
    qualification_period,
    qualification_period_name

FROM mart.borough_current_snapshot

UNION ALL

SELECT
    borough_key,
    borough_code,
    borough_name,

    'RQF4_PLUS_RATE',
    CAST(rqf4_plus_rate AS FLOAT),
    rqf4_plus_rate_status,
    qualification_period,
    qualification_period_name

FROM mart.borough_current_snapshot;
GO
