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

import com.microsoft.spark.fabric
from pyspark.sql import functions as F


GOLD = "wh_gm_skills_gold"
MODEL_RUN_ID = str(uuid.uuid4())

print("Gold fact-model run:", MODEL_RUN_ID)


def read_gold(table):
    return spark.read.synapsesql(
        f"{GOLD}.{table}"
    )


def write_gold(df, table, expected):
    target = f"{GOLD}.{table}"

    # Materialise before overwriting any table that
    # participated in the source plan.
    df = df.cache()
    actual = df.count()

    if actual != expected:
        raise RuntimeError(
            f"{table}: expected {expected:,} rows, "
            f"got {actual:,}"
        )

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

    if written != expected:
        raise RuntimeError(
            f"{table}: write reconciliation failed. "
            f"expected={expected:,}, "
            f"written={written:,}"
        )

    print(
        f"PASS {table}: {written:,} rows"
    )

    df.unpersist()

    return written


def require_keys(df, table, keys):
    condition = None

    for key in keys:
        check = F.col(key).isNull()
        condition = (
            check
            if condition is None
            else condition | check
        )

    unresolved = (
        df.filter(condition).count()
    )

    if unresolved:
        raise RuntimeError(
            f"{table}: {unresolved:,} rows "
            "contain unresolved required keys."
        )

    print(
        f"PASS {table}: required keys resolved"
    )


# CELL ********************
# Governed existing Gold dimensions.

borough = (
    read_gold("dim.borough")
    .filter(F.col("is_current") == True)
    .select(
        "borough_code",
        "borough_key",
    )
)

time_period = (
    read_gold("dim.time_period")
    .select(
        "time_period",
        "time_identifier",
        "time_period_key",
    )
)

apps_level = (
    read_gold("dim.apprenticeship_level")
    .select(
        "apps_level",
        "apprenticeship_level_key",
    )
)

ssa = (
    read_gold("dim.ssa_subject")
    .filter(F.col("is_current") == True)
    .select(
        "ssa_tier_1",
        "ssa_subject_key",
        "gateway_code",
    )
)

gateway = (
    read_gold("dim.mbacc_gateway")
    .filter(F.col("is_current") == True)
    .select(
        "gateway_code",
        "gateway_key",
    )
)


# CELL ********************
# Build governed Nomis period dimension.

labour_source = read_gold(
    "fact.labour_market_aps"
)

dim_labour_period = (
    labour_source
    .select(
        "date",
        "date_name",
        "date_code",
        "date_type",
        "date_typecode",
        "date_sortorder",
    )
    .dropDuplicates()
    .withColumn(
        "labour_market_period_key",
        F.xxhash64(
            F.concat_ws(
                "|",
                F.col("date"),
                F.col("date_code"),
                F.col("date_type"),
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
        "labour_market_period_key",
        "date",
        "date_name",
        "date_code",
        "date_type",
        "date_typecode",
        "date_sortorder",
        "gold_model_run_id",
        "gold_modelled_at_utc",
    )
)


# CELL ********************
# Build governed Nomis variable dimension.

dim_labour_variable = (
    labour_source
    .select(
        "variable",
        "variable_name",
        "variable_code",
        "variable_type",
        "variable_typecode",
        "variable_sortorder",
    )
    .dropDuplicates()
    .withColumn(
        "labour_market_variable_key",
        F.xxhash64(
            F.concat_ws(
                "|",
                F.col("variable_code"),
                F.col("variable_typecode"),
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
        "labour_market_variable_key",
        "variable",
        "variable_name",
        "variable_code",
        "variable_type",
        "variable_typecode",
        "variable_sortorder",
        "gold_model_run_id",
        "gold_modelled_at_utc",
    )
)

if dim_labour_period.count() != 86:
    raise RuntimeError(
        "Expected 86 labour-market periods."
    )

if dim_labour_variable.count() != 5:
    raise RuntimeError(
        "Expected 5 labour-market variables."
    )

print(
    "PASS labour-market dimension profile: "
    "periods=86 variables=5"
)


# CELL ********************
# Create the two new Gold dimensions.

write_gold(
    dim_labour_period,
    "dim.labour_market_period",
    86,
)

write_gold(
    dim_labour_variable,
    "dim.labour_market_variable",
    5,
)


# CELL ********************
# Re-read persisted dimensions for the fact model.

labour_period = (
    read_gold("dim.labour_market_period")
    .select(
        "date",
        "date_code",
        "date_type",
        "labour_market_period_key",
    )
)

labour_variable = (
    read_gold("dim.labour_market_variable")
    .select(
        "variable_code",
        "variable_typecode",
        "labour_market_variable_key",
    )
)


# CELL ********************
# Apprenticeship LAD.

src = read_gold(
    "fact.apprenticeship_lad"
)

original = src.columns

fact_apprenticeship_lad = (
    src
    .drop(
        "borough_key",
        "time_period_key",
        "apprenticeship_level_key",
    )
    .join(
        F.broadcast(borough),
        "borough_code",
        "left",
    )
    .join(
        F.broadcast(time_period),
        [
            "time_period",
            "time_identifier",
        ],
        "left",
    )
    .join(
        F.broadcast(apps_level),
        "apps_level",
        "left",
    )
    .select(*original)
)

require_keys(
    fact_apprenticeship_lad,
    "fact.apprenticeship_lad",
    [
        "borough_key",
        "time_period_key",
        "apprenticeship_level_key",
    ],
)


# CELL ********************
# Apprenticeship detail.

src = read_gold(
    "fact.apprenticeship_detail"
)

original = src.columns

fact_apprenticeship_detail = (
    src
    .drop(
        "borough_key",
        "time_period_key",
        "apprenticeship_level_key",
        "ssa_subject_key",
        "gateway_key",
    )
    .join(
        F.broadcast(borough),
        "borough_code",
        "left",
    )
    .join(
        F.broadcast(time_period),
        [
            "time_period",
            "time_identifier",
        ],
        "left",
    )
    .join(
        F.broadcast(apps_level),
        "apps_level",
        "left",
    )
    .join(
        F.broadcast(ssa),
        "ssa_tier_1",
        "left",
    )
    .join(
        F.broadcast(gateway),
        "gateway_code",
        "left",
    )
    .select(*original)
)

require_keys(
    fact_apprenticeship_detail,
    "fact.apprenticeship_detail",
    [
        "borough_key",
        "time_period_key",
        "apprenticeship_level_key",
        "ssa_subject_key",
    ],
)

mapped_gateway_rows = (
    fact_apprenticeship_detail
    .filter(
        F.col("gateway_key").isNotNull()
    )
    .count()
)

unmapped_gateway_rows = (
    fact_apprenticeship_detail
    .filter(
        F.col("gateway_key").isNull()
    )
    .count()
)

if mapped_gateway_rows != 8400:
    raise RuntimeError(
        "Expected 8,400 MBacc-mapped rows, "
        f"got {mapped_gateway_rows:,}"
    )

if unmapped_gateway_rows != 3360:
    raise RuntimeError(
        "Expected 3,360 intentionally "
        "unmapped rows, "
        f"got {unmapped_gateway_rows:,}"
    )

print(
    "PASS MBacc mapping: "
    f"mapped={mapped_gateway_rows:,} "
    f"intentionally_unmapped="
    f"{unmapped_gateway_rows:,}"
)


# CELL ********************
# NEET.

src = read_gold("fact.neet")
original = src.columns

fact_neet = (
    src
    .drop(
        "borough_key",
        "time_period_key",
    )
    .join(
        F.broadcast(borough),
        "borough_code",
        "left",
    )
    .join(
        F.broadcast(time_period),
        [
            "time_period",
            "time_identifier",
        ],
        "left",
    )
    .select(*original)
)

require_keys(
    fact_neet,
    "fact.neet",
    [
        "borough_key",
        "time_period_key",
    ],
)


# CELL ********************
# Participation.

src = read_gold(
    "fact.participation"
)
original = src.columns

fact_participation = (
    src
    .drop(
        "borough_key",
        "time_period_key",
    )
    .join(
        F.broadcast(borough),
        "borough_code",
        "left",
    )
    .join(
        F.broadcast(time_period),
        [
            "time_period",
            "time_identifier",
        ],
        "left",
    )
    .select(*original)
)

require_keys(
    fact_participation,
    "fact.participation",
    [
        "borough_key",
        "time_period_key",
    ],
)


# CELL ********************
# Nomis APS.

src = read_gold(
    "fact.labour_market_aps"
)
original = src.columns

fact_labour_market = (
    src
    .drop(
        "borough_key",
        "labour_market_period_key",
        "labour_market_variable_key",
    )
    .join(
        F.broadcast(borough),
        "borough_code",
        "left",
    )
    .join(
        F.broadcast(labour_period),
        [
            "date",
            "date_code",
            "date_type",
        ],
        "left",
    )
    .join(
        F.broadcast(labour_variable),
        [
            "variable_code",
            "variable_typecode",
        ],
        "left",
    )
    .select(*original)
)

require_keys(
    fact_labour_market,
    "fact.labour_market_aps",
    [
        "borough_key",
        "labour_market_period_key",
        "labour_market_variable_key",
    ],
)


# CELL ********************
# Persist dimensionalised facts.

counts = {}

counts[
    "fact.apprenticeship_lad"
] = write_gold(
    fact_apprenticeship_lad,
    "fact.apprenticeship_lad",
    2880,
)

counts[
    "fact.apprenticeship_detail"
] = write_gold(
    fact_apprenticeship_detail,
    "fact.apprenticeship_detail",
    11760,
)

counts["fact.neet"] = write_gold(
    fact_neet,
    "fact.neet",
    1754,
)

counts[
    "fact.participation"
] = write_gold(
    fact_participation,
    "fact.participation",
    1755,
)

counts[
    "fact.labour_market_aps"
] = write_gold(
    fact_labour_market,
    "fact.labour_market_aps",
    4300,
)


# CELL ********************

result = {
    "status": "success",
    "model_run_id": MODEL_RUN_ID,
    "dimensions": {
        "labour_market_period": 86,
        "labour_market_variable": 5,
    },
    "facts": counts,
    "mbacc": {
        "mapped_rows": mapped_gateway_rows,
        "intentionally_unmapped_rows":
            unmapped_gateway_rows,
    },
}

print()
print("=" * 80)
print("GOLD FACT MODEL COMPLETE")
print("=" * 80)
print(
    json.dumps(
        result,
        indent=2,
    )
)

notebookutils.notebook.exit(
    json.dumps(result)
)
