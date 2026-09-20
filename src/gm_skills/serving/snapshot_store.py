import json
import os
import threading
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from azure.identity import (
    AzureCliCredential,
    ManagedIdentityCredential,
)
from azure.storage.blob import (
    BlobServiceClient,
    ContainerClient,
)

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

DATASET_KEYS = {
    "borough-current.json": "borough_current",
    "borough-kpis.json": "borough_kpis",
    "kpi-definitions.json": "kpi_definitions",
    "skills-supply.json": "skills_supply",
    "mbacc-pathways.json": "mbacc_pathways",
    "youth-transition.json": "youth_transition",
    "borough-opportunity.json": "borough_opportunity",
    "metadata.json": "metadata",
}


@dataclass(frozen=True)
class SnapshotBundle:
    snapshot_id: str
    data_fingerprint: str
    active_slot: str
    source_exported_at_utc: str
    published_at_utc: str
    datasets: dict[str, Any]


class SnapshotStore:
    def __init__(
        self,
        account_name: str | None = None,
        container_name: str = "public-serving",
        *,
        container_client: ContainerClient | None = None,
        bootstrap_dir: Path | None = None,
    ) -> None:
        self._lock = threading.RLock()

        self._bundle: SnapshotBundle | None = None

        self._last_checked_at: str | None = None
        self._last_successful_refresh_at: str | None = None
        self._last_error: str | None = None

        self._bootstrap_dir = bootstrap_dir

        if container_client is not None:
            self._container = container_client
            return

        if not account_name:
            raise ValueError(
                "account_name is required when "
                "container_client is not supplied."
            )

        credential = self._credential()

        service = BlobServiceClient(
            account_url=(
                f"https://{account_name}."
                "blob.core.windows.net"
            ),
            credential=credential,
        )

        self._container = (
            service.get_container_client(
                container_name
            )
        )

    @classmethod
    def from_environment(
        cls,
    ) -> "SnapshotStore":
        account_name = os.environ.get(
            "GM_SKILLS_STORAGE_ACCOUNT"
        )

        if not account_name:
            raise RuntimeError(
                "GM_SKILLS_STORAGE_ACCOUNT "
                "is required."
            )

        container_name = os.environ.get(
            "GM_SKILLS_STORAGE_CONTAINER",
            "public-serving",
        )

        bootstrap_value = os.environ.get(
            "GM_SKILLS_BOOTSTRAP_DIR"
        )

        bootstrap_dir = (
            Path(bootstrap_value)
            if bootstrap_value
            else None
        )

        return cls(
            account_name=account_name,
            container_name=container_name,
            bootstrap_dir=bootstrap_dir,
        )

    @staticmethod
    def _credential():
        # App Service exposes WEBSITE_INSTANCE_ID.
        # Local Cloud Shell development uses the
        # authenticated Azure CLI session instead.
        if os.environ.get(
            "WEBSITE_INSTANCE_ID"
        ):
            client_id = os.environ.get(
                "AZURE_CLIENT_ID"
            )

            return ManagedIdentityCredential(
                client_id=client_id
            )

        return AzureCliCredential()

    @staticmethod
    def _now() -> str:
        return datetime.now(
            UTC
        ).isoformat()

    def _download_bytes(
        self,
        blob_name: str,
    ) -> bytes:
        return (
            self._container
            .download_blob(blob_name)
            .readall()
        )

    def _download_json(
        self,
        blob_name: str,
    ):
        payload = self._download_bytes(
            blob_name
        )

        return json.loads(
            payload.decode("utf-8")
        )

    @staticmethod
    def _validate_manifest(
        manifest: dict,
    ) -> None:
        if manifest.get("status") != "valid":
            raise RuntimeError(
                "Remote manifest status "
                "is not valid."
            )

        if manifest.get(
            "active_slot"
        ) not in (
            "slot-a",
            "slot-b",
        ):
            raise RuntimeError(
                "Remote manifest contains "
                "an invalid active slot."
            )

        if not manifest.get(
            "snapshot_id"
        ):
            raise RuntimeError(
                "Remote manifest has no "
                "snapshot ID."
            )

        if not manifest.get(
            "data_fingerprint"
        ):
            raise RuntimeError(
                "Remote manifest has no "
                "data fingerprint."
            )

        files = manifest.get(
            "files"
        )

        if not isinstance(
            files,
            dict,
        ):
            raise RuntimeError(
                "Remote manifest has no "
                "file catalogue."
            )

        missing = [
            filename
            for filename in REQUIRED_FILES
            if filename not in files
        ]

        if missing:
            raise RuntimeError(
                "Remote manifest is missing: "
                + ", ".join(missing)
            )

    @staticmethod
    def _validate_bundle(
        manifest: dict,
        datasets: dict[str, Any],
    ) -> None:
        metadata = datasets[
            "metadata"
        ]

        if metadata.get(
            "status"
        ) != "valid":
            raise RuntimeError(
                "Snapshot metadata status "
                "is not valid."
            )

        if (
            metadata.get(
                "snapshot_id"
            )
            != manifest.get(
                "snapshot_id"
            )
        ):
            raise RuntimeError(
                "Snapshot ID does not match "
                "the active manifest."
            )

        if (
            metadata.get(
                "data_fingerprint"
            )
            != manifest.get(
                "data_fingerprint"
            )
        ):
            raise RuntimeError(
                "Snapshot fingerprint does "
                "not match the manifest."
            )

        if len(
            datasets[
                "borough_current"
            ]
        ) != 10:
            raise RuntimeError(
                "Current borough snapshot "
                "must contain 10 rows."
            )

        if len(
            datasets[
                "borough_kpis"
            ]
        ) != 120:
            raise RuntimeError(
                "Current KPI layer must "
                "contain 120 rows."
            )

        if len(
            datasets[
                "kpi_definitions"
            ]
        ) != 12:
            raise RuntimeError(
                "KPI definition layer must "
                "contain 12 rows."
            )

    def _load_remote_bundle(
        self,
        manifest: dict,
    ) -> SnapshotBundle:
        files = manifest["files"]

        datasets = {}

        for filename in REQUIRED_FILES:
            spec = files[filename]

            blob_name = spec["blob"]

            expected_prefix = (
                manifest["active_slot"]
                + "/"
            )

            if not blob_name.startswith(
                expected_prefix
            ):
                raise RuntimeError(
                    f"{filename} points outside "
                    "the active slot."
                )

            raw = self._download_bytes(
                blob_name
            )

            expected_size = int(
                spec["bytes"]
            )

            if len(raw) != expected_size:
                raise RuntimeError(
                    f"{filename} remote size "
                    "does not match manifest."
                )

            datasets[
                DATASET_KEYS[filename]
            ] = json.loads(
                raw.decode("utf-8")
            )

        self._validate_bundle(
            manifest,
            datasets,
        )

        return SnapshotBundle(
            snapshot_id=manifest[
                "snapshot_id"
            ],
            data_fingerprint=manifest[
                "data_fingerprint"
            ],
            active_slot=manifest[
                "active_slot"
            ],
            source_exported_at_utc=(
                manifest[
                    "source_exported_at_utc"
                ]
            ),
            published_at_utc=manifest[
                "published_at_utc"
            ],
            datasets=datasets,
        )

    def _load_bootstrap(
        self,
    ) -> SnapshotBundle | None:
        if self._bootstrap_dir is None:
            return None

        root = self._bootstrap_dir

        if not root.is_dir():
            return None

        metadata_path = (
            root
            / "metadata.json"
        )

        if not metadata_path.is_file():
            return None

        metadata = json.loads(
            metadata_path.read_text(
                encoding="utf-8"
            )
        )

        datasets = {}

        for filename in REQUIRED_FILES:
            path = root / filename

            if not path.is_file():
                return None

            datasets[
                DATASET_KEYS[filename]
            ] = json.loads(
                path.read_text(
                    encoding="utf-8"
                )
            )

        manifest = {
            "status": "valid",
            "active_slot": "bootstrap",
            "snapshot_id": metadata[
                "snapshot_id"
            ],
            "data_fingerprint": metadata[
                "data_fingerprint"
            ],
        }

        if len(
            datasets["borough_current"]
        ) != 10:
            return None

        if len(
            datasets["borough_kpis"]
        ) != 120:
            return None

        return SnapshotBundle(
            snapshot_id=metadata[
                "snapshot_id"
            ],
            data_fingerprint=metadata[
                "data_fingerprint"
            ],
            active_slot="bootstrap",
            source_exported_at_utc=(
                metadata[
                    "exported_at_utc"
                ]
            ),
            published_at_utc=(
                metadata[
                    "exported_at_utc"
                ]
            ),
            datasets=datasets,
        )

    def refresh(
        self,
        *,
        force: bool = False,
    ) -> bool:
        checked_at = self._now()

        try:
            manifest = self._download_json(
                "manifest.json"
            )

            self._validate_manifest(
                manifest
            )

            with self._lock:
                current = self._bundle

            if (
                not force
                and current is not None
                and current.snapshot_id
                == manifest["snapshot_id"]
            ):
                with self._lock:
                    self._last_checked_at = (
                        checked_at
                    )
                    self._last_error = None

                return False

            candidate = (
                self._load_remote_bundle(
                    manifest
                )
            )

            with self._lock:
                self._bundle = candidate

                self._last_checked_at = (
                    checked_at
                )

                self._last_successful_refresh_at = (
                    self._now()
                )

                self._last_error = None

            return True

        except Exception as exc:
            with self._lock:
                self._last_checked_at = (
                    checked_at
                )

                self._last_error = (
                    f"{type(exc).__name__}: "
                    f"{exc}"
                )

                current = self._bundle

            if current is not None:
                # Last-known-good protection.
                return False

            bootstrap = (
                self._load_bootstrap()
            )

            if bootstrap is not None:
                with self._lock:
                    self._bundle = bootstrap

                    self._last_successful_refresh_at = (
                        self._now()
                    )

                return True

            raise

    def get_bundle(
        self,
    ) -> SnapshotBundle:
        with self._lock:
            bundle = self._bundle

        if bundle is None:
            self.refresh()

            with self._lock:
                bundle = self._bundle

        if bundle is None:
            raise RuntimeError(
                "No validated snapshot "
                "is available."
            )

        return bundle

    def dataset(
        self,
        name: str,
    ):
        bundle = self.get_bundle()

        if name not in bundle.datasets:
            raise KeyError(
                f"Unknown dataset: {name}"
            )

        return bundle.datasets[name]

    def status(self) -> dict[str, Any]:
        with self._lock:
            bundle = self._bundle

            if bundle is None:
                serving_status = (
                    "uninitialised"
                )
            elif self._last_error:
                serving_status = (
                    "last_known_good"
                )
            elif (
                bundle.active_slot
                == "bootstrap"
            ):
                serving_status = (
                    "bootstrap"
                )
            else:
                serving_status = (
                    "current"
                )

            return {
                "serving_status": (
                    serving_status
                ),
                "snapshot_id": (
                    bundle.snapshot_id
                    if bundle
                    else None
                ),
                "active_slot": (
                    bundle.active_slot
                    if bundle
                    else None
                ),
                "published_at_utc": (
                    bundle.published_at_utc
                    if bundle
                    else None
                ),
                "source_exported_at_utc": (
                    bundle.source_exported_at_utc
                    if bundle
                    else None
                ),
                "last_checked_at": (
                    self._last_checked_at
                ),
                "last_successful_refresh_at": (
                    self._last_successful_refresh_at
                ),
                "last_error": (
                    self._last_error
                ),
            }
