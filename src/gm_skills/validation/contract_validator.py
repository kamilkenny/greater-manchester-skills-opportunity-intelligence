"""Contract-driven CSV validation for GM SkillsFlow."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from gm_skills.ingestion.source_registry import (
    load_source_contract,
    load_source_registry,
)
from gm_skills.validation.checks import (
    check_accepted_values,
    check_business_key_nulls,
    check_duplicate_business_keys,
    check_geography_coverage,
    check_non_empty,
    check_required_columns,
    check_special_values,
)
from gm_skills.validation.models import (
    CheckStatus,
    ValidationResult,
)


def _scope_dataframe(
    dataframe: pd.DataFrame,
    contract: dict,
) -> pd.DataFrame:
    """Apply optional geography and level scope from a contract."""

    scope = contract.get("scope")

    if not isinstance(scope, dict):
        return dataframe.copy()

    scoped = dataframe.copy()

    geography_codes = scope.get(
        "geography_codes"
    )

    geography_key = contract.get(
        "geography_key"
    )

    if geography_codes and geography_key:
        scoped = scoped[
            scoped[geography_key].isin(
                geography_codes
            )
        ]

    geographic_level = scope.get(
        "geographic_level"
    )

    if geographic_level:
        scoped = scoped[
            scoped["geographic_level"]
            == geographic_level
        ]

    return scoped.copy()


def validate_csv_source(
    source_id: str,
    path: Path,
) -> tuple[pd.DataFrame, list[ValidationResult]]:
    """Validate one CSV source using its source contract."""

    registry = load_source_registry()

    if source_id not in registry:
        raise KeyError(
            f"Unknown source_id: {source_id}"
        )

    source = registry[source_id]
    contract = load_source_contract(
        source
    )

    if source.file_format != "csv":
        raise ValueError(
            f"{source_id} is not configured as CSV"
        )

    dataframe = pd.read_csv(
        path,
        dtype=str,
        keep_default_na=False,
    )

    results: list[ValidationResult] = []

    required_columns = check_required_columns(
        dataframe,
        contract["expected_columns"],
    )

    results.append(
        required_columns
    )

    results.append(
        check_non_empty(
            dataframe
        )
    )

    if required_columns.status == CheckStatus.FAIL:
        return dataframe, results

    scoped = _scope_dataframe(
        dataframe,
        contract,
    )

    results.append(
        check_non_empty(
            scoped
        )
    )

    geography_codes = contract.get(
        "scope",
        {},
    ).get(
        "geography_codes"
    )

    geography_key = contract.get(
        "geography_key"
    )

    if geography_codes and geography_key:
        results.append(
            check_geography_coverage(
                scoped,
                geography_key,
                geography_codes,
            )
        )

    business_key = contract.get(
        "business_key"
    )

    if business_key:
        results.append(
            check_business_key_nulls(
                scoped,
                business_key,
            )
        )

        results.append(
            check_duplicate_business_keys(
                scoped,
                business_key,
            )
        )

    accepted_values = contract.get(
        "accepted_values",
        {},
    )

    for column, accepted in accepted_values.items():
        results.append(
            check_accepted_values(
                scoped,
                column,
                accepted,
            )
        )

    special_values = contract.get(
        "expected_special_values",
        {},
    )

    for column, allowed in special_values.items():
        results.append(
            check_special_values(
                scoped,
                column,
                allowed,
            )
        )

    return scoped, results


def validation_passed(
    results: list[ValidationResult],
) -> bool:
    """Return True when no contract checks failed."""

    return all(
        result.status != CheckStatus.FAIL
        for result in results
    )
