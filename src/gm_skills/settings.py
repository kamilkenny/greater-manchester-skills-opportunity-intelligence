"""Application configuration for GM SkillsFlow."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]

load_dotenv(PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    """Runtime settings for the GM SkillsFlow platform."""

    environment: str
    log_level: str
    project_root: Path
    reference_dir: Path
    docs_dir: Path

    @classmethod
    def from_environment(cls) -> Settings:
        environment = os.getenv(
            "GM_SKILLS_ENV",
            "development",
        ).strip().lower()

        log_level = os.getenv(
            "GM_SKILLS_LOG_LEVEL",
            "INFO",
        ).strip().upper()

        valid_environments = {
            "development",
            "test",
            "production",
        }

        if environment not in valid_environments:
            raise ValueError(
                "GM_SKILLS_ENV must be one of: "
                "development, test, production"
            )

        return cls(
            environment=environment,
            log_level=log_level,
            project_root=PROJECT_ROOT,
            reference_dir=PROJECT_ROOT / "config" / "reference",
            docs_dir=PROJECT_ROOT / "docs",
        )


settings = Settings.from_environment()
