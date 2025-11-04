from __future__ import annotations

from collections import Counter, defaultdict
from typing import Dict, List

from ...attacks.domain.entities import AttackResult
from ...l1.domain.entities import L1AttackResult
from ...reporting.application.aggregator import MetricsAggregator
from ...testing.domain.results import TestRunResult
from ..domain.entities import AnalysisResult, AttackMetrics, LayerMetrics


class MetricsCalculator:
    """Calculates various metrics for analysis results."""

    def __init__(self):
        self._metrics_aggregator = MetricsAggregator()

    def calculate_layer_metrics(
        self,
        test_results: List[TestRunResult],
        attack_results: List[AttackResult]
    ) -> List[LayerMetrics]:
        """Calculate metrics for each defense layer."""

        layer_stats = defaultdict(lambda: {
            "blocks": 0, "rewrites": 0, "escalates": 0, "allows": 0,
            "false_positives": 0, "latencies": [], "attacks_blocked": 0
        })

        # Process test results for layer decisions and false positives
        for test_result in test_results:
            all_logs = test_result.defense_logs_before + test_result.defense_logs_after

            for log in all_logs:
                stats = layer_stats[log.layer_id]
                decision = log.decision.lower()

                if decision == "block":
                    stats["blocks"] += 1
                elif decision == "rewrite":
                    stats["rewrites"] += 1
                elif decision == "escalate":
                    stats["escalates"] += 1
                elif decision == "allow":
                    stats["allows"] += 1

                # Track latency if available in metadata
                if "latency_ms" in log.metadata:
                    try:
                        stats["latencies"].append(float(log.metadata["latency_ms"]))
                    except ValueError:
                        pass

            # Check for false positives (control tests that fail)
            if (test_result.test.metadata.get("control") == "true" and
                not test_result.passed):
                # Find which layer caused the false positive
                for log in all_logs:
                    if log.decision in {"block", "rewrite"}:
                        layer_stats[log.layer_id]["false_positives"] += 1
                        break

        # Process attack results for effectiveness
        for attack_result in attack_results:
            if hasattr(attack_result, 'layer_decisions'):
                for layer_id, decision in attack_result.layer_decisions.items():
                    decision_lower = decision.lower()
                    if decision_lower in {"block", "rewrite", "escalate"}:
                        layer_stats[layer_id]["attacks_blocked"] += 1

        # Convert to LayerMetrics objects
        metrics = []
        for layer_id, stats in layer_stats.items():
            latencies = stats["latencies"]
            avg_latency = sum(latencies) / len(latencies) if latencies else 0.0

            total_decisions = (stats["blocks"] + stats["rewrites"] +
                             stats["escalates"] + stats["allows"])

            # Calculate effectiveness score based on attack blocking
            total_attacks = len(attack_results)
            effectiveness = (stats["attacks_blocked"] / total_attacks * 100) if total_attacks else 0.0

            metrics.append(LayerMetrics(
                layer_id=layer_id,
                blocks_count=stats["blocks"],
                rewrites_count=stats["rewrites"],
                escalates_count=stats["escalates"],
                allows_count=stats["allows"],
                false_positives=stats["false_positives"],
                average_latency_ms=round(avg_latency, 2),
                effectiveness_score=round(effectiveness, 2)
            ))

        return metrics

    def calculate_attack_metrics(
        self,
        attack_results: List[AttackResult]
    ) -> List[AttackMetrics]:
        """Calculate metrics for attack categories and patterns."""

        category_stats = defaultdict(lambda: {
            "total": 0, "successful": 0, "blocked": 0,
            "patterns": Counter(), "complexities": []
        })

        for result in attack_results:
            if hasattr(result, 'attack') and hasattr(result.attack, 'category'):
                category = result.attack.category.value if hasattr(result.attack.category, 'value') else str(result.attack.category)
            else:
                # Handle L1AttackResult or other formats
                category = getattr(result, 'category', 'unknown')

            stats = category_stats[category]
            stats["total"] += 1

            # Determine if attack was successful
            if hasattr(result, 'success'):
                if result.success:
                    stats["successful"] += 1
                else:
                    stats["blocked"] += 1
            elif hasattr(result, 'blocked') and result.blocked:
                stats["blocked"] += 1
            else:
                # Assume successful if not explicitly blocked
                stats["successful"] += 1

            # Track patterns if available
            if hasattr(result, 'pattern'):
                stats["patterns"][result.pattern] += 1

            # Track complexity if available
            if hasattr(result, 'complexity'):
                stats["complexities"].append(result.complexity)

        # Convert to AttackMetrics objects
        metrics = []
        for category, stats in category_stats.items():
            complexities = stats["complexities"]
            avg_complexity = sum(complexities) / len(complexities) if complexities else 0.0

            metrics.append(AttackMetrics(
                category=category,
                total_attempts=stats["total"],
                successful_attempts=stats["successful"],
                blocked_attempts=stats["blocked"],
                pattern_distribution=dict(stats["patterns"]),
                average_complexity=round(avg_complexity, 2)
            ))

        return metrics

    def calculate_overall_metrics(
        self,
        test_results: List[TestRunResult],
        attack_results: List[AttackResult]
    ) -> Dict[str, int]:
        """Calculate overall metrics for the analysis."""

        total_tests = len(test_results)
        passed_tests = sum(1 for r in test_results if r.passed)
        failed_tests = total_tests - passed_tests

        total_attacks = len(attack_results)
        blocked_attacks = sum(1 for r in attack_results if getattr(r, 'blocked', False) or not getattr(r, 'success', True))

        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "total_attacks": total_attacks,
            "blocked_attacks": blocked_attacks,
        }