"""Validation workflow for SRC06 MBacc reference data."""

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
    check_expected_values,
    check_non_empty,
    check_required_columns,
)
from gm_skills.validation.models import (
    CheckStatus,
    ValidationResult,
)


def validate_src06(
    path: Path,
) -> tuple[pd.DataFrame, list[ValidationResult]]:
    """Validate the controlled MBacc gateway reference."""

    registry = load_source_registry()

    contract = load_source_contract(
        registry["SRC06"]
    )

    dataframe = pd.read_csv(
        path,
        dtype=str,
        keep_default_na=False,
    )

    results: list[ValidationResult] = []

    results.append(
        check_required_columns(
            dataframe,
            contract["expected_columns"],
        )
    )

    results.append(
        check_non_empty(dataframe)
    )

    results.append(
        check_business_key_nulls(
            dataframe,
            contract["business_key"],
        )
    )

    results.append(
        check_duplicate_business_keys(
            dataframe,
            contract["business_key"],
        )
    )

    results.append(
        check_expected_values(
            dataframe,
            "gateway_code",
            contract["expected_gateway_codes"],
        )
    )

    for column, accepted in contract[
        "accepted_values"
    ].items():
        results.append(
            check_accepted_values(
                dataframe,
                column,
                accepted,
            )
        )

    return dataframe, results


def validation_passed(
    results: list[ValidationResult],
) -> bool:
    """Return True when no MBacc checks failed."""

    return all(
        result.status != CheckStatus.FAIL
        for result in results
    )
