import pandas as pd

from gm_skills.validation.contract_validator import (
    _scope_dataframe,
)


def test_scope_dataframe_filters_geography() -> None:
    dataframe = pd.DataFrame(
        {
            "lad_code": [
                "E08000001",
                "E08000002",
                "E99999999",
            ],
            "value": [
                "1",
                "2",
                "3",
            ],
        }
    )

    contract = {
        "geography_key": "lad_code",
        "scope": {
            "geography_codes": [
                "E08000001",
                "E08000002",
            ]
        },
    }

    scoped = _scope_dataframe(
        dataframe,
        contract,
    )

    assert len(scoped) == 2

    assert set(
        scoped["lad_code"]
    ) == {
        "E08000001",
        "E08000002",
    }


def test_scope_dataframe_filters_geographic_level() -> None:
    dataframe = pd.DataFrame(
        {
            "lad_code": [
                "E08000001",
                "E08000001",
            ],
            "geographic_level": [
                "Local authority district",
                "Regional",
            ],
        }
    )

    contract = {
        "geography_key": "lad_code",
        "scope": {
            "geography_codes": [
                "E08000001",
            ],
            "geographic_level": (
                "Local authority district"
            ),
        },
    }

    scoped = _scope_dataframe(
        dataframe,
        contract,
    )

    assert len(scoped) == 1

    assert (
        scoped.iloc[0]["geographic_level"]
        == "Local authority district"
    )
