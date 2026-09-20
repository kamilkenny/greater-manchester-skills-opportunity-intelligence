from __future__ import annotations

import base64
import json
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

WORKSPACE_ID = "81e75ca0-f556-48c0-9dea-4851ce7bf916"
FABRIC_API = "https://api.fabric.microsoft.com/v1"

EXPORT_TYPES = {
    "DataPipeline",
    "Notebook",
}

OUT_ROOT = Path("fabric/items")


def get_token() -> str:
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


TOKEN = get_token()


def request_json(url: str, method: str = "GET"):
    request = urllib.request.Request(
        url,
        data=b"" if method == "POST" else None,
        method=method,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(request) as response:
            status = response.status
            headers = dict(response.headers)
            payload = response.read()

            body = json.loads(payload.decode("utf-8")) if payload else None
            return status, headers, body

    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Fabric API failed: HTTP {exc.code}\n"
            f"URL: {url}\n"
            f"{body}"
        ) from exc


def get_definition(item_id: str):
    url = (
        f"{FABRIC_API}/workspaces/{WORKSPACE_ID}"
        f"/items/{item_id}/getDefinition"
    )

    status, headers, body = request_json(url, "POST")

    if status == 200:
        return body

    if status != 202:
        raise RuntimeError(f"Unexpected HTTP status: {status}")

    operation_id = (
        headers.get("x-ms-operation-id")
        or headers.get("X-MS-OPERATION-ID")
    )

    if not operation_id:
        raise RuntimeError("Fabric returned 202 but no operation ID.")

    state_url = f"{FABRIC_API}/operations/{operation_id}"
    result_url = f"{FABRIC_API}/operations/{operation_id}/result"

    while True:
        time.sleep(3)

        _, _, state = request_json(state_url)

        operation_status = state.get("status")

        if operation_status == "Succeeded":
            break

        if operation_status == "Failed":
            raise RuntimeError(
                f"Fabric operation failed:\n"
                f"{json.dumps(state, indent=2)}"
            )

        print(
            f"    waiting for Fabric operation "
            f"{operation_id}: {operation_status}"
        )

    _, _, result = request_json(result_url)

    return result


print("Reading Fabric workspace...")
_, _, response = request_json(
    f"{FABRIC_API}/workspaces/{WORKSPACE_ID}/items"
)

items = response.get("value", [])

manifest = []

for item in items:
    item_type = item.get("type")
    name = item.get("displayName")
    item_id = item.get("id")

    manifest.append(
        {
            "displayName": name,
            "type": item_type,
            "id": item_id,
        }
    )

    if item_type not in EXPORT_TYPES:
        continue

    print(f"\nExporting {item_type}: {name}")

    definition = get_definition(item_id)

    item_dir = OUT_ROOT / name
    item_dir.mkdir(parents=True, exist_ok=True)

    definition_obj = definition.get("definition", definition)
    parts = definition_obj.get("parts", [])

    for part in parts:
        relative_path = Path(part["path"])
        target = item_dir / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)

        payload = part["payload"]
        payload_type = part.get("payloadType")

        if payload_type == "InlineBase64":
            content = base64.b64decode(payload)
            target.write_bytes(content)
        else:
            target.write_text(payload, encoding="utf-8")

        print(f"    saved {target}")

OUT_ROOT.mkdir(parents=True, exist_ok=True)

Path("fabric/manifest.json").write_text(
    json.dumps(
        {
            "workspaceId": WORKSPACE_ID,
            "items": manifest,
        },
        indent=2,
    )
    + "\n",
    encoding="utf-8",
)

print("\nExport complete.")
print(f"Workspace items discovered: {len(items)}")
