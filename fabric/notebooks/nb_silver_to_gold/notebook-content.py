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
import time
import uuid

import com.microsoft.spark.fabric  # noqa: F401
from pyspark.sql import functions as F

WORKSPACE_ID = "81e75ca0-f556-48c0-9dea-4851ce7bf916"
GOLD_ID = "ce6454df-212a-438a-809d-7f77075fb5c9"
GOLD_NAME = "wh_gm_skills_gold"

GOLD_LOAD_RUN_ID = str(uuid.uuid4())


# CELL ********************

TABLE_MAP = [
    (
        "borough_reference",
        f"{GOLD_NAME}.dim.borough",
    ),
    (
        "mbacc_gateway",
        f"{GOLD_NAME}.dim.mbacc_gateway",
    ),
    (
        "mbacc_ssa_crosswalk",
        f"{GOLD_NAME}.dim.ssa_subject",
    ),
    (
        "apprenticeship_lad",
        f"{GOLD_NAME}.fact.apprenticeship_lad",
    ),
    (
        "apprenticeship_detail",
        f"{GOLD_NAME}.fact.apprenticeship_detail",
    ),
    (
        "neet",
        f"{GOLD_NAME}.fact.neet",
    ),
    (
        "participation",
        f"{GOLD_NAME}.fact.participation",
    ),
    (
        "nomis_aps",
        f"{GOLD_NAME}.fact.labour_market_aps",
    ),
    (
        "data_quality_result",
        f"{GOLD_NAME}.audit.silver_data_quality_snapshot",
    ),
]

print("Gold load run:", GOLD_LOAD_RUN_ID)
print("Tables to load:", len(TABLE_MAP))


# CELL ********************

source_counts = {}
target_counts = {}


def prepare_gold_snapshot(df):
    return (
        df
        .withColumn(
            "gold_load_run_id",
            F.lit(GOLD_LOAD_RUN_ID),
        )
        .withColumn(
            "gold_loaded_at_utc",
            F.current_timestamp(),
        )
    )


def read_warehouse_count(table_name):
    last_error = None

    for attempt in range(1, 6):
        try:
            return (
                spark.read
                .synapsesql(table_name)
                .count()
            )
        except Exception as exc:
            last_error = exc
            print(
                f"Readback retry {attempt}/5 "
                f"for {table_name}"
            )
            time.sleep(5)

    raise RuntimeError(
        f"Unable to read back {table_name}"
    ) from last_error


# CELL ********************

for source_table, target_table in TABLE_MAP:

    print()
    print("=" * 80)
    print(f"{source_table} -> {target_table}")
    print("=" * 80)

    source_df = spark.table(source_table)

    source_count = source_df.count()
    source_counts[source_table] = source_count

    print("Silver rows:", source_count)

    gold_df = prepare_gold_snapshot(source_df)

    (
        gold_df.write
        .mode("overwrite")
        .synapsesql(target_table)
    )

    print("Warehouse write completed.")

    target_count = read_warehouse_count(
        target_table
    )

    target_counts[target_table] = target_count

    print("Gold rows:", target_count)

    if source_count != target_count:
        raise RuntimeError(
            f"Row-count mismatch for {source_table}: "
            f"Silver={source_count}, "
            f"Gold={target_count}"
        )

    print("PASS: row-count reconciliation")


# CELL ********************

expected_core_counts = {
    "borough_reference": 10,
    "mbacc_gateway": 7,
    "mbacc_ssa_crosswalk": 14,
    "apprenticeship_lad": 2880,
    "apprenticeship_detail": 11760,
    "neet": 1754,
    "participation": 1755,
    "nomis_aps": 4300,
}

for table, expected in expected_core_counts.items():

    actual = source_counts.get(table)

    if actual != expected:
        raise RuntimeError(
            f"Unexpected Silver row count for {table}: "
            f"expected={expected}, actual={actual}"
        )

print()
print("PASS: core Silver source counts verified.")


# CELL ********************

RESULT = {
    "status": "success",
    "gold_load_run_id": GOLD_LOAD_RUN_ID,
    "warehouse": GOLD_NAME,
    "tables_loaded": len(TABLE_MAP),
    "source_counts": source_counts,
    "target_counts": target_counts,
}

print()
print("=" * 80)
print("GOLD LOAD COMPLETE")
print("=" * 80)
print(json.dumps(RESULT, indent=2))

notebookutils.notebook.exit(
    json.dumps(RESULT)
)
