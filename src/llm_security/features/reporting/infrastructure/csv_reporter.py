from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable

from ...testing.domain.results import TestRunResult


def write_csv(path: Path, runs: Iterable[TestRunResult]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh, delimiter=";")
        writer.writerow(
            [
                "test_id",
                "test_name",
                "category",
                "passed",
                "reason",
                "defense_decision",
                "response",
            ]
        )
        for run in runs:
            writer.writerow(
                [
                    run.test.id,
                    run.test.name,
                    run.test.category,
                    "PASS" if run.passed else "FAIL",
                    run.evaluation.reason,
                    run.defense_decision,
                    run.response.replace("\n", " "),
                ]
            )

