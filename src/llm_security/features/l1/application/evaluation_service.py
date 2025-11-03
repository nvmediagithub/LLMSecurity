from __future__ import annotations

from ..domain.entities import L1AttackResult
from ..domain.interfaces import IL1ResultEvaluator


class L1EvaluationService:
    """Сервис для оценки результатов атак L1."""

    def __init__(self, evaluator: IL1ResultEvaluator):
        self._evaluator = evaluator

    def evaluate_results(self, results: list[L1AttackResult]) -> L1EvaluationSummary:
        """Оценить список результатов атак."""
        successful_attacks = [r for r in results if self._evaluator.evaluate_result(r)]
        failed_attacks = [r for r in results if not self._evaluator.evaluate_result(r)]

        return L1EvaluationSummary(
            total_results=len(results),
            successful_attacks=len(successful_attacks),
            failed_attacks=len(failed_attacks),
            success_rate=len(successful_attacks) / len(results) if results else 0.0,
            successful_attack_ids=[r.attack.id for r in successful_attacks],
            failed_attack_ids=[r.attack.id for r in failed_attacks],
        )

    def evaluate_single_result(self, result: L1AttackResult) -> bool:
        """Оценить одиночный результат атаки."""
        return self._evaluator.evaluate_result(result)


from dataclasses import dataclass


@dataclass(slots=True)
class L1EvaluationSummary:
    """Сводка оценки результатов атак L1."""

    total_results: int
    successful_attacks: int
    failed_attacks: int
    success_rate: float
    successful_attack_ids: list[str]
    failed_attack_ids: list[str]