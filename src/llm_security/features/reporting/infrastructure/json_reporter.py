from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from ...testing.domain.results import TestRunResult


def write_json(path: Path, runs: Iterable[TestRunResult]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = []
    for run in runs:
        payload.append(
            {
                "test_id": run.test.id,
                "name": run.test.name,
                "category": run.test.category,
                "severity": run.test.severity.value,
                "passed": run.passed,
                "reason": run.evaluation.reason,
                "defense_decision": run.defense_decision,
                "defense_logs_before": [log.__dict__ for log in run.defense_logs_before],
                "defense_logs_after": [log.__dict__ for log in run.defense_logs_after],
                "response": run.response,
                "started_at": run.started_at.isoformat(),
                "finished_at": run.finished_at.isoformat(),
                "duration_ms": run.duration_ms,
            }
        )
    with path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)

