from __future__ import annotations

import json
import subprocess
import sys
import time
import urllib.error
import urllib.request

WORKSPACE_ID = "81e75ca0-f556-48c0-9dea-4851ce7bf916"
WAREHOUSE_ID = "ce6454df-212a-438a-809d-7f77075fb5c9"

FABRIC_API = "https://api.fabric.microsoft.com/v1"

PIPELINES = [
    (
        "pl_ingest_dfe",
        "d74cac73-5175-47e6-b3e1-f36bb54e5c3d",
    ),
    (
        "pl_ingest_nomis",
        "9d8cf3d5-3430-4bb0-8814-a8e5cd8ada1f",
    ),
    (
        "pl_bronze_to_silver",
        "e446f1f5-a03c-462e-aada-0dfe5bc21903",
    ),
    (
        "pl_silver_model",
        "9ab81518-0410-4bfc-bf80-ad031df6a5f3",
    ),
    (
        "pl_silver_to_gold",
        "304cee55-294a-4999-9410-b6a0e6c5f809",
    ),
]

TERMINAL = {
    "Completed",
    "Failed",
    "Cancelled",
    "Deduped",
}


def access_token(resource: str) -> str:
    return subprocess.check_output(
        [
            "az",
            "account",
            "get-access-token",
            "--resource",
            resource,
            "--query",
            "accessToken",
            "-o",
            "tsv",
        ],
        text=True,
    ).strip()


def fabric_request(
    url: str,
    *,
    method: str = "GET",
    data: bytes | None = None,
):
    request = urllib.request.Request(
        url,
        method=method,
        data=data,
        headers={
            "Authorization": (
                "Bearer "
                + access_token(
                    "https://api.fabric.microsoft.com"
                )
            ),
            "Content-Type": "application/json",
        },
    )

    try:
        return urllib.request.urlopen(
            request,
            timeout=60,
        )

    except urllib.error.HTTPError as exc:
        body = exc.read().decode(
            "utf-8",
            errors="replace",
        )

        raise RuntimeError(
            f"Fabric HTTP {exc.code}: {body}"
        ) from exc


def run_pipeline(
    name: str,
    pipeline_id: str,
):
    print()
    print("=" * 72)
    print(f"START {name}")
    print("=" * 72)

    start_url = (
        f"{FABRIC_API}"
        f"/workspaces/{WORKSPACE_ID}"
        f"/dataPipelines/{pipeline_id}"
        f"/jobs/execute/instances"
    )

    with fabric_request(
        start_url,
        method="POST",
        data=b"",
    ) as response:
        if response.status != 202:
            raise RuntimeError(
                f"{name} returned HTTP "
                f"{response.status}"
            )

        location = response.headers.get(
            "Location"
        )

        retry_after = int(
            response.headers.get(
                "Retry-After",
                "20",
            )
        )

    if not location:
        raise RuntimeError(
            f"{name} returned no Location header."
        )

    run_id = location.rstrip("/").split("/")[-1]

    print(f"Run ID: {run_id}")

    time.sleep(
        min(
            max(retry_after, 5),
            60,
        )
    )

    deadline = time.monotonic() + (60 * 45)

    while True:
        if time.monotonic() > deadline:
            raise TimeoutError(
                f"{name} exceeded 45 minutes."
            )

        with fabric_request(
            location
        ) as response:
            result = json.load(response)

        status = result.get(
            "status",
            "Unknown",
        )

        print(
            f"{name}: {status}",
            flush=True,
        )

        if status in TERMINAL:
            if status != "Completed":
                raise RuntimeError(
                    f"{name} ended with "
                    f"{status}: "
                    f"{result.get('failureReason')}"
                )

            return run_id

        time.sleep(20)


def warehouse_connection_string() -> str:
    url = (
        f"{FABRIC_API}"
        f"/workspaces/{WORKSPACE_ID}"
        f"/warehouses/{WAREHOUSE_ID}"
    )

    with fabric_request(url) as response:
        payload = json.load(response)

    value = (
        payload
        .get("properties", {})
        .get("connectionString")
    )

    if not value:
        raise RuntimeError(
            "Fabric did not return the Gold "
            "Warehouse connection string."
        )

    return value


def main():
    completed = {}

    for name, pipeline_id in PIPELINES:
        completed[name] = run_pipeline(
            name,
            pipeline_id,
        )

    print()
    print("=" * 72)
    print("FABRIC CHAIN COMPLETE")
    print("=" * 72)

    for name, run_id in completed.items():
        print(f"{name}: {run_id}")

    endpoint = warehouse_connection_string()

    print()
    print(
        "Exporting validated public dashboard "
        "snapshot..."
    )

    subprocess.run(
        [
            sys.executable,
            "scripts/export_public_dashboard_data.py",
            "--sql-endpoint",
            endpoint,
            "--database",
            "wh_gm_skills_gold",
            "--output-dir",
            "data/public/build",
        ],
        check=True,
    )

    print()
    print("PUBLIC EXPORT COMPLETE")


if __name__ == "__main__":
    main()
