from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Dict, Iterable, List

from ...testing.domain.results import TestRunResult


@dataclass(slots=True)
class MetricsSummary:
    total: int
    passed: int
    failed: int
    pass_rate: float
    by_category: Dict[str, Dict[str, int]]
    by_layer: Dict[str, int]
    false_positives: int


class MetricsAggregator:
    def summarize(self, runs: Iterable[TestRunResult]) -> MetricsSummary:
        runs = list(runs)
        total = len(runs)
        passed = sum(1 for run in runs if run.passed)
        failed = total - passed
        pass_rate = (passed / total * 100) if total else 0.0

        by_category: Dict[str, Dict[str, int]] = defaultdict(lambda: {"passed": 0, "failed": 0})
        by_layer: Counter[str] = Counter()
        false_positives = 0

        for run in runs:
            category = run.test.category
            by_category[category]["passed" if run.passed else "failed"] += 1
            logs = run.defense_logs_before + run.defense_logs_after
            for log in logs:
                if log.decision in {"block", "rewrite", "escalate"}:
                    by_layer[log.layer_id] += 1
            if run.test.metadata.get("control") == "true" and not run.passed:
                false_positives += 1

        return MetricsSummary(
            total=total,
            passed=passed,
            failed=failed,
            pass_rate=round(pass_rate, 2),
            by_category=dict(by_category),
            by_layer=dict(by_layer),
            false_positives=false_positives,
        )

