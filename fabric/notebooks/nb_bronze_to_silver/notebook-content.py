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
# META       "default_lakehouse_workspace_id": "81e75ca0-f556-48c0-9dea-4851ce7bf916",
# META       "known_lakehouses": [
# META         {
# META           "id": "d4a65e02-93bd-4109-9acc-80c8c57e6b4d"
# META         }
# META       ]
# META     }
# META   }
# META }

# CELL ********************

import json
import re
import uuid
from functools import reduce

from pyspark.sql import functions as F

WORKSPACE_ID = "81e75ca0-f556-48c0-9dea-4851ce7bf916"
BRONZE_ID = "b9a4e5f8-5c7f-41b5-bd54-7241fed3dc12"
SILVER_ID = "d4a65e02-93bd-4109-9acc-80c8c57e6b4d"

ONELAKE = "onelake.dfs.fabric.microsoft.com"

BRONZE_FILES = (
    f"abfss://{WORKSPACE_ID}@{ONELAKE}/{BRONZE_ID}/Files"
)

SILVER_FILES = (
    f"abfss://{WORKSPACE_ID}@{ONELAKE}/{SILVER_ID}/Files"
)

GM_BOROUGHS = {
    "E08000001": "Bolton",
    "E08000002": "Bury",
    "E08000003": "Manchester",
    "E08000004": "Oldham",
    "E08000005": "Rochdale",
    "E08000006": "Salford",
    "E08000007": "Stockport",
    "E08000008": "Tameside",
    "E08000009": "Trafford",
    "E08000010": "Wigan",
}

GM_CODES = list(GM_BOROUGHS)

PROCESSING_RUN_ID = str(uuid.uuid4())

dq_results = []
critical_failures = []
table_counts = {}


def record_dq(
    source_id,
    check_name,
    passed,
    observed,
    expected,
    message="",
):
    dq_results.append(
        {
            "processing_run_id": PROCESSING_RUN_ID,
            "source_id": source_id,
            "check_name": check_name,
            "check_status": "PASS" if passed else "FAIL",
            "observed_value": str(observed),
            "expected_value": str(expected),
            "message": message,
        }
    )

    if not passed:
        critical_failures.append(
            f"{source_id}:{check_name}"
        )


def modification_time(item):
    for attribute in (
        "modifyTime",
        "modificationTime",
    ):
        value = getattr(item, attribute, None)

        if value is not None:
            try:
                return int(value)
            except Exception:
                return 0

    return 0


def latest_snapshot(relative_root):
    root = f"{BRONZE_FILES}/{relative_root}"

    stack = [root]
    candidates = []

    while stack:
        current = stack.pop()

        for item in notebookutils.fs.ls(current):
            if item.isDir:
                stack.append(item.path)

            elif (
                item.isFile
                and item.name == "source.csv"
                and "/run_id=" in item.path
            ):
                candidates.append(item)

    if not candidates:
        raise RuntimeError(
            f"No immutable source.csv found under "
            f"{relative_root}"
        )

    def sort_key(item):
        match = re.search(
            r"/year=(\d{4})/"
            r"month=(\d{2})/"
            r"day=(\d{2})/"
            r"run_id=([^/]+)/source\.csv$",
            item.path,
        )

        if match:
            year, month, day, _ = match.groups()

            date_key = (
                int(year),
                int(month),
                int(day),
            )
        else:
            date_key = (0, 0, 0)

        return (
            *date_key,
            modification_time(item),
            item.path,
        )

    selected = max(
        candidates,
        key=sort_key,
    )

    print(
        f"SELECTED {relative_root}: "
        f"{selected.path}"
    )

    return selected.path


def read_csv(path):
    return (
        spark.read
        .option("header", "true")
        .option("inferSchema", "false")
        .option("mode", "FAILFAST")
        .csv(path)
    )


def get_source_run_id(path):
    match = re.search(
        r"/run_id=([^/]+)/",
        path,
    )

    return match.group(1) if match else None


def get_snapshot_date(path):
    match = re.search(
        r"/year=(\d{4})/"
        r"month=(\d{2})/"
        r"day=(\d{2})/",
        path,
    )

    if not match:
        return None

    return "-".join(match.groups())


def add_lineage(
    dataframe,
    source_id,
    source_path,
):
    return (
        dataframe
        .withColumn(
            "source_id",
            F.lit(source_id),
        )
        .withColumn(
            "source_run_id",
            F.lit(
                get_source_run_id(
                    source_path
                )
            ),
        )
        .withColumn(
            "source_snapshot_date",
            F.to_date(
                F.lit(
                    get_snapshot_date(
                        source_path
                    )
                )
            ),
        )
        .withColumn(
            "source_file_path",
            F.lit(source_path),
        )
        .withColumn(
            "processed_at_utc",
            F.current_timestamp(),
        )
        .withColumn(
            "processing_run_id",
            F.lit(PROCESSING_RUN_ID),
        )
    )


NUMERIC_PATTERN = (
    r"^[+-]?("
    r"[0-9]+([.][0-9]*)?"
    r"|[.][0-9]+"
    r")"
    r"([eE][+-]?[0-9]+)?$"
)


def add_disclosure_triplet(
    dataframe,
    column_name,
):
    raw_value = F.trim(
        F.col(column_name).cast("string")
    )

    token = F.lower(raw_value)

    status = (
        F.when(
            F.col(column_name).isNull()
            | (raw_value == ""),
            F.lit("missing"),
        )
        .when(
            token == "c",
            F.lit("suppressed"),
        )
        .when(
            token == "z",
            F.lit("not_applicable"),
        )
        .when(
            token == "x",
            F.lit("unavailable"),
        )
        .when(
            token == "low",
            F.lit("low_non_zero"),
        )
        .when(
            raw_value.rlike(
                NUMERIC_PATTERN
            ),
            F.lit("reported"),
        )
        .otherwise(
            F.lit("invalid_token")
        )
    )

    return (
        dataframe
        .withColumn(
            f"{column_name}_raw_value",
            F.col(column_name)
            .cast("string"),
        )
        .withColumn(
            f"{column_name}_numeric_value",
            F.when(
                raw_value.rlike(
                    NUMERIC_PATTERN
                ),
                raw_value.cast("double"),
            ).otherwise(
                F.lit(None)
                .cast("double")
            ),
        )
        .withColumn(
            f"{column_name}_value_status",
            status,
        )
        .drop(column_name)
    )


def quarantine(
    dataframe,
    source_id,
    source_run_id,
):
    if dataframe.limit(1).count() == 0:
        return

    target = (
        f"{SILVER_FILES}/quarantine/"
        f"{source_id}/"
        f"source_run_id={source_run_id}"
    )

    (
        dataframe.write
        .mode("overwrite")
        .format("parquet")
        .save(target)
    )

    print(
        f"QUARANTINE {source_id}: "
        f"{target}"
    )


def validate_borough_coverage(
    dataframe,
    source_id,
):
    codes = {
        row["borough_code"]
        for row in (
            dataframe
            .select("borough_code")
            .distinct()
            .collect()
        )
        if row["borough_code"] is not None
    }

    record_dq(
        source_id,
        "gm_borough_coverage",
        codes == set(GM_CODES),
        sorted(codes),
        sorted(GM_CODES),
        (
            "All ten Greater Manchester "
            "borough GSS codes must be present."
        ),
    )


def write_table(
    dataframe,
    table_name,
):
    (
        dataframe.write
        .format("delta")
        .mode("overwrite")
        .option(
            "overwriteSchema",
            "true",
        )
        .saveAsTable(table_name)
    )

    count = dataframe.count()

    table_counts[
        table_name
    ] = count

    print(
        f"WROTE {table_name}: "
        f"{count:,} rows"
    )


DFE_CONFIG = {
    "SRC01": {
        "root": "raw/dfe/SRC01",
        "table": "apprenticeship_lad",
        "geo_code": "lad_code",
        "geo_name": "lad_name",
        "metrics": [
            "starts",
            "achievements",
            "participation",
        ],
    },
    "SRC02": {
        "root": "raw/dfe/SRC02",
        "table": "apprenticeship_detail",
        "geo_code": "lad_code",
        "geo_name": "lad_name",
        "metrics": [
            "starts",
            "achievements",
        ],
    },
    "SRC03": {
        "root": "raw/dfe/SRC03",
        "table": "neet",
        "geo_code": "new_la_code",
        "geo_name": "la_name",
        "metrics": [
            "avg_cohort_count",
            "avg_neet_nk_count",
            "avg_neet_count",
            "avg_nk_count",
            "neet_nk_percent",
            "neet_percent",
            "nk_percent",
            "annual_change_neet_nk_percent",
        ],
    },
    "SRC04": {
        "root": "raw/dfe/SRC04",
        "table": "participation",
        "geo_code": "new_la_code",
        "geo_name": "la_name",
        "metrics": [
            "cohort_count",
            "total_in_education_and_training_count",
            "total_in_education_and_training_percent",
            "annual_change_percent",
        ],
    },
}


for source_id, config in (
    DFE_CONFIG.items()
):
    path = latest_snapshot(
        config["root"]
    )

    dataframe = read_csv(path)

    required = {
        "time_period",
        "time_identifier",
        config["geo_code"],
        config["geo_name"],
        *config["metrics"],
    }

    missing = sorted(
        required
        - set(dataframe.columns)
    )

    if missing:
        raise RuntimeError(
            f"{source_id} missing "
            f"required columns: {missing}"
        )

    dataframe = (
        dataframe
        .filter(
            F.col(
                config["geo_code"]
            ).isin(GM_CODES)
        )
        .withColumnRenamed(
            config["geo_code"],
            "borough_code",
        )
        .withColumnRenamed(
            config["geo_name"],
            "borough_name",
        )
    )

    for metric in (
        config["metrics"]
    ):
        dataframe = (
            add_disclosure_triplet(
                dataframe,
                metric,
            )
        )

    status_columns = [
        f"{metric}_value_status"
        for metric
        in config["metrics"]
    ]

    invalid_condition = reduce(
        lambda left, right:
            left | right,
        [
            F.col(column_name)
            == "invalid_token"
            for column_name
            in status_columns
        ],
    )

    invalid_rows = (
        dataframe.filter(
            invalid_condition
        )
    )

    invalid_count = (
        invalid_rows.count()
    )

    quarantine(
        invalid_rows,
        source_id,
        get_source_run_id(path),
    )

    dataframe = (
        dataframe.filter(
            ~invalid_condition
        )
    )

    dataframe = add_lineage(
        dataframe,
        source_id,
        path,
    )

    row_count = dataframe.count()

    record_dq(
        source_id,
        "row_count_positive",
        row_count > 0,
        row_count,
        "> 0",
    )

    record_dq(
        source_id,
        "disclosure_tokens_valid",
        invalid_count == 0,
        invalid_count,
        "0",
    )

    validate_borough_coverage(
        dataframe,
        source_id,
    )

    write_table(
        dataframe,
        config["table"],
    )


# SRC05: Nomis APS
source_id = "SRC05"

path = latest_snapshot(
    "raw/nomis/SRC05"
)

dataframe = read_csv(path)

for column in dataframe.columns:
    dataframe = (
        dataframe.withColumnRenamed(
            column,
            column.lower(),
        )
    )

required = {
    "date",
    "date_name",
    "geography_code",
    "geography_name",
    "variable_code",
    "variable_name",
    "obs_value",
    "obs_status",
    "obs_status_name",
}

missing = sorted(
    required
    - set(dataframe.columns)
)

if missing:
    raise RuntimeError(
        f"SRC05 missing required "
        f"columns: {missing}"
    )

dataframe = (
    dataframe
    .filter(
        F.col(
            "geography_code"
        ).isin(GM_CODES)
    )
    .withColumnRenamed(
        "geography_code",
        "borough_code",
    )
    .withColumnRenamed(
        "geography_name",
        "borough_name",
    )
)

obs_raw = F.trim(
    F.col("obs_value")
    .cast("string")
)

dataframe = (
    dataframe
    .withColumn(
        "obs_raw_value",
        F.col("obs_value")
        .cast("string"),
    )
    .withColumn(
        "obs_numeric_value",
        F.when(
            obs_raw.rlike(
                NUMERIC_PATTERN
            ),
            obs_raw.cast("double"),
        ).otherwise(
            F.lit(None)
            .cast("double")
        ),
    )
    .withColumn(
        "obs_value_status",
        F.when(
            F.col("obs_value").isNull()
            | (obs_raw == ""),
            F.lit("missing"),
        )
        .when(
            obs_raw.rlike(
                NUMERIC_PATTERN
            ),
            F.lit("reported"),
        )
        .otherwise(
            F.lit("invalid_token")
        ),
    )
    .drop("obs_value")
)

invalid_rows = (
    dataframe.filter(
        F.col(
            "obs_value_status"
        ) == "invalid_token"
    )
)

invalid_count = (
    invalid_rows.count()
)

quarantine(
    invalid_rows,
    source_id,
    get_source_run_id(path),
)

dataframe = (
    dataframe.filter(
        F.col(
            "obs_value_status"
        ) != "invalid_token"
    )
)

dataframe = add_lineage(
    dataframe,
    source_id,
    path,
)

row_count = dataframe.count()

variable_count = (
    dataframe
    .select("variable_code")
    .distinct()
    .count()
)

record_dq(
    source_id,
    "row_count_positive",
    row_count > 0,
    row_count,
    "> 0",
)

record_dq(
    source_id,
    "obs_values_parseable",
    invalid_count == 0,
    invalid_count,
    "0",
)

record_dq(
    source_id,
    "expected_variable_count",
    variable_count == 5,
    variable_count,
    "5",
)

validate_borough_coverage(
    dataframe,
    source_id,
)

write_table(
    dataframe,
    "nomis_aps",
)


# SRC06: controlled MBacc reference
source_id = "SRC06"

path = latest_snapshot(
    "raw/reference/SRC06"
)

dataframe = read_csv(path)

required = {
    "gateway_code",
    "gateway_name",
    "alternate_name",
    "source_authority",
    "is_current",
    "source_checked_date",
}

missing = sorted(
    required
    - set(dataframe.columns)
)

if missing:
    raise RuntimeError(
        f"SRC06 missing required "
        f"columns: {missing}"
    )

flag = F.lower(
    F.trim(
        F.col("is_current")
    )
)

dataframe = (
    dataframe
    .withColumn(
        "is_current_boolean",
        F.when(
            flag.isin(
                "true",
                "1",
                "yes",
                "y",
            ),
            F.lit(True),
        )
        .when(
            flag.isin(
                "false",
                "0",
                "no",
                "n",
            ),
            F.lit(False),
        )
        .otherwise(
            F.lit(None)
            .cast("boolean")
        ),
    )
    .drop("is_current")
    .withColumnRenamed(
        "is_current_boolean",
        "is_current",
    )
    .withColumn(
        "source_checked_date",
        F.to_date(
            F.col(
                "source_checked_date"
            )
        ),
    )
)

invalid_flag_count = (
    dataframe
    .filter(
        F.col(
            "is_current"
        ).isNull()
    )
    .count()
)

dataframe = add_lineage(
    dataframe,
    source_id,
    path,
)

row_count = dataframe.count()

gateway_count = (
    dataframe
    .select("gateway_code")
    .distinct()
    .count()
)

record_dq(
    source_id,
    "gateway_row_count",
    row_count == 7,
    row_count,
    "7",
)

record_dq(
    source_id,
    "gateway_code_uniqueness",
    gateway_count == 7,
    gateway_count,
    "7",
)

record_dq(
    source_id,
    "is_current_valid",
    invalid_flag_count == 0,
    invalid_flag_count,
    "0",
)

write_table(
    dataframe,
    "mbacc_gateway",
)


dq_dataframe = (
    spark.createDataFrame(
        dq_results
    )
    .withColumn(
        "checked_at_utc",
        F.current_timestamp(),
    )
)

(
    dq_dataframe.write
    .format("delta")
    .mode("append")
    .saveAsTable(
        "data_quality_result"
    )
)

print()
print(
    "PROCESSING RUN:",
    PROCESSING_RUN_ID,
)

print()
print("TABLE COUNTS:")

print(
    json.dumps(
        table_counts,
        indent=2,
    )
)

print()
print("DQ RESULTS:")

dq_dataframe.orderBy(
    "source_id",
    "check_name",
).show(
    100,
    truncate=False,
)

if critical_failures:
    raise RuntimeError(
        "Critical Silver DQ "
        "failures: "
        + ", ".join(
            sorted(
                set(
                    critical_failures
                )
            )
        )
    )

RESULT = {
    "status": "success",
    "processing_run_id":
        PROCESSING_RUN_ID,
    "tables": table_counts,
}

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

notebookutils.notebook.exit(
    json.dumps(RESULT)
)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
