import json

from gm_skills.serving.snapshot_store import (
    REQUIRED_FILES,
    SnapshotStore,
)


class FakeDownload:
    def __init__(self, payload):
        self.payload = payload

    def readall(self):
        return self.payload


class FakeContainer:
    def __init__(self, blobs):
        self.blobs = blobs

    def download_blob(self, name):
        if name not in self.blobs:
            raise RuntimeError(
                f"Blob unavailable: {name}"
            )

        return FakeDownload(
            self.blobs[name]
        )


def encoded(value):
    return json.dumps(
        value,
        separators=(",", ":"),
    ).encode("utf-8")


def make_remote(snapshot_id="snapshot-1"):
    fingerprint = (
        f"fingerprint-{snapshot_id}"
    )

    data = {
        "borough-current.json": [
            {"borough_code": f"B{i}"}
            for i in range(10)
        ],
        "borough-kpis.json": [
            {
                "borough_code": f"B{i}",
                "kpi_code": f"K{j}",
            }
            for i in range(10)
            for j in range(12)
        ],
        "kpi-definitions.json": [
            {"kpi_code": f"K{i}"}
            for i in range(12)
        ],
        "skills-supply.json": [{"x": 1}],
        "mbacc-pathways.json": [{"x": 1}],
        "youth-transition.json": [{"x": 1}],
        "borough-opportunity.json": [{"x": 1}],
        "metadata.json": {
            "status": "valid",
            "snapshot_id": snapshot_id,
            "data_fingerprint": fingerprint,
        },
    }

    blobs = {}

    files = {}

    for filename in REQUIRED_FILES:
        payload = encoded(
            data[filename]
        )

        blob_name = (
            f"slot-a/{filename}"
        )

        blobs[blob_name] = payload

        files[filename] = {
            "blob": blob_name,
            "bytes": len(payload),
        }

    manifest = {
        "status": "valid",
        "active_slot": "slot-a",
        "snapshot_id": snapshot_id,
        "data_fingerprint": fingerprint,
        "source_exported_at_utc": (
            "2026-09-20T16:00:00+00:00"
        ),
        "published_at_utc": (
            "2026-09-20T16:30:00+00:00"
        ),
        "files": files,
    }

    blobs["manifest.json"] = encoded(
        manifest
    )

    return blobs


def test_loads_valid_remote_snapshot():
    container = FakeContainer(
        make_remote()
    )

    store = SnapshotStore(
        container_client=container
    )

    assert store.refresh() is True

    assert (
        store.status()["snapshot_id"]
        == "snapshot-1"
    )

    assert (
        store.status()["serving_status"]
        == "current"
    )

    assert len(
        store.dataset(
            "borough_current"
        )
    ) == 10


def test_unchanged_manifest_does_not_reload():
    container = FakeContainer(
        make_remote()
    )

    store = SnapshotStore(
        container_client=container
    )

    assert store.refresh() is True
    assert store.refresh() is False

    assert (
        store.status()["serving_status"]
        == "current"
    )


def test_failure_retains_last_known_good():
    container = FakeContainer(
        make_remote()
    )

    store = SnapshotStore(
        container_client=container
    )

    assert store.refresh() is True

    original_id = (
        store.status()["snapshot_id"]
    )

    del container.blobs[
        "manifest.json"
    ]

    assert store.refresh(
        force=True
    ) is False

    status = store.status()

    assert (
        status["snapshot_id"]
        == original_id
    )

    assert (
        status["serving_status"]
        == "last_known_good"
    )

    assert status["last_error"]


def test_broken_new_snapshot_does_not_replace_current():
    container = FakeContainer(
        make_remote("snapshot-1")
    )

    store = SnapshotStore(
        container_client=container
    )

    assert store.refresh() is True

    new_remote = make_remote(
        "snapshot-2"
    )

    container.blobs.update(
        new_remote
    )

    del container.blobs[
        "slot-a/borough-kpis.json"
    ]

    assert store.refresh(
        force=True
    ) is False

    assert (
        store.status()["snapshot_id"]
        == "snapshot-1"
    )

    assert (
        store.status()["serving_status"]
        == "last_known_good"
    )
