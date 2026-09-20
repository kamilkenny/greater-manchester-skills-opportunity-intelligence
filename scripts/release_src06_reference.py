from __future__ import annotations

import csv
import hashlib
import os
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import requests


SOURCE_ID = "SRC06"
SOURCE_FILE = Path("config/reference/mbacc_gateways_reference.csv")


def get_token() -> str:
    return subprocess.check_output(
        [
            "az",
            "account",
            "get-access-token",
            "--resource",
            "https://storage.azure.com/",
            "--query",
            "accessToken",
            "-o",
            "tsv",
        ],
        text=True,
    ).strip()


def check_response(response: requests.Response, allowed: set[int], action: str) -> None:
    if response.status_code not in allowed:
        raise RuntimeError(
            f"{action} failed: HTTP {response.status_code}\n{response.text}"
        )


def main() -> None:
    workspace_id = os.environ["WORKSPACE_ID"]
    bronze_id = os.environ["BRONZE_ID"]

    if not SOURCE_FILE.exists():
        raise FileNotFoundError(f"Missing controlled reference: {SOURCE_FILE}")

    data = SOURCE_FILE.read_bytes()

    if not data:
        raise ValueError("SRC06 reference file is empty.")

    with SOURCE_FILE.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        rows = list(reader)

    if len(rows) < 2:
        raise ValueError("SRC06 does not contain a header and data rows.")

    header = rows[0]
    records = rows[1:]

    if len(records) != 7:
        raise ValueError(
            f"SRC06 expected 7 MBacc gateway records, found {len(records)}."
        )

    if any(not row or not row[0].strip() for row in records):
        raise ValueError("SRC06 contains a record with a blank primary identifier.")

    now = datetime.now(timezone.utc)
    run_id = str(uuid.uuid4())
    sha256 = hashlib.sha256(data).hexdigest()

    root = "Files/raw/reference/SRC06"

    partition_parts = [
        f"year={now:%Y}",
        f"month={now:%m}",
        f"day={now:%d}",
        f"run_id={run_id}",
    ]

    base_url = (
        f"https://onelake.dfs.fabric.microsoft.com/"
        f"{workspace_id}/{bronze_id}"
    )

    token = get_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "x-ms-version": "2021-06-08",
    }

    current = root

    for part in partition_parts:
        current = f"{current}/{part}"
        directory_url = (
            f"{base_url}/{quote(current, safe='/=')}?resource=directory"
        )

        response = requests.put(directory_url, headers=headers, timeout=60)

        # 201 = created, 409 = already exists
        check_response(
            response,
            {200, 201, 409},
            f"Create directory {current}",
        )

    destination = f"{current}/source.csv"
    file_url = f"{base_url}/{quote(destination, safe='/=')}"

    # Create empty file
    response = requests.put(
        f"{file_url}?resource=file",
        headers=headers,
        timeout=60,
    )
    check_response(response, {200, 201}, "Create SRC06 file")

    # Append contents
    response = requests.patch(
        f"{file_url}?action=append&position=0",
        headers={
            **headers,
            "Content-Type": "application/octet-stream",
        },
        data=data,
        timeout=60,
    )
    check_response(response, {200, 202}, "Append SRC06 contents")

    # Commit the uploaded bytes
    response = requests.patch(
        f"{file_url}?action=flush&position={len(data)}",
        headers=headers,
        timeout=60,
    )
    check_response(response, {200, 201}, "Flush SRC06 file")

    print("=== SRC06 RELEASE COMPLETE ===")
    print(f"source_id:     {SOURCE_ID}")
    print(f"rows:          {len(records)}")
    print(f"columns:       {len(header)}")
    print(f"bytes:         {len(data)}")
    print(f"sha256:        {sha256}")
    print(f"run_id:        {run_id}")
    print(f"destination:   {destination}")


if __name__ == "__main__":
    main()
