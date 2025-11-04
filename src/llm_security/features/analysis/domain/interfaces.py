from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from ...attacks.domain.entities import AttackResult
from ...testing.domain.results import TestRunResult


class IAnalysisService(ABC):
    """Unified interface for analyzing test and attack results."""

    @abstractmethod
    def analyze_results(
        self,
        test_results: List[TestRunResult],
        attack_results: List[AttackResult]
    ) -> "AnalysisResult":
        """Analyze combined test and attack results."""
        pass

    @abstractmethod
    def generate_report(self, analysis_result: "AnalysisResult") -> "UnifiedReport":
        """Generate unified report from analysis."""
        pass