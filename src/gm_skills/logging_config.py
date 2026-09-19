"""Logging configuration for GM SkillsFlow."""

from __future__ import annotations

import logging

from gm_skills.settings import settings


def configure_logging() -> None:
    """Configure application logging."""

    logging.basicConfig(
        level=getattr(
            logging,
            settings.log_level,
            logging.INFO,
        ),
        format=(
            "%(asctime)s | "
            "%(levelname)s | "
            "%(name)s | "
            "%(message)s"
        ),
    )
