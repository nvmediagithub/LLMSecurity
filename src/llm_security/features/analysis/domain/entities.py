from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from ...attacks.domain.entities import AttackResult
from ...testing.domain.results import TestRunResult


@dataclass(slots=True)
class LayerMetrics:
    """Metrics for individual defense layers."""

    layer_id: str
    blocks_count: int = 0
    rewrites_count: int = 0
    escalates_count: int = 0
    allows_count: int = 0
    false_positives: int = 0
    average_latency_ms: float = 0.0
    effectiveness_score: float = 0.0  # Percentage of attacks successfully blocked

    @property
    def total_decisions(self) -> int:
        return self.blocks_count + self.rewrites_count + self.escalates_count + self.allows_count

    @property
    def block_rate(self) -> float:
        return (self.blocks_count / self.total_decisions * 100) if self.total_decisions else 0.0


@dataclass(slots=True)
class AttackMetrics:
    """Metrics for attack patterns and categories."""

    category: str
    total_attempts: int = 0
    successful_attempts: int = 0
    blocked_attempts: int = 0
    pattern_distribution: Dict[str, int] = field(default_factory=dict)
    average_complexity: float = 0.0

    @property
    def success_rate(self) -> float:
        return (self.successful_attempts / self.total_attempts * 100) if self.total_attempts else 0.0

    @property
    def block_rate(self) -> float:
        return (self.blocked_attempts / self.total_attempts * 100) if self.total_attempts else 0.0


@dataclass(slots=True)
class AnalysisResult:
    """Comprehensive analysis result combining test and attack data."""

    timestamp: datetime
    test_results: List[TestRunResult]
    attack_results: List[AttackResult]

    # Overall metrics
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    total_attacks: int = 0
    blocked_attacks: int = 0

    # Detailed metrics
    layer_metrics: List[LayerMetrics] = field(default_factory=list)
    attack_metrics: List[AttackMetrics] = field(default_factory=list)

    # Vulnerabilities and recommendations
    vulnerabilities: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    @property
    def test_pass_rate(self) -> float:
        return (self.passed_tests / self.total_tests * 100) if self.total_tests else 0.0

    @property
    def attack_block_rate(self) -> float:
        return (self.blocked_attacks / self.total_attacks * 100) if self.total_attacks else 0.0


@dataclass(slots=True)
class UnifiedReport:
    """Unified report combining all analysis results."""

    analysis_result: AnalysisResult
    generated_at: datetime

    # Summary sections
    executive_summary: str = ""
    security_assessment: str = ""
    performance_analysis: str = ""
    recommendations: List[str] = field(default_factory=list)

    # Export formats available
    supports_csv: bool = True
    supports_json: bool = True
    supports_html: bool = True