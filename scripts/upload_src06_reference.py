from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import UTC, datetime
from pathlib import Path

ONELAKE = "https://onelake.dfs.fabric.microsoft.com"
API_VERSION = "2023-11-03"


def storage_token() -> str:
    result = subprocess.run(
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
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def git_commit() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def request(
    url: str,
    method: str,
    token: str,
    data: bytes = b"",
    content_type: str | None = None,
) -> int:
    headers = {
        "Authorization": f"Bearer {token}",
        "x-ms-version": API_VERSION,
    }

    if content_type:
        headers["Content-Type"] = content_type

    req = urllib.request.Request(
        url,
        method=method,
        data=data,
        headers=headers,
    )

    try:
        with urllib.request.urlopen(req) as response:
            return response.status
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"OneLake request failed\n"
            f"HTTP {exc.code}\n"
            f"{method} {url}\n"
            f"{body}"
        ) from exc


def upload_file(
    *,
    workspace_id: str,
    lakehouse_id: str,
    relative_path: str,
    content: bytes,
    token: str,
) -> None:
    encoded_path = urllib.parse.quote(
        f"{lakehouse_id}/{relative_path}",
        safe="/=",
    )

    base_url = f"{ONELAKE}/{workspace_id}/{encoded_path}"

    create_status = request(
        f"{base_url}?resource=file",
        "PUT",
        token,
    )

    append_status = request(
        f"{base_url}?action=append&position=0",
        "PATCH",
        token,
        data=content,
        content_type="application/octet-stream",
    )

    flush_status = request(
        f"{base_url}?action=flush&position={len(content)}",
        "PATCH",
        token,
    )

    print(
        f"Uploaded {relative_path} "
        f"[create={create_status}, "
        f"append={append_status}, "
        f"flush={flush_status}]"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace-id", required=True)
    parser.add_argument("--lakehouse-id", required=True)
    parser.add_argument("--source-file", required=True)
    args = parser.parse_args()

    source = Path(args.source_file)

    if not source.exists():
        raise FileNotFoundError(source)

    content = source.read_bytes()
    checksum = hashlib.sha256(content).hexdigest()

    now = datetime.now(UTC)
    run_id = str(uuid.uuid4())

    run_folder = (
        "Files/raw/reference/SRC06/"
        f"year={now:%Y}/"
        f"month={now:%m}/"
        f"day={now:%d}/"
        f"run_id={run_id}"
    )

    token = storage_token()

    upload_file(
        workspace_id=args.workspace_id,
        lakehouse_id=args.lakehouse_id,
        relative_path=f"{run_folder}/source.csv",
        content=content,
        token=token,
    )

    metadata = {
        "source_id": "SRC06",
        "source_type": "controlled_reference",
        "source_file": str(source),
        "run_id": run_id,
        "ingested_at_utc": now.isoformat(),
        "sha256": checksum,
        "byte_count": len(content),
        "git_commit": git_commit(),
    }

    metadata_content = (
        json.dumps(metadata, indent=2) + "\n"
    ).encode("utf-8")

    upload_file(
        workspace_id=args.workspace_id,
        lakehouse_id=args.lakehouse_id,
        relative_path=f"{run_folder}/metadata.json",
        content=metadata_content,
        token=token,
    )

    print()
    print("SRC06 ingestion complete")
    print(f"Run ID:       {run_id}")
    print(f"Bytes:        {len(content)}")
    print(f"SHA256:       {checksum}")
    print(f"Bronze path:  {run_folder}")


if __name__ == "__main__":
    main()
