from __future__ import annotations

import argparse
import json
import os
import subprocess
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

WORKSPACE_ID = "81e75ca0-f556-48c0-9dea-4851ce7bf916"
FABRIC_API = "https://api.fabric.microsoft.com/v1"

PIPELINES = {
    "pl_ingest_dfe": "d74cac73-5175-47e6-b3e1-f36bb54e5c3d",
    "pl_ingest_nomis": "9d8cf3d5-3430-4bb0-8814-a8e5cd8ada1f",
    "pl_bronze_to_silver": "e446f1f5-a03c-462e-aada-0dfe5bc21903",
    "pl_silver_model": "9ab81518-0410-4bfc-bf80-ad031df6a5f3",
    "pl_silver_to_gold": "304cee55-294a-4999-9410-b6a0e6c5f809",
}

RUNTIME = Path(".runtime/last_job.json")


def token() -> str:
    os.environ.setdefault(
        "AZURE_CONFIG_DIR",
        str(Path.home() / ".azure-fabric"),
    )

    result = subprocess.run(
        [
            "az",
            "account",
            "get-access-token",
            "--resource",
            "https://api.fabric.microsoft.com",
            "--query",
            "accessToken",
            "-o",
            "tsv",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    return result.stdout.strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "pipeline",
        choices=sorted(PIPELINES),
    )
    args = parser.parse_args()

    pipeline_id = PIPELINES[args.pipeline]

    url = (
        f"{FABRIC_API}/workspaces/{WORKSPACE_ID}"
        f"/dataPipelines/{pipeline_id}"
        f"/jobs/execute/instances"
    )

    request = urllib.request.Request(
        url,
        method="POST",
        data=b"",
        headers={
            "Authorization": f"Bearer {token()}",
            "Content-Length": "0",
        },
    )

    with urllib.request.urlopen(request) as response:
        if response.status != 202:
            raise RuntimeError(
                f"Unexpected HTTP status: {response.status}"
            )

        location = response.headers.get("Location")
        retry_after = response.headers.get(
            "Retry-After",
            "60",
        )

    if not location:
        raise RuntimeError(
            "Fabric returned 202 without a Location header."
        )

    job_id = location.rstrip("/").split("/")[-1]

    state = {
        "workspace_id": WORKSPACE_ID,
        "pipeline_name": args.pipeline,
        "pipeline_id": pipeline_id,
        "job_id": job_id,
        "location": location,
        "submitted_at_utc": datetime.now(UTC).isoformat(),
    }

    RUNTIME.parent.mkdir(parents=True, exist_ok=True)
    RUNTIME.write_text(
        json.dumps(state, indent=2) + "\n",
        encoding="utf-8",
    )

    print("Fabric job submitted")
    print(f"Pipeline:    {args.pipeline}")
    print(f"Pipeline ID: {pipeline_id}")
    print(f"Job ID:      {job_id}")
    print(f"Retry after: {retry_after} seconds")
    print()
    print("Check later with:")
    print("python scripts/fabric_status.py")


if __name__ == "__main__":
    main()
