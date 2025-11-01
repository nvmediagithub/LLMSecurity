from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional

from ...testing.application.service import ABTestResult, TestSuiteResult, TestSuiteService
from ...testing.domain.models import PromptTest


@dataclass
class UISuiteData:
    tests: List[PromptTest]
    profiles: List[str]


class UISuiteController:
    """Связывает PyQt UI с TestSuiteService."""

    def __init__(self, service: TestSuiteService | None = None):
        self._service = service or TestSuiteService()

    def load_initial_data(self) -> UISuiteData:
        tests = self._service.list_tests()
        profiles = [profile.id for profile in self._service.list_profiles()]
        return UISuiteData(tests=tests, profiles=profiles)

    def run_suite(self, profile_id: str, *, categories: Optional[Iterable[str]] = None, test_ids: Optional[Iterable[str]] = None) -> TestSuiteResult:
        return self._service.run_suite(profile_id, categories=categories, test_ids=test_ids)

    def run_ab(self, profile_id: str, *, categories: Optional[Iterable[str]] = None, test_ids: Optional[Iterable[str]] = None) -> ABTestResult:
        return self._service.run_ab(profile_id, categories=categories, test_ids=test_ids)

