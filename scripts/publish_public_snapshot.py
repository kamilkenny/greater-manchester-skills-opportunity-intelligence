import argparse
import json
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SNAPSHOT = ROOT / "data" / "public" / "build"

REQUIRED_FILES = (
    "borough-current.json",
    "borough-kpis.json",
    "kpi-definitions.json",
    "skills-supply.json",
    "mbacc-pathways.json",
    "youth-transition.json",
    "borough-opportunity.json",
    "metadata.json",
)


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Publish a validated GM SkillsFlow snapshot "
            "to bounded two-slot Azure Blob storage."
        )
    )

    parser.add_argument(
        "--account",
        required=True,
        help="Azure Storage account name.",
    )

    parser.add_argument(
        "--container",
        default="public-serving",
        help="Azure Blob container name.",
    )

    parser.add_argument(
        "--snapshot-dir",
        type=Path,
        default=DEFAULT_SNAPSHOT,
        help="Validated local snapshot directory.",
    )

    return parser.parse_args()


def run_az(*args, capture=True):
    command = ["az", *args]

    result = subprocess.run(
        command,
        check=True,
        text=True,
        capture_output=capture,
    )

    if capture:
        return result.stdout.strip()

    return ""


def blob_exists(account, container, name):
    result = run_az(
        "storage",
        "blob",
        "exists",
        "--account-name",
        account,
        "--container-name",
        container,
        "--name",
        name,
        "--auth-mode",
        "login",
        "--query",
        "exists",
        "-o",
        "tsv",
    )

    return result.lower() == "true"


def download_json(account, container, name):
    with tempfile.NamedTemporaryFile(
        suffix=".json",
        delete=False,
    ) as handle:
        target = Path(handle.name)

    try:
        run_az(
            "storage",
            "blob",
            "download",
            "--account-name",
            account,
            "--container-name",
            container,
            "--name",
            name,
            "--file",
            str(target),
            "--auth-mode",
            "login",
            "--overwrite",
            "true",
            "--only-show-errors",
            "--output",
            "none",
            capture=False,
        )

        return json.loads(
            target.read_text(
                encoding="utf-8"
            )
        )

    finally:
        target.unlink(
            missing_ok=True
        )


def list_prefix(account, container, prefix):
    output = run_az(
        "storage",
        "blob",
        "list",
        "--account-name",
        account,
        "--container-name",
        container,
        "--prefix",
        prefix,
        "--auth-mode",
        "login",
        "--query",
        "[].name",
        "-o",
        "tsv",
    )

    if not output:
        return []

    return output.splitlines()


def delete_blob(account, container, name):
    run_az(
        "storage",
        "blob",
        "delete",
        "--account-name",
        account,
        "--container-name",
        container,
        "--name",
        name,
        "--auth-mode",
        "login",
        "--only-show-errors",
        "--output",
        "none",
        capture=False,
    )


def upload_blob(
    account,
    container,
    name,
    source,
):
    run_az(
        "storage",
        "blob",
        "upload",
        "--account-name",
        account,
        "--container-name",
        container,
        "--name",
        name,
        "--file",
        str(source),
        "--auth-mode",
        "login",
        "--overwrite",
        "true",
        "--content-type",
        "application/json",
        "--only-show-errors",
        "--output",
        "none",
        capture=False,
    )


def remote_size(
    account,
    container,
    name,
):
    value = run_az(
        "storage",
        "blob",
        "show",
        "--account-name",
        account,
        "--container-name",
        container,
        "--name",
        name,
        "--auth-mode",
        "login",
        "--query",
        "properties.contentLength",
        "-o",
        "tsv",
    )

    return int(value)


def validate_local_snapshot(snapshot):
    if not snapshot.is_dir():
        raise RuntimeError(
            f"Snapshot directory not found: {snapshot}"
        )

    missing = [
        filename
        for filename in REQUIRED_FILES
        if not (
            snapshot
            / filename
        ).is_file()
    ]

    if missing:
        raise RuntimeError(
            "Snapshot is incomplete. Missing: "
            + ", ".join(missing)
        )

    metadata = json.loads(
        (
            snapshot
            / "metadata.json"
        ).read_text(
            encoding="utf-8"
        )
    )

    if metadata.get("status") != "valid":
        raise RuntimeError(
            "Snapshot metadata status "
            "is not valid."
        )

    if not metadata.get(
        "data_fingerprint"
    ):
        raise RuntimeError(
            "Snapshot has no data fingerprint."
        )

    return metadata


def main():
    args = parse_args()

    snapshot = (
        args.snapshot_dir
        .expanduser()
        .resolve()
    )

    metadata = (
        validate_local_snapshot(
            snapshot
        )
    )

    fingerprint = metadata[
        "data_fingerprint"
    ]

    manifest_name = "manifest.json"

    current_manifest = None

    if blob_exists(
        args.account,
        args.container,
        manifest_name,
    ):
        current_manifest = (
            download_json(
                args.account,
                args.container,
                manifest_name,
            )
        )

    if (
        current_manifest
        and current_manifest.get(
            "data_fingerprint"
        )
        == fingerprint
    ):
        print(
            "GM SkillsFlow publication: "
            "NO_CHANGE"
        )
        print(
            "Active slot: "
            f"{current_manifest['active_slot']}"
        )
        print(
            "Snapshot ID: "
            f"{current_manifest['snapshot_id']}"
        )
        print(
            "No blobs were uploaded."
        )
        return

    if current_manifest:
        active_slot = (
            current_manifest.get(
                "active_slot"
            )
        )

        if active_slot not in (
            "slot-a",
            "slot-b",
        ):
            raise RuntimeError(
                "Remote manifest has an "
                "invalid active slot."
            )

        target_slot = (
            "slot-b"
            if active_slot == "slot-a"
            else "slot-a"
        )

    else:
        target_slot = "slot-a"

    print(
        "GM SkillsFlow publication"
    )

    print(
        f"Target slot: {target_slot}"
    )

    existing = list_prefix(
        args.account,
        args.container,
        f"{target_slot}/",
    )

    for blob_name in existing:
        delete_blob(
            args.account,
            args.container,
            blob_name,
        )

    print(
        f"Cleared {len(existing)} "
        f"old blob(s) from {target_slot}."
    )

    file_manifest = {}

    for filename in REQUIRED_FILES:
        source = (
            snapshot
            / filename
        )

        blob_name = (
            f"{target_slot}/"
            f"{filename}"
        )

        upload_blob(
            args.account,
            args.container,
            blob_name,
            source,
        )

        expected_size = (
            source.stat().st_size
        )

        actual_size = remote_size(
            args.account,
            args.container,
            blob_name,
        )

        if expected_size != actual_size:
            raise RuntimeError(
                f"Remote verification "
                f"failed for {filename}: "
                f"expected {expected_size}, "
                f"got {actual_size}."
            )

        file_manifest[
            filename
        ] = {
            "blob": blob_name,
            "bytes": expected_size,
        }

        print(
            f"PASS {filename:<30} "
            f"{expected_size:>9,} bytes"
        )

    manifest = {
        "product": "GM SkillsFlow",
        "schema_version": 1,
        "status": "valid",
        "active_slot": target_slot,
        "snapshot_id": metadata[
            "snapshot_id"
        ],
        "data_fingerprint": fingerprint,
        "source_exported_at_utc": (
            metadata[
                "exported_at_utc"
            ]
        ),
        "published_at_utc": (
            datetime.now(
                UTC
            ).isoformat()
        ),
        "files": file_manifest,
    }

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".json",
        encoding="utf-8",
        delete=False,
    ) as handle:
        json.dump(
            manifest,
            handle,
            ensure_ascii=False,
            separators=(",", ":"),
        )

        handle.write("\n")

        manifest_path = Path(
            handle.name
        )

    try:
        # Manifest is deliberately uploaded LAST.
        # It is the commit pointer for readers.
        upload_blob(
            args.account,
            args.container,
            manifest_name,
            manifest_path,
        )

    finally:
        manifest_path.unlink(
            missing_ok=True
        )

    print()
    print(
        "PUBLICATION COMPLETE"
    )
    print(
        f"Active slot: {target_slot}"
    )
    print(
        "Snapshot ID: "
        f"{metadata['snapshot_id']}"
    )
    print(
        "Manifest switched only after "
        "all snapshot files passed "
        "remote size verification."
    )


if __name__ == "__main__":
    main()
