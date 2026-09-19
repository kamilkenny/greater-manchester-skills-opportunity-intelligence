import pandas as pd

from gm_skills.validation.checks import (
    check_accepted_values,
    check_business_key_nulls,
    check_duplicate_business_keys,
    check_geography_coverage,
    check_non_empty,
    check_required_columns,
    check_special_values,
)
from gm_skills.validation.models import CheckStatus


def test_required_columns_pass() -> None:
    dataframe = pd.DataFrame(
        {
            "borough": ["Bolton"],
            "value": [10],
        }
    )

    result = check_required_columns(
        dataframe,
        ["borough", "value"],
    )

    assert result.status == CheckStatus.PASS


def test_required_columns_fail() -> None:
    dataframe = pd.DataFrame(
        {
            "borough": ["Bolton"],
        }
    )

    result = check_required_columns(
        dataframe,
        ["borough", "value"],
    )

    assert result.status == CheckStatus.FAIL


def test_non_empty_pass() -> None:
    dataframe = pd.DataFrame(
        {
            "value": [1],
        }
    )

    result = check_non_empty(
        dataframe
    )

    assert result.status == CheckStatus.PASS


def test_non_empty_fail() -> None:
    dataframe = pd.DataFrame()

    result = check_non_empty(
        dataframe
    )

    assert result.status == CheckStatus.FAIL


def test_business_key_nulls_fail() -> None:
    dataframe = pd.DataFrame(
        {
            "period": ["202526", "202526"],
            "borough": ["Bolton", None],
        }
    )

    result = check_business_key_nulls(
        dataframe,
        ["period", "borough"],
    )

    assert result.status == CheckStatus.FAIL
    assert result.observed_value == 1


def test_business_key_blank_string_fails() -> None:
    dataframe = pd.DataFrame(
        {
            "period": ["202526", "202526"],
            "borough": ["Bolton", "   "],
        }
    )

    result = check_business_key_nulls(
        dataframe,
        ["period", "borough"],
    )

    assert result.status == CheckStatus.FAIL
    assert result.observed_value == 1


def test_duplicate_business_keys_fail() -> None:
    dataframe = pd.DataFrame(
        {
            "period": [
                "202526",
                "202526",
            ],
            "borough": [
                "Bolton",
                "Bolton",
            ],
        }
    )

    result = check_duplicate_business_keys(
        dataframe,
        ["period", "borough"],
    )

    assert result.status == CheckStatus.FAIL
    assert result.observed_value == 2


def test_accepted_values_pass() -> None:
    dataframe = pd.DataFrame(
        {
            "sex": [
                "Female",
                "Male",
                "Total",
            ]
        }
    )

    result = check_accepted_values(
        dataframe,
        "sex",
        ["Female", "Male", "Total"],
    )

    assert result.status == CheckStatus.PASS


def test_accepted_values_fail() -> None:
    dataframe = pd.DataFrame(
        {
            "sex": [
                "Female",
                "Unexpected",
            ]
        }
    )

    result = check_accepted_values(
        dataframe,
        "sex",
        ["Female", "Male", "Total"],
    )

    assert result.status == CheckStatus.FAIL


def test_geography_coverage_pass() -> None:
    dataframe = pd.DataFrame(
        {
            "lad_code": [
                "E08000001",
                "E08000002",
            ]
        }
    )

    result = check_geography_coverage(
        dataframe,
        "lad_code",
        [
            "E08000001",
            "E08000002",
        ],
    )

    assert result.status == CheckStatus.PASS


def test_geography_coverage_fail() -> None:
    dataframe = pd.DataFrame(
        {
            "lad_code": [
                "E08000001",
            ]
        }
    )

    result = check_geography_coverage(
        dataframe,
        "lad_code",
        [
            "E08000001",
            "E08000002",
        ],
    )

    assert result.status == CheckStatus.FAIL


def test_special_values_pass() -> None:
    dataframe = pd.DataFrame(
        {
            "starts": [
                "10",
                "0",
                "low",
                "25",
            ]
        }
    )

    result = check_special_values(
        dataframe,
        "starts",
        ["low"],
    )

    assert result.status == CheckStatus.PASS


def test_special_values_fail() -> None:
    dataframe = pd.DataFrame(
        {
            "starts": [
                "10",
                "low",
                "suppressed",
            ]
        }
    )

    result = check_special_values(
        dataframe,
        "starts",
        ["low"],
    )

    assert result.status == CheckStatus.FAIL
