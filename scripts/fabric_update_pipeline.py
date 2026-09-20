from __future__ import annotations

import argparse
import base64
import json
import os
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

WORKSPACE_ID = "81e75ca0-f556-48c0-9dea-4851ce7bf916"
FABRIC_API = "https://api.fabric.microsoft.com/v1"

PIPELINES = {
    "pl_ingest_dfe":
        "d74cac73-5175-47e6-b3e1-f36bb54e5c3d",
    "pl_ingest_nomis":
        "9d8cf3d5-3430-4bb0-8814-a8e5cd8ada1f",
    "pl_bronze_to_silver":
        "e446f1f5-a03c-462e-aada-0dfe5bc21903",
    "pl_silver_model":
        "9ab81518-0410-4bfc-bf80-ad031df6a5f3",
    "pl_silver_to_gold":
        "304cee55-294a-4999-9410-b6a0e6c5f809",
}


def get_token() -> str:
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


def encode_file(path: Path) -> str:
    return base64.b64encode(
        path.read_bytes()
    ).decode("ascii")


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "pipeline",
        choices=sorted(PIPELINES),
    )

    args = parser.parse_args()

    pipeline_id = PIPELINES[args.pipeline]

    directory = (
        Path("fabric/pipelines")
        / args.pipeline
    )

    content_file = (
        directory / "pipeline-content.json"
    )

    platform_file = directory / ".platform"

    if not content_file.exists():
        raise SystemExit(
            f"Missing {content_file}"
        )

    # Validate JSON before sending anything to Fabric.
    json.loads(
        content_file.read_text(
            encoding="utf-8"
        )
    )

    parts = [
        {
            "path": "pipeline-content.json",
            "payload": encode_file(
                content_file
            ),
            "payloadType": "InlineBase64",
        }
    ]

    if platform_file.exists():
        parts.append(
            {
                "path": ".platform",
                "payload": encode_file(
                    platform_file
                ),
                "payloadType": "InlineBase64",
            }
        )

    payload = json.dumps(
        {
            "definition": {
                "parts": parts,
            }
        }
    ).encode("utf-8")

    url = (
        f"{FABRIC_API}/workspaces/"
        f"{WORKSPACE_ID}"
        f"/dataPipelines/"
        f"{pipeline_id}"
        f"/updateDefinition"
    )

    request = urllib.request.Request(
        url,
        method="POST",
        data=payload,
        headers={
            "Authorization":
                f"Bearer {get_token()}",
            "Content-Type":
                "application/json",
        },
    )

    try:
        response = urllib.request.urlopen(
            request
        )

    except urllib.error.HTTPError as exc:
        body = exc.read().decode(
            "utf-8",
            errors="replace",
        )

        raise RuntimeError(
            f"Fabric deployment failed "
            f"HTTP {exc.code}\n{body}"
        ) from exc

    print(
        f"Fabric response: HTTP "
        f"{response.status}"
    )

    if response.status == 200:
        print(
            f"{args.pipeline} updated."
        )
        return

    if response.status != 202:
        raise RuntimeError(
            "Unexpected Fabric response: "
            f"{response.status}"
        )

    location = response.headers.get(
        "Location"
    )

    retry_after = int(
        response.headers.get(
            "Retry-After",
            "10",
        )
    )

    if not location:
        raise RuntimeError(
            "Fabric returned 202 without "
            "an operation Location."
        )

    print(
        "Definition update accepted."
    )

    while True:
        time.sleep(retry_after)

        poll_request = urllib.request.Request(
            location,
            headers={
                "Authorization":
                    f"Bearer {get_token()}",
            },
        )

        with urllib.request.urlopen(
            poll_request
        ) as poll_response:
            body = poll_response.read()

        result = (
            json.loads(
                body.decode("utf-8")
            )
            if body
            else {}
        )

        status = result.get(
            "status",
            "Unknown",
        )

        print(
            f"Deployment status: {status}"
        )

        if status == "Succeeded":
            print(
                f"{args.pipeline} updated."
            )
            return

        if status in {
            "Failed",
            "Cancelled",
            "Canceled",
        }:
            raise RuntimeError(
                json.dumps(
                    result,
                    indent=2,
                )
            )


if __name__ == "__main__":
    main()
