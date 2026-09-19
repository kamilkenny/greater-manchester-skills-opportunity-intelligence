/*
GM SkillsFlow
Gold Warehouse schemas
*/

IF NOT EXISTS (
    SELECT 1
    FROM sys.schemas
    WHERE name = 'ctl'
)
    EXEC('CREATE SCHEMA ctl');

IF NOT EXISTS (
    SELECT 1
    FROM sys.schemas
    WHERE name = 'audit'
)
    EXEC('CREATE SCHEMA audit');

IF NOT EXISTS (
    SELECT 1
    FROM sys.schemas
    WHERE name = 'hist'
)
    EXEC('CREATE SCHEMA hist');

IF NOT EXISTS (
    SELECT 1
    FROM sys.schemas
    WHERE name = 'dim'
)
    EXEC('CREATE SCHEMA dim');

IF NOT EXISTS (
    SELECT 1
    FROM sys.schemas
    WHERE name = 'fact'
)
    EXEC('CREATE SCHEMA fact');

IF NOT EXISTS (
    SELECT 1
    FROM sys.schemas
    WHERE name = 'mart'
)
    EXEC('CREATE SCHEMA mart');
