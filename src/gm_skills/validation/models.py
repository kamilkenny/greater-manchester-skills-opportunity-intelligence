"""Data-quality result models for GM SkillsFlow."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class CheckStatus(StrEnum):
    """Supported data-quality check outcomes."""

    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"


@dataclass(frozen=True)
class ValidationResult:
    """Result from one data-quality check."""

    check_name: str
    status: CheckStatus
    message: str
    observed_value: object | None = None
    expected_value: object | None = None

    @property
    def passed(self) -> bool:
        """Return whether the check avoided a failure."""

        return self.status != CheckStatus.FAIL
