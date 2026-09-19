/*
GM SkillsFlow
Control, audit and SCD Type 4 foundation
*/


IF OBJECT_ID('ctl.source_config', 'U') IS NULL
BEGIN
    CREATE TABLE ctl.source_config
    (
        source_id             VARCHAR(20)   NOT NULL,
        source_name           VARCHAR(200)  NOT NULL,
        source_type           VARCHAR(50)   NOT NULL,
        endpoint              VARCHAR(1000) NULL,
        target_path           VARCHAR(500)  NOT NULL,
        file_format           VARCHAR(30)   NOT NULL,
        refresh_frequency     VARCHAR(50)   NOT NULL,
        enabled               BIT           NOT NULL,
        last_watermark        VARCHAR(100)  NULL,
        config_hash           VARCHAR(64)   NULL,
        updated_at_utc        DATETIME2(3)  NOT NULL,
        source_run_id         VARCHAR(100)  NULL
    );
END;


IF OBJECT_ID('hist.source_config', 'U') IS NULL
BEGIN
    CREATE TABLE hist.source_config
    (
        source_id             VARCHAR(20)   NOT NULL,
        source_name           VARCHAR(200)  NOT NULL,
        source_type           VARCHAR(50)   NOT NULL,
        endpoint              VARCHAR(1000) NULL,
        target_path           VARCHAR(500)  NOT NULL,
        file_format           VARCHAR(30)   NOT NULL,
        refresh_frequency     VARCHAR(50)   NOT NULL,
        enabled               BIT           NOT NULL,
        last_watermark        VARCHAR(100)  NULL,
        config_hash           VARCHAR(64)   NULL,
        valid_from_utc        DATETIME2(3)  NOT NULL,
        valid_to_utc          DATETIME2(3)  NOT NULL,
        archived_at_utc       DATETIME2(3)  NOT NULL,
        source_run_id         VARCHAR(100)  NULL
    );
END;


IF OBJECT_ID('audit.pipeline_run', 'U') IS NULL
BEGIN
    CREATE TABLE audit.pipeline_run
    (
        run_id                VARCHAR(100)  NOT NULL,
        pipeline_name         VARCHAR(200)  NOT NULL,
        environment_code      VARCHAR(20)   NOT NULL,
        status                VARCHAR(30)   NOT NULL,
        started_at_utc        DATETIME2(3)  NOT NULL,
        completed_at_utc      DATETIME2(3)  NULL,
        rows_read             BIGINT        NULL,
        rows_written          BIGINT        NULL,
        error_message         VARCHAR(4000) NULL
    );
END;


IF OBJECT_ID('audit.data_quality_result', 'U') IS NULL
BEGIN
    CREATE TABLE audit.data_quality_result
    (
        run_id                VARCHAR(100)  NOT NULL,
        source_id             VARCHAR(20)   NOT NULL,
        check_name            VARCHAR(200)  NOT NULL,
        check_status          VARCHAR(20)   NOT NULL,
        observed_value        VARCHAR(2000) NULL,
        expected_value        VARCHAR(2000) NULL,
        check_message         VARCHAR(4000) NULL,
        checked_at_utc        DATETIME2(3)  NOT NULL
    );
END;
