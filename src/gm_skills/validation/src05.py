"""Validation workflow for SRC05 ONS Nomis APS."""

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
    check_geography_coverage,
    check_non_empty,
    check_required_columns,
)
from gm_skills.validation.models import (
    CheckStatus,
    ValidationResult,
)


def _validate_file(
    dataframe: pd.DataFrame,
    contract: dict,
    expected_variables: list[str],
) -> list[ValidationResult]:
    """Validate one Nomis metric-family extract."""

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
        check_geography_coverage(
            dataframe,
            contract["geography_key"],
            contract["scope"]["geography_codes"],
        )
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
            "VARIABLE",
            expected_variables,
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

    return results


def validate_src05(
    labour_market_path: Path,
    qualifications_path: Path,
) -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    list[ValidationResult],
]:
    """Validate both Nomis APS metric families."""

    registry = load_source_registry()
    contract = load_source_contract(
        registry["SRC05"]
    )

    labour_market = pd.read_csv(
        labour_market_path,
        dtype=str,
        keep_default_na=False,
    )

    qualifications = pd.read_csv(
        qualifications_path,
        dtype=str,
        keep_default_na=False,
    )

    labour_results = _validate_file(
        labour_market,
        contract,
        contract["expected_variables"][
            "labour_market"
        ],
    )

    qualification_results = _validate_file(
        qualifications,
        contract,
        contract["expected_variables"][
            "qualifications"
        ],
    )

    results = (
        labour_results
        + qualification_results
    )

    return (
        labour_market,
        qualifications,
        results,
    )


def validation_passed(
    results: list[ValidationResult],
) -> bool:
    """Return True when no Nomis checks failed."""

    return all(
        result.status != CheckStatus.FAIL
        for result in results
    )
