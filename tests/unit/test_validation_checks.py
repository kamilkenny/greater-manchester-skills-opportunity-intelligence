import pandas as pd

from gm_skills.validation.checks import (
    check_business_key_nulls,
    check_duplicate_business_keys,
    check_non_empty,
    check_required_columns,
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
