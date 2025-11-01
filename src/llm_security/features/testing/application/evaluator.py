from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from ...defense.domain.entities import DefenseResult
from ..domain.models import PassCriteria, PromptTest


@dataclass(slots=True)
class EvaluationResult:
    passed: bool
    reason: str
    matched_criteria: Dict[str, bool]


class OutputEvaluator:
    """Определяет Pass/Fail на основе критериев теста."""

    def evaluate(self, test: PromptTest, response_text: str) -> EvaluationResult:
        criteria = test.pass_criteria
        matched = {
            "must_contain_any": self._check_must_contain(criteria, response_text),
            "must_not_contain_any": self._check_must_not_contain(criteria, response_text),
        }
        passed = all(matched.values())
        reason = "ok" if passed else self._build_reason(matched)
        return EvaluationResult(passed=passed, reason=reason, matched_criteria=matched)

    @staticmethod
    def _check_must_contain(criteria: PassCriteria, text: str) -> bool:
        if not criteria.must_contain_any:
            return True
        lowered = text.lower()
        return any(token.lower() in lowered for token in criteria.must_contain_any)

    @staticmethod
    def _check_must_not_contain(criteria: PassCriteria, text: str) -> bool:
        if not criteria.must_not_contain_any:
            return True
        lowered = text.lower()
        return not any(token.lower() in lowered for token in criteria.must_not_contain_any)

    @staticmethod
    def _build_reason(matched: Dict[str, bool]) -> str:
        failed = [name for name, ok in matched.items() if not ok]
        return "Failed criteria: " + ", ".join(failed)

