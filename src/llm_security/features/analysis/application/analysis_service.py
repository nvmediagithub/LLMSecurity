from __future__ import annotations

from typing import List

from ...attacks.domain.entities import AttackResult
from ...testing.domain.results import TestRunResult
from ..domain.entities import AnalysisResult, UnifiedReport
from ..domain.interfaces import IAnalysisService
from .result_analyzer import ResultAnalyzer
from .report_generator import ReportGenerator


class AnalysisService(IAnalysisService):
    """Unified analysis service that combines existing systems."""

    def __init__(self):
        self._result_analyzer = ResultAnalyzer()
        self._report_generator = ReportGenerator()

    def analyze_results(
        self,
        test_results: List[TestRunResult],
        attack_results: List[AttackResult]
    ) -> AnalysisResult:
        """Analyze combined test and attack results."""
        return self._result_analyzer.analyze_results(test_results, attack_results)

    def generate_report(self, analysis_result: AnalysisResult) -> UnifiedReport:
        """Generate unified report from analysis."""
        return self._report_generator.generate_report(analysis_result)