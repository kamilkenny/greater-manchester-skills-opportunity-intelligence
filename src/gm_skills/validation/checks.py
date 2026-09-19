"""Reusable data-quality checks for GM SkillsFlow."""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd

from gm_skills.validation.models import (
    CheckStatus,
    ValidationResult,
)


def check_required_columns(
    dataframe: pd.DataFrame,
    expected_columns: Iterable[str],
) -> ValidationResult:
    """Check that all contract columns exist."""

    expected = set(expected_columns)
    actual = set(dataframe.columns)

    missing = sorted(
        expected - actual
    )

    if missing:
        return ValidationResult(
            check_name="required_columns",
            status=CheckStatus.FAIL,
            message=(
                "Required columns are missing: "
                + ", ".join(missing)
            ),
            observed_value=sorted(actual),
            expected_value=sorted(expected),
        )

    return ValidationResult(
        check_name="required_columns",
        status=CheckStatus.PASS,
        message="All required columns are present.",
        observed_value=len(actual),
        expected_value=len(expected),
    )


def check_non_empty(
    dataframe: pd.DataFrame,
) -> ValidationResult:
    """Check that the dataset contains records."""

    row_count = len(dataframe)

    if row_count == 0:
        return ValidationResult(
            check_name="non_empty",
            status=CheckStatus.FAIL,
            message="Dataset contains no records.",
            observed_value=0,
            expected_value="> 0",
        )

    return ValidationResult(
        check_name="non_empty",
        status=CheckStatus.PASS,
        message="Dataset contains records.",
        observed_value=row_count,
        expected_value="> 0",
    )


def check_business_key_nulls(
    dataframe: pd.DataFrame,
    business_key: Iterable[str],
) -> ValidationResult:
    """Check for null values in business-key columns."""

    key_columns = list(
        business_key
    )

    null_rows = dataframe[
        key_columns
    ].isna().any(axis=1)

    null_count = int(
        null_rows.sum()
    )

    if null_count:
        return ValidationResult(
            check_name="business_key_nulls",
            status=CheckStatus.FAIL,
            message=(
                f"{null_count} rows contain "
                "null business-key values."
            ),
            observed_value=null_count,
            expected_value=0,
        )

    return ValidationResult(
        check_name="business_key_nulls",
        status=CheckStatus.PASS,
        message=(
            "No null business-key values found."
        ),
        observed_value=0,
        expected_value=0,
    )


def check_duplicate_business_keys(
    dataframe: pd.DataFrame,
    business_key: Iterable[str],
) -> ValidationResult:
    """Check for duplicate business-key combinations."""

    key_columns = list(
        business_key
    )

    duplicate_count = int(
        dataframe.duplicated(
            subset=key_columns,
            keep=False,
        ).sum()
    )

    if duplicate_count:
        return ValidationResult(
            check_name="duplicate_business_keys",
            status=CheckStatus.FAIL,
            message=(
                f"{duplicate_count} rows belong to "
                "duplicate business-key combinations."
            ),
            observed_value=duplicate_count,
            expected_value=0,
        )

    return ValidationResult(
        check_name="duplicate_business_keys",
        status=CheckStatus.PASS,
        message=(
            "No duplicate business keys found."
        ),
        observed_value=0,
        expected_value=0,
    )
