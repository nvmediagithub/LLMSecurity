from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List

from ...defense.domain.entities import DefenseResult, PromptBundle
from ...defense.application.pipeline import PipelineDecision
from .models import PromptTest, TestSeverity
from ..application.evaluator import EvaluationResult


@dataclass(slots=True)
class LayerLog:
    layer_id: str
    decision: str
    reason: str
    metadata: Dict[str, str]


@dataclass(slots=True)
class TestRunResult:
    test: PromptTest
    response: str
    evaluation: EvaluationResult
    started_at: datetime
    finished_at: datetime
    defense_logs_before: List[LayerLog] = field(default_factory=list)
    defense_logs_after: List[LayerLog] = field(default_factory=list)
    defense_decision: str = "allow"
    duration_ms: float = 0.0

    @property
    def passed(self) -> bool:
        return self.evaluation.passed

