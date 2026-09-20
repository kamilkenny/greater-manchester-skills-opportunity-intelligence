from __future__ import annotations

import argparse
import hashlib
import json
import os
import struct
import subprocess
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pyodbc
import yaml

WORKSPACE_ID = "81e75ca0-f556-48c0-9dea-4851ce7bf916"
GOLD_ID = "ce6454df-212a-438a-809d-7f77075fb5c9"
GOLD_DB = "wh_gm_skills_gold"

EXPECTED_SOURCE_IDS = {
    "SRC01",
    "SRC02",
    "SRC03",
    "SRC04",
    "SRC05",
    "SRC06",
}


def _az(args: list[str]) -> str:
    env = dict(os.environ)
    env.setdefault(
        "AZURE_CONFIG_DIR",
        str(Path.home() / ".azure-fabric"),
    )

    result = subprocess.run(
        ["az", *args],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )

    return result.stdout.strip()


def _first(
    source: dict[str, Any],
    keys: tuple[str, ...],
    default: Any = None,
) -> Any:
    for key in keys:
        value = source.get(key)

        if value not in (None, ""):
            return value

    return default


def _nested_first(
    source: dict[str, Any],
    containers: tuple[str, ...],
    keys: tuple[str, ...],
    default: Any = None,
) -> Any:
    value = _first(source, keys)

    if value not in (None, ""):
        return value

    for container in containers:
        nested = source.get(container)

        if not isinstance(nested, dict):
            continue

        value = _first(nested, keys)

        if value not in (None, ""):
            return value

    return default


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value

    if isinstance(value, (int, float)):
        return bool(value)

    if isinstance(value, str):
        return value.strip().lower() not in {
            "false",
            "0",
            "no",
            "off",
            "disabled",
        }

    return True


def load_sources(path: Path) -> list[dict[str, Any]]:
    document = yaml.safe_load(
        path.read_text(encoding="utf-8")
    )

    if not isinstance(document, dict):
        raise ValueError(
            "sources.yaml must contain a mapping."
        )

    raw_sources = document.get(
        "sources",
        document,
    )

    entries: list[tuple[str, dict[str, Any]]] = []

    if isinstance(raw_sources, list):
        for source in raw_sources:
            if not isinstance(source, dict):
                continue

            source_id = (
                source.get("source_id")
                or source.get("id")
            )

            if not source_id:
                raise ValueError(
                    "Source entry is missing source_id."
                )

            entries.append(
                (str(source_id), source)
            )

    elif isinstance(raw_sources, dict):
        for key, source in raw_sources.items():
            if not isinstance(source, dict):
                continue

            source_id = (
                source.get("source_id")
                or source.get("id")
                or key
            )

            entries.append(
                (str(source_id), source)
            )

    else:
        raise ValueError(
            "sources must be a list or mapping."
        )

    normalised = [
        normalise_source(source_id, source)
        for source_id, source in entries
    ]

    source_ids = {
        source["source_id"]
        for source in normalised
    }

    if source_ids != EXPECTED_SOURCE_IDS:
        raise ValueError(
            "Unexpected source registry. "
            f"Expected {sorted(EXPECTED_SOURCE_IDS)}, "
            f"found {sorted(source_ids)}."
        )

    return sorted(
        normalised,
        key=lambda row: row["source_id"],
    )


def normalise_source(
    source_id: str,
    source: dict[str, Any],
) -> dict[str, Any]:
    containers = (
        "source",
        "connection",
        "ingestion",
        "destination",
        "bronze",
    )

    source_name = str(
        _first(
            source,
            (
                "source_name",
                "name",
                "display_name",
                "title",
            ),
            source_id,
        )
    )

    source_type = str(
        _first(
            source,
            (
                "source_type",
                "type",
                "ingestion_type",
            ),
            "unknown",
        )
    )

    endpoint = _nested_first(
        source,
        containers,
        (
            "endpoint",
            "url",
            "base_url",
            "source_url",
            "download_url",
        ),
    )

    target_path = _nested_first(
        source,
        containers,
        (
            "target_path",
            "bronze_path",
            "destination_path",
            "path",
        ),
    )

    if not target_path:
        raise ValueError(
            f"{source_id} has no target path."
        )

    file_format = str(
        _nested_first(
            source,
            containers,
            (
                "file_format",
                "format",
                "source_format",
            ),
            "csv",
        )
    )

    refresh_frequency = str(
        _first(
            source,
            (
                "refresh_frequency",
                "frequency",
                "cadence",
                "schedule",
            ),
            "manual",
        )
    )

    record = {
        "source_id": source_id,
        "source_name": source_name,
        "source_type": source_type,
        "endpoint": (
            str(endpoint)
            if endpoint is not None
            else None
        ),
        "target_path": str(target_path),
        "file_format": file_format,
        "refresh_frequency": refresh_frequency,
        "enabled": _as_bool(
            source.get("enabled", True)
        ),
    }

    record["config_hash"] = config_hash(record)

    return record


def config_hash(
    record: dict[str, Any],
) -> str:
    payload = {
        key: value
        for key, value in record.items()
        if key != "config_hash"
    }

    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )

    return hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()


def change_action(
    existing_hash: str | None,
    incoming_hash: str,
) -> str:
    if existing_hash is None:
        return "insert"

    if existing_hash == incoming_hash:
        return "unchanged"

    return "archive_and_update"


def gold_connection() -> pyodbc.Connection:
    server = _az(
        [
            "rest",
            "--method",
            "GET",
            "--url",
            (
                "https://api.fabric.microsoft.com/v1/"
                f"workspaces/{WORKSPACE_ID}/"
                f"warehouses/{GOLD_ID}/"
                "connectionString"
            ),
            "--resource",
            "https://api.fabric.microsoft.com",
            "--query",
            "connectionString",
            "-o",
            "tsv",
        ]
    )

    access_token = _az(
        [
            "account",
            "get-access-token",
            "--resource",
            "https://database.windows.net/",
            "--query",
            "accessToken",
            "-o",
            "tsv",
        ]
    )

    drivers = [
        driver
        for driver in pyodbc.drivers()
        if "SQL Server" in driver
    ]

    if not drivers:
        raise RuntimeError(
            "No SQL Server ODBC driver found."
        )

    driver = drivers[-1]

    token_bytes = access_token.encode(
        "utf-16-le"
    )

    token_struct = struct.pack(
        f"<I{len(token_bytes)}s",
        len(token_bytes),
        token_bytes,
    )

    connection_string = (
        f"Driver={{{driver}}};"
        f"Server={server};"
        f"Database={GOLD_DB};"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
    )

    return pyodbc.connect(
        connection_string,
        attrs_before={
            1256: token_struct
        },
        timeout=30,
        autocommit=False,
    )


def ensure_schema(
    cursor: pyodbc.Cursor,
) -> None:
    current_columns = {
        row[0]
        for row in cursor.execute(
            """
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'ctl'
              AND TABLE_NAME = 'source_config';
            """
        ).fetchall()
    }

    history_columns = {
        row[0]
        for row in cursor.execute(
            """
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'hist'
              AND TABLE_NAME = 'source_config';
            """
        ).fetchall()
    }

    required_current = {
        "source_id",
        "source_name",
        "source_type",
        "endpoint",
        "target_path",
        "file_format",
        "refresh_frequency",
        "enabled",
        "last_watermark",
        "config_hash",
        "updated_at_utc",
        "source_run_id",
    }

    required_history = (
        required_current
        | {
            "valid_from_utc",
            "valid_to_utc",
            "archived_at_utc",
        }
    )

    missing_current = (
        required_current - current_columns
    )

    missing_history = (
        required_history - history_columns
    )

    if missing_current:
        raise RuntimeError(
            "ctl.source_config is missing: "
            f"{sorted(missing_current)}"
        )

    if missing_history:
        raise RuntimeError(
            "hist.source_config is missing: "
            f"{sorted(missing_history)}"
        )


def synchronise(
    sources: list[dict[str, Any]],
    *,
    dry_run: bool,
) -> None:
    run_id = str(uuid.uuid4())
    now = datetime.now(UTC).replace(
        tzinfo=None
    )

    connection = gold_connection()

    try:
        cursor = connection.cursor()
        ensure_schema(cursor)

        summary = {
            "insert": 0,
            "unchanged": 0,
            "archive_and_update": 0,
        }

        for source in sources:
            source_id = source["source_id"]

            existing = cursor.execute(
                """
                SELECT
                    source_name,
                    source_type,
                    endpoint,
                    target_path,
                    file_format,
                    refresh_frequency,
                    enabled,
                    last_watermark,
                    config_hash,
                    updated_at_utc,
                    source_run_id
                FROM ctl.source_config
                WHERE source_id = ?;
                """,
                source_id,
            ).fetchone()

            existing_hash = (
                existing[8]
                if existing
                else None
            )

            action = change_action(
                existing_hash,
                source["config_hash"],
            )

            summary[action] += 1

            print(
                f"{source_id:<6} {action}"
            )

            if dry_run:
                continue

            if action == "unchanged":
                continue

            if action == "insert":
                cursor.execute(
                    """
                    INSERT INTO ctl.source_config (
                        source_id,
                        source_name,
                        source_type,
                        endpoint,
                        target_path,
                        file_format,
                        refresh_frequency,
                        enabled,
                        last_watermark,
                        config_hash,
                        updated_at_utc,
                        source_run_id
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    source_id,
                    source["source_name"],
                    source["source_type"],
                    source["endpoint"],
                    source["target_path"],
                    source["file_format"],
                    source["refresh_frequency"],
                    source["enabled"],
                    None,
                    source["config_hash"],
                    now,
                    run_id,
                )

                continue

            previous_valid_from = (
                existing[9]
                if existing[9] is not None
                else now
            )

            cursor.execute(
                """
                INSERT INTO hist.source_config (
                    source_id,
                    source_name,
                    source_type,
                    endpoint,
                    target_path,
                    file_format,
                    refresh_frequency,
                    enabled,
                    last_watermark,
                    config_hash,
                    updated_at_utc,
                    source_run_id,
                    valid_from_utc,
                    valid_to_utc,
                    archived_at_utc
                )
                VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?
                );
                """,
                source_id,
                existing[0],
                existing[1],
                existing[2],
                existing[3],
                existing[4],
                existing[5],
                existing[6],
                existing[7],
                existing[8],
                existing[9],
                existing[10],
                previous_valid_from,
                now,
                now,
            )

            cursor.execute(
                """
                UPDATE ctl.source_config
                SET
                    source_name = ?,
                    source_type = ?,
                    endpoint = ?,
                    target_path = ?,
                    file_format = ?,
                    refresh_frequency = ?,
                    enabled = ?,
                    config_hash = ?,
                    updated_at_utc = ?,
                    source_run_id = ?
                WHERE source_id = ?;
                """,
                source["source_name"],
                source["source_type"],
                source["endpoint"],
                source["target_path"],
                source["file_format"],
                source["refresh_frequency"],
                source["enabled"],
                source["config_hash"],
                now,
                run_id,
                source_id,
            )

        print()
        print("SCD4 SUMMARY")
        print(
            json.dumps(
                summary,
                indent=2,
            )
        )

        if dry_run:
            connection.rollback()
            print("Dry run. No changes committed.")
        else:
            connection.commit()
            print(
                "SCD4 source configuration "
                "synchronisation committed."
            )

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--config",
        default="config/sources.yaml",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
    )

    args = parser.parse_args()

    sources = load_sources(
        Path(args.config)
    )

    print(
        f"Loaded {len(sources)} "
        "controlled source configurations."
    )

    synchronise(
        sources,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
