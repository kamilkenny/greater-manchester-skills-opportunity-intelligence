import argparse
import hashlib
import json
import os
import shutil
import struct
import subprocess
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

import pyodbc

ROOT = Path(__file__).resolve().parents[1]

DEFAULT_OUTPUT = (
    ROOT
    / "data"
    / "public"
    / "build"
)

DEFAULT_DATABASE = "wh_gm_skills_gold"


EXPORTS = {
    "borough-current.json": """
        SELECT *
        FROM mart.borough_current_snapshot
        ORDER BY borough_name;
    """,
    "borough-kpis.json": """
        SELECT *
        FROM mart.borough_kpi_current
        ORDER BY borough_name, kpi_code;
    """,
    "kpi-definitions.json": """
        SELECT *
        FROM mart.kpi_definition
        ORDER BY domain_name, kpi_code;
    """,
    "skills-supply.json": """
        SELECT *
        FROM mart.skills_supply
        ORDER BY borough_name, time_period;
    """,
    "mbacc-pathways.json": """
        SELECT *
        FROM mart.mbacc_pathway
        ORDER BY
            borough_name,
            time_period,
            gateway_code;
    """,
    "youth-transition.json": """
        SELECT *
        FROM mart.youth_transition
        ORDER BY borough_name, time_period;
    """,
    "borough-opportunity.json": """
        SELECT *
        FROM mart.borough_opportunity
        ORDER BY borough_name, date;
    """,
}


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Build a validated disclosure-safe "
            "GM SkillsFlow public snapshot."
        )
    )

    parser.add_argument(
        "--sql-endpoint",
        help=(
            "Fabric Warehouse SQL endpoint. "
            "Defaults to GOLD_SQL_ENDPOINT."
        ),
    )

    parser.add_argument(
        "--database",
        help=(
            "Fabric Warehouse database. "
            "Defaults to GOLD_DATABASE or "
            "wh_gm_skills_gold."
        ),
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=(
            "Candidate snapshot directory. "
            "Existing contents are replaced only "
            "after validation succeeds."
        ),
    )

    return parser.parse_args()


def get_access_token():
    return subprocess.check_output(
        [
            "az",
            "account",
            "get-access-token",
            "--resource",
            "https://database.windows.net/",
            "--query",
            "accessToken",
            "-o",
            "tsv",
        ],
        text=True,
    ).strip()


def select_driver():
    installed = pyodbc.drivers()

    for driver in (
        "ODBC Driver 18 for SQL Server",
        "ODBC Driver 17 for SQL Server",
    ):
        if driver in installed:
            return driver

    raise RuntimeError(
        "No supported SQL Server ODBC driver found."
    )


def connect(sql_endpoint, database):
    token = get_access_token().encode(
        "utf-16-le"
    )

    token_struct = struct.pack(
        f"<I{len(token)}s",
        len(token),
        token,
    )

    driver = select_driver()

    connection_string = (
        f"Driver={{{driver}}};"
        f"Server={sql_endpoint};"
        f"Database={database};"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
        "Connection Timeout=30;"
    )

    return pyodbc.connect(
        connection_string,
        attrs_before={
            1256: token_struct,
        },
        autocommit=True,
    )


def serialise(value):
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(
                tzinfo=UTC
            )

        return value.astimezone(
            UTC
        ).isoformat()

    if isinstance(value, date):
        return value.isoformat()

    if isinstance(value, Decimal):
        return float(value)

    if isinstance(value, bytes):
        return value.hex()

    raise TypeError(
        f"Unsupported JSON value: {type(value)!r}"
    )


def fetch_rows(cursor, query):
    cursor.execute(query)

    columns = [
        column[0]
        for column in cursor.description
    ]

    return [
        dict(
            zip(
                columns,
                row,
                strict=True,
            )
        )
        for row in cursor.fetchall()
    ]


def write_json(path, value):
    path.write_text(
        json.dumps(
            value,
            ensure_ascii=False,
            default=serialise,
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
    )


def validate(exports):
    expected_exact = {
        "borough-current.json": 10,
        "borough-kpis.json": 120,
        "kpi-definitions.json": 12,
    }

    for filename, expected in (
        expected_exact.items()
    ):
        actual = len(exports[filename])

        if actual != expected:
            raise RuntimeError(
                f"{filename}: expected "
                f"{expected} rows, got {actual}."
            )

    for filename, rows in exports.items():
        if not rows:
            raise RuntimeError(
                f"{filename}: no rows returned."
            )

    borough_rows = exports[
        "borough-current.json"
    ]

    borough_codes = {
        row["borough_code"]
        for row in borough_rows
    }

    if len(borough_codes) != 10:
        raise RuntimeError(
            "Current snapshot does not contain "
            "10 unique borough codes."
        )

    kpi_rows = exports[
        "borough-kpis.json"
    ]

    kpi_keys = {
        (
            row["borough_code"],
            row["kpi_code"],
        )
        for row in kpi_rows
    }

    if len(kpi_keys) != 120:
        raise RuntimeError(
            "KPI serving layer does not contain "
            "120 unique borough/KPI pairs."
        )


def calculate_fingerprint(directory):
    digest = hashlib.sha256()

    for filename in sorted(EXPORTS):
        path = directory / filename

        digest.update(
            filename.encode("utf-8")
        )

        digest.update(
            path.read_bytes()
        )

    return digest.hexdigest()


def replace_directory(
    candidate,
    destination,
):
    if destination.exists():
        shutil.rmtree(destination)

    candidate.rename(destination)


def main():
    args = parse_args()

    sql_endpoint = (
        args.sql_endpoint
        or os.environ.get(
            "GOLD_SQL_ENDPOINT"
        )
    )

    database = (
        args.database
        or os.environ.get(
            "GOLD_DATABASE"
        )
        or DEFAULT_DATABASE
    )

    if not sql_endpoint:
        raise RuntimeError(
            "Fabric SQL endpoint is required. "
            "Use --sql-endpoint or set "
            "GOLD_SQL_ENDPOINT."
        )

    output = args.output_dir.resolve()

    candidate = output.parent / (
        f".{output.name}.candidate"
    )

    if candidate.exists():
        shutil.rmtree(candidate)

    candidate.mkdir(
        parents=True,
        exist_ok=False,
    )

    print(
        "GM SKILLSFLOW PUBLIC SNAPSHOT"
    )

    print(
        f"Warehouse: {database}"
    )

    exports = {}

    try:
        with connect(
            sql_endpoint,
            database,
        ) as connection:
            cursor = connection.cursor()

            for filename, query in (
                EXPORTS.items()
            ):
                rows = fetch_rows(
                    cursor,
                    query,
                )

                exports[filename] = rows

                write_json(
                    candidate / filename,
                    rows,
                )

                print(
                    f"PASS {filename:<30} "
                    f"{len(rows):>6,} rows"
                )

        validate(exports)

        fingerprint = (
            calculate_fingerprint(
                candidate
            )
        )

        exported_at = datetime.now(
            UTC
        ).isoformat()

        row_counts = {
            filename: len(rows)
            for filename, rows
            in exports.items()
        }

        metadata = {
            "product": "GM SkillsFlow",
            "title": (
                "Greater Manchester Skills "
                "& Opportunity Intelligence"
            ),
            "schema_version": 1,
            "status": "valid",
            "snapshot_id": fingerprint[:16],
            "data_fingerprint": fingerprint,
            "exported_at_utc": exported_at,
            "warehouse": database,
            "row_counts": row_counts,
            "reporting_period_policy": (
                "Each indicator retains its "
                "source reporting period."
            ),
            "disclosure_policy": (
                "Suppressed or partially "
                "reportable values remain null "
                "with governed value status."
            ),
        }

        write_json(
            candidate / "metadata.json",
            metadata,
        )

        size_bytes = sum(
            path.stat().st_size
            for path in candidate.iterdir()
            if path.is_file()
        )

        replace_directory(
            candidate,
            output,
        )

        print()
        print(
            "PUBLIC SNAPSHOT VALIDATED"
        )

        print(
            f"snapshot_id: "
            f"{metadata['snapshot_id']}"
        )

        print(
            f"fingerprint: {fingerprint}"
        )

        print(
            f"size_bytes: {size_bytes:,}"
        )

        print(
            f"output: {output}"
        )

    except Exception:
        if candidate.exists():
            shutil.rmtree(candidate)

        raise


if __name__ == "__main__":
    main()
