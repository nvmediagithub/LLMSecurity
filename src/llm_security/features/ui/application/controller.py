from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional

from ...testing.application.service import ABTestResult, TestSuiteResult, TestSuiteService
from ...testing.domain.models import PromptTest
from ...models.domain.connection import ConnectionInfo


@dataclass
class UISuiteData:
    tests: List[PromptTest]
    profiles: List[str]
    connections: List[ConnectionInfo]


class UISuiteController:
    """Связывает PyQt UI с TestSuiteService."""

    def __init__(self, service: TestSuiteService | None = None):
        self._service = service or TestSuiteService()

    def load_initial_data(self) -> UISuiteData:
        tests = self._service.list_tests()
        profiles = [profile.id for profile in self._service.list_profiles()]
        connections = self._service.list_connections()
        return UISuiteData(tests=tests, profiles=profiles, connections=connections)

    def run_suite(
        self,
        profile_id: str,
        *,
        categories: Optional[Iterable[str]] = None,
        test_ids: Optional[Iterable[str]] = None,
        connection_id: Optional[str] = None,
    ) -> TestSuiteResult:
        return self._service.run_suite(profile_id, categories=categories, test_ids=test_ids, connection_id=connection_id)

    def run_ab(
        self,
        profile_id: str,
        *,
        categories: Optional[Iterable[str]] = None,
        test_ids: Optional[Iterable[str]] = None,
        connection_id: Optional[str] = None,
    ) -> ABTestResult:
        return self._service.run_ab(profile_id, categories=categories, test_ids=test_ids, connection_id=connection_id)
