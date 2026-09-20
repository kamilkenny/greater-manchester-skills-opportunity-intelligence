# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "d4a65e02-93bd-4109-9acc-80c8c57e6b4d",
# META       "default_lakehouse_name": "lh_gm_skills_silver",
# META       "default_lakehouse_workspace_id": "81e75ca0-f556-48c0-9dea-4851ce7bf916"
# META     }
# META   }
# META }

# CELL ********************

import json
import uuid

import com.microsoft.spark.fabric  # noqa: F401
from pyspark.sql import functions as F

GOLD_NAME = "wh_gm_skills_gold"
MODEL_RUN_ID = str(uuid.uuid4())

OPEN_END_DATE = F.to_date(
    F.lit("9999-12-31")
)

print("Gold dimensional model run:", MODEL_RUN_ID)


# CELL ********************

def row_hash(*columns):
    return F.sha2(
        F.concat_ws(
            "||",
            *[
                F.coalesce(
                    F.col(c).cast("string"),
                    F.lit(""),
                )
                for c in columns
            ],
        ),
        256,
    )


def warehouse_write(df, target):
    (
        df.write
        .mode("overwrite")
        .synapsesql(target)
    )

    written = (
        spark.read
        .synapsesql(target)
        .count()
    )

    expected = df.count()

    if written != expected:
        raise RuntimeError(
            f"Reconciliation failed for {target}: "
            f"expected={expected}, actual={written}"
        )

    print(
        f"PASS {target}: {written:,} rows"
    )

    return written


# CELL ********************
# dim.borough
# SCD2-ready dimension

borough_source = spark.table(
    "borough_reference"
)

dim_borough = (
    borough_source
    .select(
        "borough_code",
        "borough_name",
        "source_authority",
        "source_checked_date",
        "is_current",
    )
    .dropDuplicates(["borough_code"])
    .withColumn(
        "borough_key",
        F.xxhash64("borough_code"),
    )
    .withColumn(
        "effective_from",
        F.to_date("source_checked_date"),
    )
    .withColumn(
        "effective_to",
        OPEN_END_DATE,
    )
    .withColumn(
        "scd_version",
        F.lit(1),
    )
    .withColumn(
        "row_hash",
        row_hash(
            "borough_code",
            "borough_name",
            "source_authority",
        ),
    )
    .withColumn(
        "gold_model_run_id",
        F.lit(MODEL_RUN_ID),
    )
    .withColumn(
        "gold_modelled_at_utc",
        F.current_timestamp(),
    )
    .select(
        "borough_key",
        "borough_code",
        "borough_name",
        "source_authority",
        "effective_from",
        "effective_to",
        "is_current",
        "scd_version",
        "row_hash",
        "gold_model_run_id",
        "gold_modelled_at_utc",
    )
)

if dim_borough.count() != 10:
    raise RuntimeError(
        "Expected 10 borough dimension rows."
    )


# CELL ********************
# dim.mbacc_gateway
# SCD2-ready dimension

gateway_source = spark.table(
    "mbacc_gateway"
)

dim_gateway = (
    gateway_source
    .select(
        "gateway_code",
        "gateway_name",
        "alternate_name",
        "source_authority",
        "source_checked_date",
        "is_current",
    )
    .dropDuplicates(["gateway_code"])
    .withColumn(
        "gateway_key",
        F.xxhash64("gateway_code"),
    )
    .withColumn(
        "effective_from",
        F.to_date("source_checked_date"),
    )
    .withColumn(
        "effective_to",
        OPEN_END_DATE,
    )
    .withColumn(
        "scd_version",
        F.lit(1),
    )
    .withColumn(
        "row_hash",
        row_hash(
            "gateway_code",
            "gateway_name",
            "alternate_name",
            "source_authority",
        ),
    )
    .withColumn(
        "gold_model_run_id",
        F.lit(MODEL_RUN_ID),
    )
    .withColumn(
        "gold_modelled_at_utc",
        F.current_timestamp(),
    )
    .select(
        "gateway_key",
        "gateway_code",
        "gateway_name",
        "alternate_name",
        "source_authority",
        "effective_from",
        "effective_to",
        "is_current",
        "scd_version",
        "row_hash",
        "gold_model_run_id",
        "gold_modelled_at_utc",
    )
)

if dim_gateway.count() != 7:
    raise RuntimeError(
        "Expected 7 MBacc gateway dimension rows."
    )


# CELL ********************
# dim.ssa_subject
# Version-aware SCD2 structure

ssa_source = spark.table(
    "mbacc_ssa_crosswalk"
)

dim_ssa = (
    ssa_source
    .withColumn(
        "ssa_subject_key",
        F.xxhash64(
            F.concat_ws(
                "|",
                F.col("ssa_tier_1"),
                F.col("mapping_version"),
                F.col("effective_from").cast(
                    "string"
                ),
            )
        ),
    )
    .withColumn(
        "effective_from",
        F.to_date("effective_from"),
    )
    .withColumn(
        "effective_to",
        F.coalesce(
            F.to_date("effective_to"),
            OPEN_END_DATE,
        ),
    )
    .withColumn(
        "scd_version",
        F.lit(1),
    )
    .withColumn(
        "row_hash",
        row_hash(
            "ssa_tier_1",
            "gateway_code",
            "mapping_status",
            "mapping_basis",
            "mapping_version",
        ),
    )
    .withColumn(
        "gold_model_run_id",
        F.lit(MODEL_RUN_ID),
    )
    .withColumn(
        "gold_modelled_at_utc",
        F.current_timestamp(),
    )
    .select(
        "ssa_subject_key",
        "ssa_tier_1",
        "gateway_code",
        "mapping_status",
        "mapping_basis",
        "mapping_version",
        "effective_from",
        "effective_to",
        "is_current",
        "scd_version",
        "row_hash",
        "gold_model_run_id",
        "gold_modelled_at_utc",
    )
)

if dim_ssa.count() != 14:
    raise RuntimeError(
        "Expected 14 SSA subject rows."
    )


# CELL ********************
# dim.time_period
# DfE analytical period dimension

time_sources = [
    "apprenticeship_lad",
    "apprenticeship_detail",
    "neet",
    "participation",
]

time_df = None

for table in time_sources:

    part = (
        spark.table(table)
        .select(
            F.trim("time_period").alias(
                "time_period"
            ),
            F.trim("time_identifier").alias(
                "time_identifier"
            ),
        )
    )

    time_df = (
        part
        if time_df is None
        else time_df.unionByName(part)
    )

dim_time = (
    time_df
    .filter(
        F.col("time_period").isNotNull()
    )
    .dropDuplicates(
        [
            "time_period",
            "time_identifier",
        ]
    )
    .withColumn(
        "time_period_key",
        F.xxhash64(
            F.concat_ws(
                "|",
                "time_period",
                "time_identifier",
            )
        ),
    )
    .withColumn(
        "gold_model_run_id",
        F.lit(MODEL_RUN_ID),
    )
    .withColumn(
        "gold_modelled_at_utc",
        F.current_timestamp(),
    )
    .select(
        "time_period_key",
        "time_period",
        "time_identifier",
        "gold_model_run_id",
        "gold_modelled_at_utc",
    )
)

if dim_time.count() == 0:
    raise RuntimeError(
        "Time period dimension is empty."
    )


# CELL ********************
# dim.apprenticeship_level

level_df = (
    spark.table("apprenticeship_lad")
    .select("apps_level")
    .unionByName(
        spark.table(
            "apprenticeship_detail"
        ).select("apps_level")
    )
)

dim_level = (
    level_df
    .filter(
        F.col("apps_level").isNotNull()
    )
    .withColumn(
        "apps_level",
        F.trim("apps_level"),
    )
    .filter(
        F.col("apps_level") != ""
    )
    .dropDuplicates(["apps_level"])
    .withColumn(
        "apprenticeship_level_key",
        F.xxhash64("apps_level"),
    )
    .withColumn(
        "gold_model_run_id",
        F.lit(MODEL_RUN_ID),
    )
    .withColumn(
        "gold_modelled_at_utc",
        F.current_timestamp(),
    )
    .select(
        "apprenticeship_level_key",
        "apps_level",
        "gold_model_run_id",
        "gold_modelled_at_utc",
    )
)

if dim_level.count() == 0:
    raise RuntimeError(
        "Apprenticeship level dimension is empty."
    )


# CELL ********************
# Referential-integrity validation before Gold write

valid_gateway_codes = (
    dim_gateway
    .select("gateway_code")
    .distinct()
)

invalid_ssa_gateway = (
    dim_ssa
    .filter(
        F.col("gateway_code").isNotNull()
    )
    .select("gateway_code")
    .distinct()
    .join(
        valid_gateway_codes,
        on="gateway_code",
        how="left_anti",
    )
)

if invalid_ssa_gateway.count():
    invalid_ssa_gateway.show(
        truncate=False
    )
    raise RuntimeError(
        "SSA to MBacc referential integrity failed."
    )

print(
    "PASS: dimensional referential integrity"
)


# CELL ********************
# Write governed Gold dimensions

counts = {}

counts["dim.borough"] = warehouse_write(
    dim_borough,
    f"{GOLD_NAME}.dim.borough",
)

counts["dim.mbacc_gateway"] = warehouse_write(
    dim_gateway,
    f"{GOLD_NAME}.dim.mbacc_gateway",
)

counts["dim.ssa_subject"] = warehouse_write(
    dim_ssa,
    f"{GOLD_NAME}.dim.ssa_subject",
)

counts["dim.time_period"] = warehouse_write(
    dim_time,
    f"{GOLD_NAME}.dim.time_period",
)

counts[
    "dim.apprenticeship_level"
] = warehouse_write(
    dim_level,
    f"{GOLD_NAME}.dim.apprenticeship_level",
)


# CELL ********************

RESULT = {
    "status": "success",
    "model_run_id": MODEL_RUN_ID,
    "warehouse": GOLD_NAME,
    "dimensions": counts,
    "scd2_ready": [
        "dim.borough",
        "dim.mbacc_gateway",
        "dim.ssa_subject",
    ],
}

print()
print("=" * 80)
print("GOLD DIMENSIONAL CORE COMPLETE")
print("=" * 80)
print(
    json.dumps(
        RESULT,
        indent=2,
    )
)

notebookutils.notebook.exit(
    json.dumps(RESULT)
)
