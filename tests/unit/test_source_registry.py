from gm_skills.ingestion.source_registry import (
    load_source_contract,
    load_source_registry,
)


EXPECTED_SOURCE_IDS = {
    "SRC01",
    "SRC02",
    "SRC03",
    "SRC04",
    "SRC05",
    "SRC06",
}


def test_registry_contains_six_core_sources() -> None:
    registry = load_source_registry()

    assert set(registry) == EXPECTED_SOURCE_IDS


def test_all_core_sources_are_enabled() -> None:
    registry = load_source_registry()

    assert all(
        source.enabled
        for source in registry.values()
    )


def test_all_contract_files_exist() -> None:
    registry = load_source_registry()

    assert all(
        source.contract_path.exists()
        for source in registry.values()
    )


def test_contract_ids_match_registry_ids() -> None:
    registry = load_source_registry()

    for source in registry.values():
        contract = load_source_contract(
            source
        )

        assert (
            contract["source_id"]
            == source.source_id
        )


def test_contracts_define_expected_columns() -> None:
    registry = load_source_registry()

    for source in registry.values():
        contract = load_source_contract(
            source
        )

        assert contract["expected_columns"]


def test_remote_sources_use_https() -> None:
    registry = load_source_registry()

    for source in registry.values():
        if source.source_type in {
            "direct_csv",
            "rest_api",
        }:
            assert source.endpoint.startswith(
                "https://"
            )
