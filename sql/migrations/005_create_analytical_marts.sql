/*
GM SkillsFlow
Migration 005: Gold analytical marts

Creates governed business-facing views over the dimensional Gold
model.

Important:
- DfE aggregate rows are selected explicitly.
- Overlapping age/demographic totals are never summed.
- Disclosure/suppression states remain visible.
- Different source period structures remain explicitly labelled.
*/


/* ============================================================
   DROP DEPENDENT VIEWS FIRST
   ============================================================ */

DROP VIEW IF EXISTS mart.borough_current_snapshot;
GO

DROP VIEW IF EXISTS mart.borough_opportunity;
GO

DROP VIEW IF EXISTS mart.youth_transition;
GO

DROP VIEW IF EXISTS mart.mbacc_pathway;
GO

DROP VIEW IF EXISTS mart.skills_supply;
GO


/* ============================================================
   1. SKILLS SUPPLY

   Grain:
     borough x apprenticeship academic year

   Uses explicit Total rows for:
     age_summary
     apps_level
     sex
   ============================================================ */

CREATE VIEW mart.skills_supply
AS

WITH base AS
(
    SELECT
        f.time_period_key,
        f.time_period,
        f.time_identifier,

        f.borough_key,
        f.borough_code,
        f.borough_name,

        f.starts_numeric_value
            AS apprenticeship_starts,

        f.starts_value_status
            AS apprenticeship_starts_status,

        f.achievements_numeric_value
            AS apprenticeship_achievements,

        f.achievements_value_status
            AS apprenticeship_achievements_status,

        f.participation_numeric_value
            AS apprenticeship_participation,

        f.participation_value_status
            AS apprenticeship_participation_status,

        f.source_snapshot_date

    FROM fact.apprenticeship_lad AS f

    WHERE f.age_summary = 'Total'
      AND f.apps_level = 'Total'
      AND f.sex = 'Total'
),

trend AS
(
    SELECT
        b.*,

        LAG(
            b.apprenticeship_starts
        ) OVER (
            PARTITION BY b.borough_key
            ORDER BY b.time_period
        ) AS previous_starts,

        LAG(
            b.apprenticeship_achievements
        ) OVER (
            PARTITION BY b.borough_key
            ORDER BY b.time_period
        ) AS previous_achievements

    FROM base AS b
)

SELECT
    t.time_period_key,
    t.time_period,
    t.time_identifier,

    t.borough_key,
    t.borough_code,
    t.borough_name,

    t.apprenticeship_starts,
    t.apprenticeship_starts_status,

    t.apprenticeship_achievements,
    t.apprenticeship_achievements_status,

    t.apprenticeship_participation,
    t.apprenticeship_participation_status,

    t.previous_starts,

    CASE
        WHEN t.apprenticeship_starts IS NOT NULL
         AND t.previous_starts IS NOT NULL
        THEN
            t.apprenticeship_starts
            - t.previous_starts
    END AS starts_change,

    CASE
        WHEN t.previous_starts > 0
        THEN
            100.0
            * (
                t.apprenticeship_starts
                - t.previous_starts
            )
            / t.previous_starts
    END AS starts_change_pct,

    t.previous_achievements,

    CASE
        WHEN t.apprenticeship_achievements IS NOT NULL
         AND t.previous_achievements IS NOT NULL
        THEN
            t.apprenticeship_achievements
            - t.previous_achievements
    END AS achievements_change,

    CASE
        WHEN t.previous_achievements > 0
        THEN
            100.0
            * (
                t.apprenticeship_achievements
                - t.previous_achievements
            )
            / t.previous_achievements
    END AS achievements_change_pct,

    CASE
        WHEN t.time_period = (
            SELECT MAX(time_period)
            FROM fact.apprenticeship_lad
            WHERE age_summary = 'Total'
              AND apps_level = 'Total'
              AND sex = 'Total'
        )
        THEN 1
        ELSE 0
    END AS is_latest_period,

    t.source_snapshot_date

FROM trend AS t;
GO


/* ============================================================
   2. MBACC PATHWAY

   Grain:
     borough x academic year x MBacc gateway

   Only source rows already resolved through the governed
   SSA-to-MBacc crosswalk are included.

   Aggregate measures are returned only when every contributing
   SSA component is numerically reportable.
   ============================================================ */

CREATE VIEW mart.mbacc_pathway
AS

SELECT
    f.time_period_key,
    f.time_period,
    f.time_identifier,

    f.borough_key,
    f.borough_code,
    f.borough_name,

    f.gateway_key,
    g.gateway_code,
    g.gateway_name,

    COUNT_BIG(*)
        AS contributing_ssa_count,

    COUNT(f.starts_numeric_value)
        AS reportable_starts_components,

    CASE
        WHEN COUNT_BIG(*)
           = COUNT(f.starts_numeric_value)
        THEN SUM(f.starts_numeric_value)
    END AS apprenticeship_starts,

    CASE
        WHEN COUNT_BIG(*)
           = COUNT(f.starts_numeric_value)
        THEN 'reported'
        ELSE 'partial_or_suppressed'
    END AS apprenticeship_starts_status,

    COUNT(f.achievements_numeric_value)
        AS reportable_achievement_components,

    CASE
        WHEN COUNT_BIG(*)
           = COUNT(f.achievements_numeric_value)
        THEN SUM(f.achievements_numeric_value)
    END AS apprenticeship_achievements,

    CASE
        WHEN COUNT_BIG(*)
           = COUNT(f.achievements_numeric_value)
        THEN 'reported'
        ELSE 'partial_or_suppressed'
    END AS apprenticeship_achievements_status,

    CASE
        WHEN f.time_period = (
            SELECT MAX(time_period)
            FROM fact.apprenticeship_detail
        )
        THEN 1
        ELSE 0
    END AS is_latest_period,

    MAX(f.source_snapshot_date)
        AS source_snapshot_date

FROM fact.apprenticeship_detail AS f

JOIN dim.mbacc_gateway AS g
  ON f.gateway_key = g.gateway_key

WHERE f.apps_level = 'Total'
  AND f.sex = 'Total'
  AND f.ethnicity_major = 'Total'
  AND f.ssa_tier_1 <> 'Total'
  AND f.gateway_key IS NOT NULL

GROUP BY
    f.time_period_key,
    f.time_period,
    f.time_identifier,

    f.borough_key,
    f.borough_code,
    f.borough_name,

    f.gateway_key,
    g.gateway_code,
    g.gateway_name;
GO


/* ============================================================
   3. YOUTH TRANSITION

   Grain:
     borough x calendar year

   Uses:
     age = 16 to 17
     characteristic_grouping = Total
     characteristic = Total

   This avoids overlap with the individual age-16 and age-17
   observations.
   ============================================================ */

CREATE VIEW mart.youth_transition
AS

WITH neet_total AS
(
    SELECT
        time_period_key,
        time_period,
        time_identifier,

        borough_key,
        borough_code,
        borough_name,

        avg_cohort_count_numeric_value
            AS cohort_count,

        avg_cohort_count_value_status
            AS cohort_count_status,

        avg_neet_nk_count_numeric_value
            AS neet_or_not_known_count,

        avg_neet_nk_count_value_status
            AS neet_or_not_known_count_status,

        avg_neet_count_numeric_value
            AS neet_count,

        avg_neet_count_value_status
            AS neet_count_status,

        avg_nk_count_numeric_value
            AS not_known_count,

        avg_nk_count_value_status
            AS not_known_count_status,

        neet_nk_percent_numeric_value
            AS neet_or_not_known_percent,

        neet_nk_percent_value_status
            AS neet_or_not_known_percent_status,

        neet_percent_numeric_value
            AS neet_percent,

        neet_percent_value_status
            AS neet_percent_status,

        nk_percent_numeric_value
            AS not_known_percent,

        nk_percent_value_status
            AS not_known_percent_status,

        annual_change_neet_nk_percent_numeric_value
            AS annual_change_neet_or_not_known_pp,

        annual_change_neet_nk_percent_value_status
            AS annual_change_neet_or_not_known_status,

        source_snapshot_date
            AS neet_snapshot_date

    FROM fact.neet

    WHERE age = '16 to 17'
      AND characteristic_grouping = 'Total'
      AND characteristic = 'Total'
),

participation_total AS
(
    SELECT
        time_period_key,
        borough_key,

        cohort_count_numeric_value
            AS participation_cohort_count,

        cohort_count_value_status
            AS participation_cohort_count_status,

        total_in_education_and_training_count_numeric_value
            AS education_training_count,

        total_in_education_and_training_count_value_status
            AS education_training_count_status,

        total_in_education_and_training_percent_numeric_value
            AS education_training_percent,

        total_in_education_and_training_percent_value_status
            AS education_training_percent_status,

        annual_change_percent_numeric_value
            AS annual_change_education_training_pp,

        annual_change_percent_value_status
            AS annual_change_education_training_status,

        source_snapshot_date
            AS participation_snapshot_date

    FROM fact.participation

    WHERE age = '16 to 17'
      AND characteristic_grouping = 'Total'
      AND characteristic = 'Total'
)

SELECT
    n.time_period_key,
    n.time_period,
    n.time_identifier,

    n.borough_key,
    n.borough_code,
    n.borough_name,

    n.cohort_count,
    n.cohort_count_status,

    n.neet_or_not_known_count,
    n.neet_or_not_known_count_status,

    n.neet_count,
    n.neet_count_status,

    n.not_known_count,
    n.not_known_count_status,

    n.neet_or_not_known_percent,
    n.neet_or_not_known_percent_status,

    n.neet_percent,
    n.neet_percent_status,

    n.not_known_percent,
    n.not_known_percent_status,

    n.annual_change_neet_or_not_known_pp,
    n.annual_change_neet_or_not_known_status,

    p.participation_cohort_count,
    p.participation_cohort_count_status,

    p.education_training_count,
    p.education_training_count_status,

    p.education_training_percent,
    p.education_training_percent_status,

    p.annual_change_education_training_pp,
    p.annual_change_education_training_status,

    CASE
        WHEN n.time_period = (
            SELECT MAX(time_period)
            FROM fact.neet
            WHERE age = '16 to 17'
              AND characteristic_grouping = 'Total'
              AND characteristic = 'Total'
        )
        THEN 1
        ELSE 0
    END AS is_latest_period,

    n.neet_snapshot_date,
    p.participation_snapshot_date

FROM neet_total AS n

JOIN participation_total AS p
  ON n.time_period_key = p.time_period_key
 AND n.borough_key = p.borough_key;
GO


/* ============================================================
   4. BOROUGH OPPORTUNITY

   Grain:
     borough x Nomis labour-market period

   Pivots the five governed APS variables into an analytical
   borough labour-market profile.
   ============================================================ */

CREATE VIEW mart.borough_opportunity
AS

WITH pivoted AS
(
    SELECT
        f.labour_market_period_key,

        f.date,
        f.date_name,
        f.date_type,

        f.borough_key,
        f.borough_code,
        f.borough_name,

        MAX(
            CASE
                WHEN f.variable_code = '45'
                THEN f.obs_numeric_value
            END
        ) AS employment_rate,

        MAX(
            CASE
                WHEN f.variable_code = '45'
                THEN f.obs_value_status
            END
        ) AS employment_rate_status,

        MAX(
            CASE
                WHEN f.variable_code = '84'
                THEN f.obs_numeric_value
            END
        ) AS unemployment_rate,

        MAX(
            CASE
                WHEN f.variable_code = '84'
                THEN f.obs_value_status
            END
        ) AS unemployment_rate_status,

        MAX(
            CASE
                WHEN f.variable_code = '111'
                THEN f.obs_numeric_value
            END
        ) AS economic_inactivity_rate,

        MAX(
            CASE
                WHEN f.variable_code = '111'
                THEN f.obs_value_status
            END
        ) AS economic_inactivity_rate_status,

        MAX(
            CASE
                WHEN f.variable_code = '2010'
                THEN f.obs_numeric_value
            END
        ) AS rqf3_plus_rate,

        MAX(
            CASE
                WHEN f.variable_code = '2010'
                THEN f.obs_value_status
            END
        ) AS rqf3_plus_rate_status,

        MAX(
            CASE
                WHEN f.variable_code = '1902'
                THEN f.obs_numeric_value
            END
        ) AS rqf4_plus_rate,

        MAX(
            CASE
                WHEN f.variable_code = '1902'
                THEN f.obs_value_status
            END
        ) AS rqf4_plus_rate_status,

        MAX(f.source_snapshot_date)
            AS source_snapshot_date

    FROM fact.labour_market_aps AS f

    GROUP BY
        f.labour_market_period_key,

        f.date,
        f.date_name,
        f.date_type,

        f.borough_key,
        f.borough_code,
        f.borough_name
)

SELECT
    p.*,

    CASE
        WHEN p.rqf3_plus_rate IS NOT NULL
         AND p.rqf4_plus_rate IS NOT NULL
        THEN
            p.rqf3_plus_rate
            - p.rqf4_plus_rate
    END AS rqf3_plus_minus_rqf4_plus_pp,

    CASE
        WHEN p.date = (
            SELECT MAX(date)
            FROM fact.labour_market_aps
        )
        THEN 1
        ELSE 0
    END AS is_latest_period

FROM pivoted AS p;
GO


/* ============================================================
   5. CURRENT BOROUGH SNAPSHOT

   Grain:
     one row per current Greater Manchester borough

   IMPORTANT:
   This is a multi-source current snapshot.

   Source periods are deliberately retained separately:
   - apprenticeship academic year
   - youth-transition calendar year
   - labour-market APS period
   - qualification APS period

   The latest labour-market and qualification periods are selected
   independently because Nomis publishes these indicators on
   different reporting cycles.
   ============================================================ */

CREATE VIEW mart.borough_current_snapshot
AS

WITH latest_skills AS
(
    SELECT *
    FROM mart.skills_supply
    WHERE is_latest_period = 1
),

latest_youth AS
(
    SELECT *
    FROM mart.youth_transition
    WHERE is_latest_period = 1
),

latest_labour AS
(
    SELECT *
    FROM mart.borough_opportunity

    WHERE date = (
        SELECT MAX(date)
        FROM mart.borough_opportunity
        WHERE employment_rate IS NOT NULL
          AND unemployment_rate IS NOT NULL
          AND economic_inactivity_rate IS NOT NULL
    )

      AND employment_rate IS NOT NULL
      AND unemployment_rate IS NOT NULL
      AND economic_inactivity_rate IS NOT NULL
),

latest_qualification AS
(
    SELECT *
    FROM mart.borough_opportunity

    WHERE date = (
        SELECT MAX(date)
        FROM mart.borough_opportunity
        WHERE rqf3_plus_rate IS NOT NULL
          AND rqf4_plus_rate IS NOT NULL
    )

      AND rqf3_plus_rate IS NOT NULL
      AND rqf4_plus_rate IS NOT NULL
),

latest_mbacc AS
(
    SELECT
        borough_key,

        MAX(time_period)
            AS mbacc_period,

        COUNT_BIG(*)
            AS mbacc_gateway_count,

        CASE
            WHEN COUNT_BIG(*)
               = COUNT(apprenticeship_starts)
            THEN SUM(apprenticeship_starts)
        END AS mbacc_mapped_starts,

        CASE
            WHEN COUNT_BIG(*)
               = COUNT(apprenticeship_starts)
            THEN 'reported'
            ELSE 'partial_or_suppressed'
        END AS mbacc_mapped_starts_status,

        CASE
            WHEN COUNT_BIG(*)
               = COUNT(apprenticeship_achievements)
            THEN SUM(apprenticeship_achievements)
        END AS mbacc_mapped_achievements,

        CASE
            WHEN COUNT_BIG(*)
               = COUNT(apprenticeship_achievements)
            THEN 'reported'
            ELSE 'partial_or_suppressed'
        END AS mbacc_mapped_achievements_status

    FROM mart.mbacc_pathway

    WHERE is_latest_period = 1

    GROUP BY
        borough_key
)

SELECT
    b.borough_key,
    b.borough_code,
    b.borough_name,

    /* Apprenticeship supply */

    s.time_period
        AS apprenticeship_period,

    s.apprenticeship_starts,
    s.apprenticeship_starts_status,

    s.apprenticeship_achievements,
    s.apprenticeship_achievements_status,

    s.apprenticeship_participation,
    s.apprenticeship_participation_status,

    /* MBacc pathway */

    m.mbacc_period,
    m.mbacc_gateway_count,

    m.mbacc_mapped_starts,
    m.mbacc_mapped_starts_status,

    m.mbacc_mapped_achievements,
    m.mbacc_mapped_achievements_status,

    /* Youth transition */

    y.time_period
        AS youth_transition_period,

    y.neet_percent,
    y.neet_percent_status,

    y.neet_or_not_known_percent,
    y.neet_or_not_known_percent_status,

    y.education_training_percent,
    y.education_training_percent_status,

    /* Labour market */

    l.date
        AS labour_market_period,

    l.date_name
        AS labour_market_period_name,

    l.employment_rate,
    l.employment_rate_status,

    l.unemployment_rate,
    l.unemployment_rate_status,

    l.economic_inactivity_rate,
    l.economic_inactivity_rate_status,

    /* Qualifications */

    q.date
        AS qualification_period,

    q.date_name
        AS qualification_period_name,

    q.rqf3_plus_rate,
    q.rqf3_plus_rate_status,

    q.rqf4_plus_rate,
    q.rqf4_plus_rate_status,

    q.rqf3_plus_minus_rqf4_plus_pp

FROM dim.borough AS b

LEFT JOIN latest_skills AS s
  ON b.borough_key = s.borough_key

LEFT JOIN latest_mbacc AS m
  ON b.borough_key = m.borough_key

LEFT JOIN latest_youth AS y
  ON b.borough_key = y.borough_key

LEFT JOIN latest_labour AS l
  ON b.borough_key = l.borough_key

LEFT JOIN latest_qualification AS q
  ON b.borough_key = q.borough_key

WHERE b.is_current = 1;
GO
