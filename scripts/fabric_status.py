from __future__ import annotations

import json
import os
import subprocess
import urllib.request
from datetime import UTC, datetime, timedelta
from pathlib import Path

FABRIC_API = "https://api.fabric.microsoft.com/v1"
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


def request_json(
    url: str,
    access_token: str,
    *,
    method: str = "GET",
    body: dict | None = None,
) -> dict:
    data = None

    headers = {
        "Authorization": f"Bearer {access_token}",
    }

    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(
        url,
        method=method,
        data=data,
        headers=headers,
    )

    with urllib.request.urlopen(request) as response:
        payload = response.read()

    if not payload:
        return {}

    return json.loads(payload.decode("utf-8"))


def main() -> None:
    if not RUNTIME.exists():
        raise SystemExit(
            "No .runtime/last_job.json found."
        )

    state = json.loads(
        RUNTIME.read_text(encoding="utf-8")
    )

    access_token = token()

    response = request_json(
        state["location"],
        access_token,
    )

    status = response.get("status", "Unknown")

    print("=" * 70)
    print("FABRIC JOB STATUS")
    print("=" * 70)
    print(f"Pipeline: {state['pipeline_name']}")
    print(f"Job ID:   {state['job_id']}")
    print(f"Status:   {status}")
    print(
        f"Started:  "
        f"{response.get('startTimeUtc', '-')}"
    )
    print(
        f"Ended:    "
        f"{response.get('endTimeUtc', '-')}"
    )

    if response.get("failureReason"):
        print(
            "Failure:  "
            f"{response['failureReason']}"
        )

    if status not in {"Completed", "Succeeded"}:
        return

    print()
    print("=" * 70)
    print("ACTIVITY OUTPUT")
    print("=" * 70)

    start_text = response.get("startTimeUtc")

    if start_text:
        start = datetime.fromisoformat(
            start_text.replace("Z", "+00:00")
        )
    else:
        start = datetime.now(UTC) - timedelta(hours=2)

    end_text = response.get("endTimeUtc")

    if end_text:
        end = datetime.fromisoformat(
            end_text.replace("Z", "+00:00")
        )
    else:
        end = datetime.now(UTC)

    start -= timedelta(minutes=5)
    end += timedelta(minutes=5)

    activity_url = (
        f"{FABRIC_API}/workspaces/"
        f"{state['workspace_id']}"
        f"/datapipelines/pipelineruns/"
        f"{state['job_id']}"
        f"/queryactivityruns"
    )

    activity_response = request_json(
        activity_url,
        access_token,
        method="POST",
        body={
            "filters": [],
            "orderBy": [
                {
                    "orderBy": "ActivityRunStart",
                    "order": "ASC",
                }
            ],
            "lastUpdatedAfter": start.strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            ),
            "lastUpdatedBefore": end.strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            ),
        },
    )

    activities = activity_response.get(
        "value",
        activity_response
        if isinstance(activity_response, list)
        else [],
    )

    for activity in activities:
        print()
        print(
            f"Activity: "
            f"{activity.get('activityName', '-')}"
        )
        print(
            f"Type:     "
            f"{activity.get('activityType', '-')}"
        )
        print(
            f"Status:   "
            f"{activity.get('status', '-')}"
        )

        output = activity.get("output") or {}
        result = output.get("result") or {}

        exit_value = result.get("exitValue")

        if exit_value:
            print("Exit value:")

            try:
                parsed = json.loads(exit_value)
                print(
                    json.dumps(
                        parsed,
                        indent=2,
                    )
                )
            except json.JSONDecodeError:
                print(exit_value)

        error = activity.get("error") or {}

        if error.get("message"):
            print(
                "Error:    "
                f"{error['message']}"
            )


if __name__ == "__main__":
    main()
