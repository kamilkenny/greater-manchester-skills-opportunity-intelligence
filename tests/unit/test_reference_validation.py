import pandas as pd

from gm_skills.settings import settings
from gm_skills.validation.checks import check_expected_values
from gm_skills.validation.models import CheckStatus
from gm_skills.validation.src06 import (
    validate_src06,
    validation_passed,
)


def test_expected_values_pass() -> None:
    dataframe = pd.DataFrame(
        {
            "gateway_code": [
                "MBACC01",
                "MBACC02",
            ]
        }
    )

    result = check_expected_values(
        dataframe,
        "gateway_code",
        [
            "MBACC01",
            "MBACC02",
        ],
    )

    assert result.status == CheckStatus.PASS


def test_expected_values_fail() -> None:
    dataframe = pd.DataFrame(
        {
            "gateway_code": [
                "MBACC01",
                "MBACC99",
            ]
        }
    )

    result = check_expected_values(
        dataframe,
        "gateway_code",
        [
            "MBACC01",
            "MBACC02",
        ],
    )

    assert result.status == CheckStatus.FAIL


def test_mbacc_reference_passes_contract() -> None:
    path = (
        settings.reference_dir
        / "mbacc_gateways_reference.csv"
    )

    dataframe, results = validate_src06(
        path
    )

    assert len(dataframe) == 7
    assert validation_passed(results)
