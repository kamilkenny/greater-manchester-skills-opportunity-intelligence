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
    """Check for null or blank values in business-key columns."""

    key_columns = list(
        business_key
    )

    key_frame = dataframe[
        key_columns
    ]

    null_mask = key_frame.isna()

    blank_mask = key_frame.map(
        lambda value: (
            isinstance(value, str)
            and not value.strip()
        )
    )

    invalid_rows = (
        null_mask | blank_mask
    ).any(axis=1)

    invalid_count = int(
        invalid_rows.sum()
    )

    if invalid_count:
        return ValidationResult(
            check_name="business_key_nulls",
            status=CheckStatus.FAIL,
            message=(
                f"{invalid_count} rows contain "
                "null or blank business-key values."
            ),
            observed_value=invalid_count,
            expected_value=0,
        )

    return ValidationResult(
        check_name="business_key_nulls",
        status=CheckStatus.PASS,
        message=(
            "No null or blank business-key values found."
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


def check_accepted_values(
    dataframe: pd.DataFrame,
    column: str,
    accepted_values: Iterable[str],
) -> ValidationResult:
    """Check categorical values against an approved domain."""

    accepted = set(
        accepted_values
    )

    observed = {
        str(value).strip()
        for value in dataframe[
            column
        ].dropna().unique()
    }

    unexpected = sorted(
        observed - accepted
    )

    if unexpected:
        return ValidationResult(
            check_name=f"accepted_values_{column}",
            status=CheckStatus.FAIL,
            message=(
                f"Unexpected values in {column}: "
                + ", ".join(unexpected)
            ),
            observed_value=unexpected,
            expected_value=sorted(accepted),
        )

    return ValidationResult(
        check_name=f"accepted_values_{column}",
        status=CheckStatus.PASS,
        message=(
            f"All {column} values are accepted."
        ),
        observed_value=sorted(observed),
        expected_value=sorted(accepted),
    )


def check_geography_coverage(
    dataframe: pd.DataFrame,
    geography_column: str,
    expected_codes: Iterable[str],
) -> ValidationResult:
    """Check that expected geography codes are present."""

    expected = set(
        expected_codes
    )

    observed = {
        str(value).strip()
        for value in dataframe[
            geography_column
        ].dropna().unique()
    }

    missing = sorted(
        expected - observed
    )

    unexpected = sorted(
        observed - expected
    )

    if missing or unexpected:
        return ValidationResult(
            check_name="geography_coverage",
            status=CheckStatus.FAIL,
            message=(
                f"Missing geography codes: {missing}; "
                f"unexpected codes: {unexpected}"
            ),
            observed_value=sorted(observed),
            expected_value=sorted(expected),
        )

    return ValidationResult(
        check_name="geography_coverage",
        status=CheckStatus.PASS,
        message=(
            "Geography coverage matches the contract."
        ),
        observed_value=sorted(observed),
        expected_value=sorted(expected),
    )


def check_special_values(
    dataframe: pd.DataFrame,
    column: str,
    allowed_special_values: Iterable[str],
) -> ValidationResult:
    """Check non-numeric metric values against known source codes."""

    allowed = set(
        allowed_special_values
    )

    series = (
        dataframe[column]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    numeric = pd.to_numeric(
        series,
        errors="coerce",
    )

    observed_special = {
        value
        for value, numeric_value
        in zip(
            series,
            numeric,
            strict=True,
        )
        if value
        and pd.isna(numeric_value)
    }

    unexpected = sorted(
        observed_special - allowed
    )

    if unexpected:
        return ValidationResult(
            check_name=f"special_values_{column}",
            status=CheckStatus.FAIL,
            message=(
                f"Unexpected non-numeric values in {column}: "
                + ", ".join(unexpected)
            ),
            observed_value=sorted(observed_special),
            expected_value=sorted(allowed),
        )

    return ValidationResult(
        check_name=f"special_values_{column}",
        status=CheckStatus.PASS,
        message=(
            f"Special values in {column} "
            "match the source contract."
        ),
        observed_value=sorted(observed_special),
        expected_value=sorted(allowed),
    )


def check_expected_values(
    dataframe: pd.DataFrame,
    column: str,
    expected_values: Iterable[str],
) -> ValidationResult:
    """Check that a column contains exactly the expected value set."""

    expected = {
        str(value).strip()
        for value in expected_values
    }

    observed = {
        str(value).strip()
        for value in dataframe[column].dropna().unique()
    }

    missing = sorted(
        expected - observed
    )

    unexpected = sorted(
        observed - expected
    )

    if missing or unexpected:
        return ValidationResult(
            check_name=f"expected_values_{column}",
            status=CheckStatus.FAIL,
            message=(
                f"Missing values: {missing}; "
                f"unexpected values: {unexpected}"
            ),
            observed_value=sorted(observed),
            expected_value=sorted(expected),
        )

    return ValidationResult(
        check_name=f"expected_values_{column}",
        status=CheckStatus.PASS,
        message=(
            f"{column} contains exactly the expected values."
        ),
        observed_value=sorted(observed),
        expected_value=sorted(expected),
    )
