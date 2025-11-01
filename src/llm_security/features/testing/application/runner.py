from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Iterable, List, Sequence

from ....features.defense.application.pipeline import DefensePipeline, PipelineDecision
from ....features.defense.domain.entities import Decision, PromptBundle
from ....features.defense.domain.profile import DefenseProfile
from ....features.defense.domain.interfaces import IDefenseLayer
from ....features.models.domain.interfaces import ModelClient
from ..domain.models import PromptTest
from ..domain.results import LayerLog, TestRunResult
from .evaluator import EvaluationResult, OutputEvaluator


PipelineFactory = Callable[[DefenseProfile], DefensePipeline]


def _to_layer_logs(results: Iterable) -> List[LayerLog]:
    logs: List[LayerLog] = []
    for result in results:
        if result is None:
            continue
        logs.append(
            LayerLog(
                layer_id=result.layer_id,
                decision=result.decision.value if hasattr(result.decision, "value") else str(result.decision),
                reason=result.reason,
                metadata={k: str(v) for k, v in (result.metadata or {}).items()},
            )
        )
    return logs


class TestRunner:
    """Оркестратор прогона тестов prompt-инъекций."""

    def __init__(self, model_client: ModelClient, evaluator: OutputEvaluator, pipeline_factory: PipelineFactory):
        self._model_client = model_client
        self._evaluator = evaluator
        self._pipeline_factory = pipeline_factory

    def run_test(self, test: PromptTest, profile: DefenseProfile | None = None) -> TestRunResult:
        profile = profile or DefenseProfile(id="baseline", title="Baseline", description="No defenses", enabled_layers=[], params={})
        pipeline = self._pipeline_factory(profile)
        prompt_bundle = PromptBundle(system_prompt=test.system_prompt, user_prompt=test.user_prompt, context={"test_id": test.id})

        started_at = datetime.utcnow()
        defense_before = pipeline.guard_before(prompt_bundle)
        if defense_before.decision == Decision.BLOCK:
            finished_at = datetime.utcnow()
            evaluation = EvaluationResult(
                passed=True,
                reason=f"blocked_by:{self._collect_layer_ids(defense_before.logs)}",
                matched_criteria={"must_contain_any": True, "must_not_contain_any": True},
            )
            return TestRunResult(
                test=test,
                response="",
                evaluation=evaluation,
                started_at=started_at,
                finished_at=finished_at,
                defense_decision=defense_before.decision.value,
                defense_logs_before=_to_layer_logs(defense_before.logs),
                duration_ms=(finished_at - started_at).total_seconds() * 1000,
            )
        if defense_before.decision == Decision.ESCALATE:
            finished_at = datetime.utcnow()
            evaluation = EvaluationResult(
                passed=False,
                reason="escalated",
                matched_criteria={"must_contain_any": False, "must_not_contain_any": False},
            )
            return TestRunResult(
                test=test,
                response="",
                evaluation=evaluation,
                started_at=started_at,
                finished_at=finished_at,
                defense_decision=defense_before.decision.value,
                defense_logs_before=_to_layer_logs(defense_before.logs),
                duration_ms=(finished_at - started_at).total_seconds() * 1000,
            )

        bundle_after_pre = defense_before.payload if isinstance(defense_before.payload, PromptBundle) else prompt_bundle
        t0 = time.perf_counter()
        response = self._model_client.generate(bundle_after_pre)
        inference_ms = (time.perf_counter() - t0) * 1000

        defense_after = pipeline.guard_after(bundle_after_pre, response)
        final_response = defense_after.payload if isinstance(defense_after.payload, str) else response
        evaluation = self._evaluator.evaluate(test, final_response)
        finished_at = datetime.utcnow()
        total_ms = (finished_at - started_at).total_seconds() * 1000

        return TestRunResult(
            test=test,
            response=final_response,
            evaluation=evaluation,
            started_at=started_at,
            finished_at=finished_at,
            defense_decision=defense_after.decision.value,
            defense_logs_before=_to_layer_logs(defense_before.logs),
            defense_logs_after=_to_layer_logs(defense_after.logs),
            duration_ms=total_ms,
        )

    @staticmethod
    def _collect_layer_ids(results: Sequence) -> str:
        return ",".join(result.layer_id for result in results if getattr(result, "layer_id", None))

