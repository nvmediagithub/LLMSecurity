from __future__ import annotations

from datetime import datetime
from typing import List

from ...attacks.domain.entities import AttackResult
from ...testing.domain.results import TestRunResult
from ..domain.entities import AnalysisResult
from .metrics_calculator import MetricsCalculator


class ResultAnalyzer:
    """Analyzes test and attack results to identify vulnerabilities and patterns."""

    def __init__(self):
        self._metrics_calculator = MetricsCalculator()

    def analyze_results(
        self,
        test_results: List[TestRunResult],
        attack_results: List[AttackResult]
    ) -> AnalysisResult:
        """Analyze combined test and attack results."""

        # Calculate metrics
        layer_metrics = self._metrics_calculator.calculate_layer_metrics(test_results, attack_results)
        attack_metrics = self._metrics_calculator.calculate_attack_metrics(attack_results)
        overall_metrics = self._metrics_calculator.calculate_overall_metrics(test_results, attack_results)

        # Identify vulnerabilities
        vulnerabilities = self._identify_vulnerabilities(
            test_results, attack_results, layer_metrics, attack_metrics
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(
            layer_metrics, attack_metrics, overall_metrics
        )

        return AnalysisResult(
            timestamp=datetime.now(),
            test_results=test_results,
            attack_results=attack_results,
            total_tests=overall_metrics["total_tests"],
            passed_tests=overall_metrics["passed_tests"],
            failed_tests=overall_metrics["failed_tests"],
            total_attacks=overall_metrics["total_attacks"],
            blocked_attacks=overall_metrics["blocked_attacks"],
            layer_metrics=layer_metrics,
            attack_metrics=attack_metrics,
            vulnerabilities=vulnerabilities,
            recommendations=recommendations,
        )

    def _identify_vulnerabilities(
        self,
        test_results: List[TestRunResult],
        attack_results: List[AttackResult],
        layer_metrics: List,
        attack_metrics: List
    ) -> List[str]:
        """Identify security vulnerabilities from the results."""

        vulnerabilities = []

        # Check for high false positive rates
        for metric in layer_metrics:
            if metric.false_positives > 0:
                fp_rate = metric.false_positives / metric.total_decisions * 100 if metric.total_decisions else 0
                if fp_rate > 10:  # More than 10% false positives
                    vulnerabilities.append(
                        f"Layer {metric.layer_id}: High false positive rate ({fp_rate:.1f}%) - "
                        f"{metric.false_positives} false positives out of {metric.total_decisions} decisions"
                    )

        # Check for ineffective layers (low block rate)
        for metric in layer_metrics:
            if metric.effectiveness_score < 50:  # Less than 50% effectiveness
                vulnerabilities.append(
                    f"Layer {metric.layer_id}: Low effectiveness ({metric.effectiveness_score:.1f}%) - "
                    "Failing to block sufficient attacks"
                )

        # Check for successful attack patterns
        for metric in attack_metrics:
            if metric.success_rate > 20:  # More than 20% success rate
                vulnerabilities.append(
                    f"Attack category '{metric.category}': High success rate ({metric.success_rate:.1f}%) - "
                    f"{metric.successful_attempts} successful out of {metric.total_attempts} attempts"
                )

        # Check for high failure rates in tests
        total_tests = len(test_results)
        failed_tests = sum(1 for r in test_results if not r.passed)
        if total_tests > 0:
            failure_rate = failed_tests / total_tests * 100
            if failure_rate > 30:  # More than 30% test failures
                vulnerabilities.append(
                    f"Overall: High test failure rate ({failure_rate:.1f}%) - "
                    f"{failed_tests} failed out of {total_tests} tests"
                )

        # Check for attack bypass patterns
        successful_attacks = [r for r in attack_results if getattr(r, 'success', True)]
        if successful_attacks:
            vulnerabilities.append(
                f"Security Gap: {len(successful_attacks)} attacks successfully bypassed defenses"
            )

        return vulnerabilities

    def _generate_recommendations(
        self,
        layer_metrics: List,
        attack_metrics: List,
        overall_metrics: Dict[str, int]
    ) -> List[str]:
        """Generate recommendations based on analysis."""

        recommendations = []

        # Recommendations for high false positives
        high_fp_layers = [m for m in layer_metrics if m.false_positives > 0 and
                         m.false_positives / m.total_decisions * 100 > 5]
        if high_fp_layers:
            recommendations.append(
                "Tune detection thresholds for layers with high false positives: " +
                ", ".join(m.layer_id for m in high_fp_layers)
            )

        # Recommendations for ineffective layers
        ineffective_layers = [m for m in layer_metrics if m.effectiveness_score < 30]
        if ineffective_layers:
            recommendations.append(
                "Review and enhance layers with low effectiveness: " +
                ", ".join(m.layer_id for m in ineffective_layers)
            )

        # Recommendations for successful attack categories
        vulnerable_categories = [m for m in attack_metrics if m.success_rate > 10]
        if vulnerable_categories:
            recommendations.append(
                "Implement additional protections against successful attack categories: " +
                ", ".join(m.category for m in vulnerable_categories)
            )

        # Performance recommendations
        slow_layers = [m for m in layer_metrics if m.average_latency_ms > 100]  # > 100ms
        if slow_layers:
            recommendations.append(
                "Optimize performance for slow layers: " +
                ", ".join(f"{m.layer_id} ({m.average_latency_ms:.1f}ms)" for m in slow_layers)
            )

        # Overall security recommendations
        attack_block_rate = overall_metrics["blocked_attacks"] / overall_metrics["total_attacks"] * 100 if overall_metrics["total_attacks"] else 0
        if attack_block_rate < 80:
            recommendations.append(
                f"Overall security posture needs improvement. Current attack block rate: {attack_block_rate:.1f}%"
            )

        # Test coverage recommendations
        if overall_metrics["total_tests"] < 10:
            recommendations.append("Increase test coverage to better validate security controls")

        if not recommendations:
            recommendations.append("Security analysis complete - no critical issues identified")

        return recommendations