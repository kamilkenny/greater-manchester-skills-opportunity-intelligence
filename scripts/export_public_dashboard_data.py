import json
import os
import struct
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import pyodbc

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "web" / "data"

OUTPUT.mkdir(
    parents=True,
    exist_ok=True,
)

SQL_ENDPOINT = os.environ[
    "GOLD_SQL_ENDPOINT"
]

DATABASE = os.environ.get(
    "GOLD_DATABASE",
    "wh_gm_skills_gold",
)


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


def access_token():
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


def serialise(value):
    if value is None:
        return None

    if hasattr(value, "isoformat"):
        return value.isoformat()

    return value


def fetch_rows(cursor, query):
    cursor.execute(query)

    columns = [
        column[0]
        for column in cursor.description
    ]

    rows = []

    for record in cursor.fetchall():
        rows.append(
            {
                column: serialise(value)
                for column, value
                in zip(columns, record, strict=False)
            }
        )

    return rows


token = access_token()
token_bytes = token.encode("utf-16-le")

packed_token = (
    struct.pack(
        "<I",
        len(token_bytes),
    )
    + token_bytes
)

connection_string = (
    "Driver={ODBC Driver 18 for SQL Server};"
    f"Server=tcp:{SQL_ENDPOINT},1433;"
    f"Database={DATABASE};"
    "Encrypt=yes;"
    "TrustServerCertificate=no;"
    "Connection Timeout=30;"
)

manifest = {}

with pyodbc.connect(
    connection_string,
    attrs_before={
        1256: packed_token
    },
) as connection:

    cursor = connection.cursor()

    print("=" * 72)
    print("GM SKILLSFLOW PUBLIC DATA EXPORT")
    print("=" * 72)

    for filename, query in EXPORTS.items():

        rows = fetch_rows(
            cursor,
            query,
        )

        path = OUTPUT / filename

        path.write_text(
            json.dumps(
                rows,
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )

        manifest[filename] = len(rows)

        print(
            f"PASS {filename:<30} "
            f"{len(rows):>5} rows"
        )


exported_at = datetime.now(
    UTC
).isoformat()

metadata = {
    "product": "GM SkillsFlow",
    "title": (
        "Greater Manchester Skills "
        "& Opportunity Intelligence"
    ),
    "exported_at_utc": exported_at,
    "warehouse": DATABASE,
    "datasets": manifest,
    "reporting_periods": {
        "apprenticeships": "2025/26",
        "youth_transition": "2026",
        "labour_market":
            "Apr 2025-Mar 2026",
        "qualifications":
            "Jan 2025-Dec 2025",
    },
    "disclosure_note": (
        "Null values may represent official "
        "suppression or unavailable values. "
        "Suppressed values are not reconstructed."
    ),
}

(
    OUTPUT
    / "metadata.json"
).write_text(
    json.dumps(
        metadata,
        indent=2,
        ensure_ascii=False,
    )
    + "\n",
    encoding="utf-8",
)

print(
    f"PASS {'metadata.json':<30} "
    "metadata"
)

print()
print(
    "PUBLIC DATA EXPORT COMPLETE"
)
