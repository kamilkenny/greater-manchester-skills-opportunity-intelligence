/*
GM SkillsFlow
Migration 004: Dimensionalise Gold fact tables

Adds nullable surrogate-key columns required by the mature
Gold star schema.

Columns remain nullable during the migration so the existing
verified fact data remains available until the governed Fabric
fact-model notebook successfully populates the relationships.
*/

BEGIN TRANSACTION;

/* Apprenticeship LAD */

IF NOT EXISTS (
    SELECT 1
    FROM sys.columns
    WHERE object_id = OBJECT_ID('fact.apprenticeship_lad')
      AND name = 'borough_key'
)
    ALTER TABLE fact.apprenticeship_lad
    ADD borough_key BIGINT NULL;

IF NOT EXISTS (
    SELECT 1
    FROM sys.columns
    WHERE object_id = OBJECT_ID('fact.apprenticeship_lad')
      AND name = 'time_period_key'
)
    ALTER TABLE fact.apprenticeship_lad
    ADD time_period_key BIGINT NULL;

IF NOT EXISTS (
    SELECT 1
    FROM sys.columns
    WHERE object_id = OBJECT_ID('fact.apprenticeship_lad')
      AND name = 'apprenticeship_level_key'
)
    ALTER TABLE fact.apprenticeship_lad
    ADD apprenticeship_level_key BIGINT NULL;


/* Apprenticeship detail */

IF NOT EXISTS (
    SELECT 1
    FROM sys.columns
    WHERE object_id = OBJECT_ID('fact.apprenticeship_detail')
      AND name = 'borough_key'
)
    ALTER TABLE fact.apprenticeship_detail
    ADD borough_key BIGINT NULL;

IF NOT EXISTS (
    SELECT 1
    FROM sys.columns
    WHERE object_id = OBJECT_ID('fact.apprenticeship_detail')
      AND name = 'time_period_key'
)
    ALTER TABLE fact.apprenticeship_detail
    ADD time_period_key BIGINT NULL;

IF NOT EXISTS (
    SELECT 1
    FROM sys.columns
    WHERE object_id = OBJECT_ID('fact.apprenticeship_detail')
      AND name = 'apprenticeship_level_key'
)
    ALTER TABLE fact.apprenticeship_detail
    ADD apprenticeship_level_key BIGINT NULL;

IF NOT EXISTS (
    SELECT 1
    FROM sys.columns
    WHERE object_id = OBJECT_ID('fact.apprenticeship_detail')
      AND name = 'ssa_subject_key'
)
    ALTER TABLE fact.apprenticeship_detail
    ADD ssa_subject_key BIGINT NULL;

IF NOT EXISTS (
    SELECT 1
    FROM sys.columns
    WHERE object_id = OBJECT_ID('fact.apprenticeship_detail')
      AND name = 'gateway_key'
)
    ALTER TABLE fact.apprenticeship_detail
    ADD gateway_key BIGINT NULL;


/* NEET */

IF NOT EXISTS (
    SELECT 1
    FROM sys.columns
    WHERE object_id = OBJECT_ID('fact.neet')
      AND name = 'borough_key'
)
    ALTER TABLE fact.neet
    ADD borough_key BIGINT NULL;

IF NOT EXISTS (
    SELECT 1
    FROM sys.columns
    WHERE object_id = OBJECT_ID('fact.neet')
      AND name = 'time_period_key'
)
    ALTER TABLE fact.neet
    ADD time_period_key BIGINT NULL;


/* Participation */

IF NOT EXISTS (
    SELECT 1
    FROM sys.columns
    WHERE object_id = OBJECT_ID('fact.participation')
      AND name = 'borough_key'
)
    ALTER TABLE fact.participation
    ADD borough_key BIGINT NULL;

IF NOT EXISTS (
    SELECT 1
    FROM sys.columns
    WHERE object_id = OBJECT_ID('fact.participation')
      AND name = 'time_period_key'
)
    ALTER TABLE fact.participation
    ADD time_period_key BIGINT NULL;


/* Nomis APS */

IF NOT EXISTS (
    SELECT 1
    FROM sys.columns
    WHERE object_id = OBJECT_ID('fact.labour_market_aps')
      AND name = 'borough_key'
)
    ALTER TABLE fact.labour_market_aps
    ADD borough_key BIGINT NULL;

IF NOT EXISTS (
    SELECT 1
    FROM sys.columns
    WHERE object_id = OBJECT_ID('fact.labour_market_aps')
      AND name = 'labour_market_period_key'
)
    ALTER TABLE fact.labour_market_aps
    ADD labour_market_period_key BIGINT NULL;

IF NOT EXISTS (
    SELECT 1
    FROM sys.columns
    WHERE object_id = OBJECT_ID('fact.labour_market_aps')
      AND name = 'labour_market_variable_key'
)
    ALTER TABLE fact.labour_market_aps
    ADD labour_market_variable_key BIGINT NULL;

COMMIT TRANSACTION;
