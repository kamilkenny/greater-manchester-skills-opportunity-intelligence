from gm_skills.settings import settings


def test_environment_is_supported() -> None:
    assert settings.environment in {
        "development",
        "test",
        "production",
    }


def test_reference_directory_exists() -> None:
    assert settings.reference_dir.exists()


def test_docs_directory_exists() -> None:
    assert settings.docs_dir.exists()
