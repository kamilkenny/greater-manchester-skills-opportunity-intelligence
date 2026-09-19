"""Validation workflow for SRC02 detailed apprenticeships."""

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


def validate_src02(
    path: Path,
) -> tuple[pd.DataFrame, list[ValidationResult]]:
    """Validate the detailed apprenticeship source for Greater Manchester."""

    registry = load_source_registry()
    source = registry["SRC02"]
    contract = load_source_contract(source)

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
        check_non_empty(
            dataframe
        )
    )

    scope = contract["scope"]

    scoped = dataframe[
        (
            dataframe["geographic_level"]
            == scope["geographic_level"]
        )
        & (
            dataframe["lad_code"].isin(
                scope["geography_codes"]
            )
        )
    ].copy()

    results.append(
        check_non_empty(
            scoped
        )
    )

    results.append(
        check_geography_coverage(
            scoped,
            "lad_code",
            scope["geography_codes"],
        )
    )

    results.append(
        check_business_key_nulls(
            scoped,
            contract["business_key"],
        )
    )

    results.append(
        check_duplicate_business_keys(
            scoped,
            contract["business_key"],
        )
    )

    for column, accepted in contract[
        "accepted_values"
    ].items():
        results.append(
            check_accepted_values(
                scoped,
                column,
                accepted,
            )
        )

    for column, special_values in contract[
        "expected_special_values"
    ].items():
        results.append(
            check_special_values(
                scoped,
                column,
                special_values,
            )
        )

    return scoped, results


def validation_passed(
    results: list[ValidationResult],
) -> bool:
    """Return whether no validation checks failed."""

    return all(
        result.status != CheckStatus.FAIL
        for result in results
    )
