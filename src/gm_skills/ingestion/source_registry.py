"""Metadata-driven source registry for GM SkillsFlow."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from gm_skills.settings import settings

DEFAULT_REGISTRY = settings.project_root / "config" / "sources.yaml"


@dataclass(frozen=True)
class SourceDefinition:
    """Configuration for one source system."""

    source_id: str
    source_name: str
    provider: str
    source_type: str
    endpoint: str
    file_format: str
    refresh_frequency: str
    enabled: bool
    bronze_path: str
    contract_path: Path
    period_strategy: str


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open(
        "r",
        encoding="utf-8",
    ) as handle:
        data = yaml.safe_load(handle)

    if not isinstance(data, dict):
        raise ValueError(
            f"Expected YAML mapping in {path}"
        )

    return data


def load_source_registry(
    path: Path = DEFAULT_REGISTRY,
) -> dict[str, SourceDefinition]:
    """Load and validate the configured data-source registry."""

    data = _load_yaml(path)

    if data.get("version") != 1:
        raise ValueError(
            "Unsupported source registry version"
        )

    configured_sources = data.get("sources")

    if not isinstance(
        configured_sources,
        list,
    ):
        raise ValueError(
            "Registry 'sources' must be a list"
        )

    registry: dict[str, SourceDefinition] = {}

    for item in configured_sources:
        if not isinstance(item, dict):
            raise ValueError(
                "Each source definition must be a mapping"
            )

        source_id = str(
            item["source_id"]
        ).strip()

        if source_id in registry:
            raise ValueError(
                f"Duplicate source_id: {source_id}"
            )

        contract_path = (
            settings.project_root
            / str(item["contract"])
        )

        if not contract_path.exists():
            raise FileNotFoundError(
                f"Missing contract for {source_id}: "
                f"{contract_path}"
            )

        registry[source_id] = SourceDefinition(
            source_id=source_id,
            source_name=str(item["source_name"]),
            provider=str(item["provider"]),
            source_type=str(item["source_type"]),
            endpoint=str(item["endpoint"]),
            file_format=str(item["file_format"]),
            refresh_frequency=str(
                item["refresh_frequency"]
            ),
            enabled=bool(item["enabled"]),
            bronze_path=str(item["bronze_path"]),
            contract_path=contract_path,
            period_strategy=str(
                item["period_strategy"]
            ),
        )

    return registry


def load_source_contract(
    source: SourceDefinition,
) -> dict[str, Any]:
    """Load a source contract and verify its source identifier."""

    contract = _load_yaml(
        source.contract_path
    )

    contract_source_id = str(
        contract.get("source_id", "")
    )

    if contract_source_id != source.source_id:
        raise ValueError(
            f"Contract source_id mismatch for "
            f"{source.source_id}"
        )

    expected_columns = contract.get(
        "expected_columns"
    )

    if not isinstance(
        expected_columns,
        list,
    ) or not expected_columns:
        raise ValueError(
            f"Contract for {source.source_id} "
            "must define expected_columns"
        )

    return contract
