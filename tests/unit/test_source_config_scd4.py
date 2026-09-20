from scripts.sync_source_config_scd4 import (
    change_action,
    config_hash,
    normalise_source,
)


def test_normalise_source() -> None:
    result = normalise_source(
        "SRC99",
        {
            "name": "Example Source",
            "type": "http",
            "endpoint": "https://example.test/data",
            "target_path": "Files/raw/example/SRC99",
            "file_format": "csv",
            "refresh_frequency": "daily",
            "enabled": True,
        },
    )

    assert result["source_id"] == "SRC99"
    assert result["source_name"] == "Example Source"
    assert result["enabled"] is True
    assert len(result["config_hash"]) == 64


def test_config_hash_is_stable() -> None:
    left = {
        "source_id": "SRC01",
        "source_name": "Example",
        "enabled": True,
    }

    right = {
        "enabled": True,
        "source_name": "Example",
        "source_id": "SRC01",
    }

    assert config_hash(left) == config_hash(right)


def test_change_action() -> None:
    assert change_action(None, "abc") == "insert"
    assert change_action("abc", "abc") == "unchanged"

    assert (
        change_action("abc", "xyz")
        == "archive_and_update"
    )
