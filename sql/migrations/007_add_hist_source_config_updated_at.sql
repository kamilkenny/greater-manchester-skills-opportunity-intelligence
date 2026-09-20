-- GM SkillsFlow
-- SCD Type 4 schema alignment
-- Adds the source configuration update timestamp to the
-- separate history table.

IF NOT EXISTS (
    SELECT 1
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = 'hist'
      AND TABLE_NAME = 'source_config'
      AND COLUMN_NAME = 'updated_at_utc'
)
BEGIN
    ALTER TABLE hist.source_config
    ADD updated_at_utc DATETIME2(3) NULL;
END;
