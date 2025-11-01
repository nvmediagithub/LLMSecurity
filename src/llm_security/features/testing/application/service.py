from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional

from ....core.config.loader import ConfigLoader
from ...defense.application.profiles_service import ProfileRepository
from ...defense.domain.profile import DefenseProfile
from ...defense.infrastructure.factory import DefensePipelineBuilder
from ...models.domain.interfaces import ModelClient
from ...models.infrastructure.dummy import DummyModelClient
from ...reporting.application.aggregator import MetricsAggregator, MetricsSummary
from ..domain.models import PromptTest
from ..domain.results import TestRunResult
from ..infrastructure.repositories.yaml_tests_repository import PromptTestRepository
from .evaluator import OutputEvaluator
from .runner import TestRunner


@dataclass
class TestSuiteResult:
    profile: DefenseProfile
    runs: List[TestRunResult]
    metrics: MetricsSummary


@dataclass
class ABTestResult:
    baseline: TestSuiteResult
    protected: TestSuiteResult

    @property
    def delta_pass_rate(self) -> float:
        return round(self.protected.metrics.pass_rate - self.baseline.metrics.pass_rate, 2)


class TestSuiteService:
    """Высокоуровневая фасада для запуска тестов и получения метрик."""

    def __init__(
        self,
        *,
        config_loader: ConfigLoader | None = None,
        model_client: ModelClient | None = None,
    ):
        self._loader = config_loader or ConfigLoader()
        self._model_client = model_client or DummyModelClient()
        self._tests_repo = PromptTestRepository(self._loader)
        self._profiles_repo = ProfileRepository(self._loader)
        self._pipeline_builder = DefensePipelineBuilder(self._loader)
        self._evaluator = OutputEvaluator()

    def list_tests(self) -> List[PromptTest]:
        return list(self._tests_repo.tests())

    def list_profiles(self) -> List[DefenseProfile]:
        return list(self._profiles_repo.load_all().values())

    def run_suite(
        self,
        profile_id: str,
        *,
        categories: Optional[Iterable[str]] = None,
        test_ids: Optional[Iterable[str]] = None,
    ) -> TestSuiteResult:
        profile = self._profiles_repo.get(profile_id)
        pipeline_builder = self._pipeline_builder
        runner = TestRunner(
            model_client=self._model_client,
            evaluator=self._evaluator,
            pipeline_factory=lambda p: pipeline_builder.build(p),
        )

        tests = self._select_tests(categories=categories, test_ids=test_ids)
        runs = [runner.run_test(test, profile) for test in tests]
        metrics = MetricsAggregator().summarize(runs)
        return TestSuiteResult(profile=profile, runs=runs, metrics=metrics)

    def run_baseline(self, *, categories: Optional[Iterable[str]] = None) -> TestSuiteResult:
        tests = self._select_tests(categories=categories)
        baseline_profile = DefenseProfile(id="baseline", title="Baseline", description="No defenses", enabled_layers=[], params={})
        pipeline_builder = self._pipeline_builder
        runner = TestRunner(
            model_client=self._model_client,
            evaluator=self._evaluator,
            pipeline_factory=lambda p: pipeline_builder.build(p),
        )
        runs = [runner.run_test(test, baseline_profile) for test in tests]
        metrics = MetricsAggregator().summarize(runs)
        return TestSuiteResult(profile=baseline_profile, runs=runs, metrics=metrics)

    def run_ab(
        self,
        profile_id: str,
        *,
        categories: Optional[Iterable[str]] = None,
        test_ids: Optional[Iterable[str]] = None,
    ) -> ABTestResult:
        baseline = self.run_baseline(categories=categories)
        protected = self.run_suite(profile_id, categories=categories, test_ids=test_ids)
        return ABTestResult(baseline=baseline, protected=protected)

    def _select_tests(
        self,
        *,
        categories: Optional[Iterable[str]] = None,
        test_ids: Optional[Iterable[str]] = None,
    ) -> List[PromptTest]:
        tests = list(self._tests_repo.tests())
        if test_ids:
            wanted = set(test_ids)
            tests = [test for test in tests if test.id in wanted]
        if categories:
            wanted_cats = set(categories)
            tests = [test for test in tests if test.category in wanted_cats]
        return tests
