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

from pyspark.sql import functions as F

WORKSPACE_ID = "81e75ca0-f556-48c0-9dea-4851ce7bf916"
SILVER_ID = "d4a65e02-93bd-4109-9acc-80c8c57e6b4d"

SILVER_ROOT = (
    f"abfss://{WORKSPACE_ID}"
    "@onelake.dfs.fabric.microsoft.com/"
    f"{SILVER_ID}"
)

BOROUGH_PATH = (
    f"{SILVER_ROOT}/Files/reference/"
    "gm_boroughs/version=v1/"
    "gm_boroughs_reference.csv"
)

CROSSWALK_PATH = (
    f"{SILVER_ROOT}/Files/reference/"
    "mbacc_ssa_crosswalk/version=v1/"
    "mbacc_ssa_crosswalk.csv"
)

EXPECTED_GSS = {
    f"E080000{x:02d}"
    for x in range(1, 11)
}

EXPECTED_GATEWAYS = {
    f"MBACC{x:02d}"
    for x in range(1, 8)
}

ALLOWED_MAPPING_STATUS = {
    "direct_theme_alignment",
    "analytical_proxy",
    "cross_cutting",
    "no_direct_mapping",
    "aggregate_excluded",
}


# CELL ********************

borough = (
    spark.read
    .option("header", True)
    .option("inferSchema", False)
    .csv(BOROUGH_PATH)
)

crosswalk = (
    spark.read
    .option("header", True)
    .option("inferSchema", False)
    .csv(CROSSWALK_PATH)
)

print("Raw borough rows:", borough.count())
print("Raw crosswalk rows:", crosswalk.count())


# CELL ********************

borough = (
    borough
    .withColumn(
        "is_current",
        F.lower(F.trim("is_current")) == F.lit("true"),
    )
    .withColumn(
        "source_checked_date",
        F.to_date("source_checked_date"),
    )
    .withColumn(
        "reference_version",
        F.lit("v1"),
    )
    .withColumn(
        "loaded_at_utc",
        F.current_timestamp(),
    )
)

crosswalk = (
    crosswalk
    .withColumn(
        "gateway_code",
        F.when(
            F.trim("gateway_code") == "",
            F.lit(None),
        ).otherwise(F.trim("gateway_code")),
    )
    .withColumn(
        "effective_from",
        F.to_date("effective_from"),
    )
    .withColumn(
        "effective_to",
        F.to_date("effective_to"),
    )
    .withColumn(
        "is_current",
        F.lower(F.trim("is_current")) == F.lit("true"),
    )
    .withColumn(
        "reference_version",
        F.lit("v1"),
    )
    .withColumn(
        "loaded_at_utc",
        F.current_timestamp(),
    )
)


# CELL ********************

# Borough DQ

borough_count = borough.count()

if borough_count != 10:
    raise RuntimeError(
        f"Expected 10 GM boroughs, found {borough_count}"
    )

borough_distinct = (
    borough
    .select("borough_code")
    .distinct()
    .count()
)

if borough_distinct != 10:
    raise RuntimeError(
        "Borough code uniqueness check failed."
    )

actual_gss = {
    row["borough_code"]
    for row in (
        borough
        .select("borough_code")
        .distinct()
        .collect()
    )
}

if actual_gss != EXPECTED_GSS:
    raise RuntimeError(
        "Greater Manchester GSS coverage check failed. "
        f"Found: {sorted(actual_gss)}"
    )

if borough.filter(~F.col("is_current")).count() != 0:
    raise RuntimeError(
        "Unexpected non-current borough reference row."
    )

print("PASS: borough reference DQ")


# CELL ********************

# Crosswalk DQ

crosswalk_count = crosswalk.count()

if crosswalk_count != 14:
    raise RuntimeError(
        f"Expected 14 SSA mappings, found {crosswalk_count}"
    )

crosswalk_distinct = (
    crosswalk
    .select("ssa_tier_1")
    .distinct()
    .count()
)

if crosswalk_distinct != 14:
    raise RuntimeError(
        "SSA Tier 1 crosswalk uniqueness check failed."
    )

bad_status = (
    crosswalk
    .filter(
        ~F.col("mapping_status").isin(
            sorted(ALLOWED_MAPPING_STATUS)
        )
    )
    .count()
)

if bad_status:
    raise RuntimeError(
        f"Invalid mapping statuses found: {bad_status}"
    )

total_rows = (
    crosswalk
    .filter(F.col("ssa_tier_1") == "Total")
    .collect()
)

if len(total_rows) != 1:
    raise RuntimeError(
        "Expected exactly one Total mapping row."
    )

if (
    total_rows[0]["mapping_status"]
    != "aggregate_excluded"
    or total_rows[0]["gateway_code"] is not None
):
    raise RuntimeError(
        "Total must be excluded from gateway attribution."
    )

print("PASS: crosswalk structural DQ")


# CELL ********************

# Validate against the governed MBacc gateway table.

gateway = (
    spark.table("mbacc_gateway")
    .select("gateway_code")
    .distinct()
)

actual_gateway_codes = {
    row["gateway_code"]
    for row in gateway.collect()
}

if actual_gateway_codes != EXPECTED_GATEWAYS:
    raise RuntimeError(
        "Existing mbacc_gateway table does not contain "
        "the expected seven governed gateway codes."
    )

invalid_fk = (
    crosswalk
    .filter(F.col("gateway_code").isNotNull())
    .select("gateway_code")
    .distinct()
    .join(
        gateway,
        on="gateway_code",
        how="left_anti",
    )
)

invalid_fk_count = invalid_fk.count()

if invalid_fk_count:
    invalid_fk.show(truncate=False)
    raise RuntimeError(
        f"MBacc referential-integrity failures: "
        f"{invalid_fk_count}"
    )

print("PASS: MBacc gateway referential integrity")


# CELL ********************

# Validate the crosswalk against actual apprenticeship_detail SSA values.

actual_ssa = (
    spark.table("apprenticeship_detail")
    .select("ssa_tier_1")
    .distinct()
)

unmapped_source_values = (
    actual_ssa
    .join(
        crosswalk.select("ssa_tier_1"),
        on="ssa_tier_1",
        how="left_anti",
    )
)

missing_crosswalk_count = unmapped_source_values.count()

if missing_crosswalk_count:
    unmapped_source_values.show(truncate=False)
    raise RuntimeError(
        "Apprenticeship SSA values exist without "
        "crosswalk coverage."
    )

orphan_crosswalk = (
    crosswalk
    .select("ssa_tier_1")
    .join(
        actual_ssa,
        on="ssa_tier_1",
        how="left_anti",
    )
)

orphan_count = orphan_crosswalk.count()

if orphan_count:
    orphan_crosswalk.show(truncate=False)
    raise RuntimeError(
        "Crosswalk contains SSA values not present "
        "in apprenticeship_detail."
    )

print("PASS: complete SSA source coverage")


# CELL ********************

borough.write \
    .format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .saveAsTable("borough_reference")

crosswalk.write \
    .format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .saveAsTable("mbacc_ssa_crosswalk")

print("PASS: Silver reference Delta tables written.")


# CELL ********************

RESULT = {
    "status": "success",
    "tables": {
        "borough_reference": borough_count,
        "mbacc_ssa_crosswalk": crosswalk_count,
    },
    "checks": {
        "gm_borough_count": 10,
        "ssa_category_count": 14,
        "mbacc_gateway_count": 7,
        "invalid_gateway_fk": 0,
        "unmapped_source_ssa": 0,
        "orphan_crosswalk_ssa": 0,
    },
}

print(json.dumps(RESULT, indent=2))

notebookutils.notebook.exit(
    json.dumps(RESULT)
)
