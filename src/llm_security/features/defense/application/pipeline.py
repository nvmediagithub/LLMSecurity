from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, Sequence, Tuple

from ..domain.entities import Decision, DefenseResult, PromptBundle
from ..domain.interfaces import IDefenseLayer
# Импорт новой системы слоев для обратной совместимости
from ...layers.domain.interfaces import ILayer
from ...layers.infrastructure.defense_layer_adapter import DefenseLayerAdapter


@dataclass
class PipelineDecision:
    decision: Decision
    payload: PromptBundle | str
    logs: List[DefenseResult] = field(default_factory=list)


class DefensePipeline:
    """Оркестратор конвейера защит."""

    def __init__(self, layers: Sequence[IDefenseLayer | ILayer]):
        # Адаптируем слои нового типа к старому интерфейсу
        adapted_layers = []
        for layer in layers:
            if isinstance(layer, ILayer):
                # Если слой уже адаптирован или является новым типом
                adapted_layers.append(layer)
            else:
                # Адаптируем старый слой через адаптер
                adapted_layer = DefenseLayerAdapter.create_from_defense_layer(layer)
                adapted_layers.append(adapted_layer)

        self._layers = [layer for layer in adapted_layers if layer.enabled]

    def guard_before(self, prompt_bundle: PromptBundle) -> PipelineDecision:
        logs: List[DefenseResult] = []
        bundle = prompt_bundle
        for layer in self._layers:
            result = layer.before_send(bundle)
            logs.append(result)
            if result.decision == Decision.BLOCK:
                return PipelineDecision(Decision.BLOCK, bundle, logs)
            if result.decision == Decision.ESCALATE:
                return PipelineDecision(Decision.ESCALATE, bundle, logs)
            if result.decision == Decision.REWRITE and result.rewritten_text:
                bundle = bundle.update(user_prompt=result.rewritten_text)
        return PipelineDecision(Decision.ALLOW, bundle, logs)

    def guard_after(self, prompt_bundle: PromptBundle, response: str) -> PipelineDecision:
        logs: List[DefenseResult] = []
        output = response
        for layer in self._layers:
            result = layer.after_recv(prompt_bundle, output)
            logs.append(result)
            if result.decision == Decision.BLOCK:
                return PipelineDecision(Decision.BLOCK, "", logs)
            if result.decision == Decision.ESCALATE:
                return PipelineDecision(Decision.ESCALATE, output, logs)
            if result.decision == Decision.REWRITE and result.rewritten_text:
                output = result.rewritten_text
        return PipelineDecision(Decision.ALLOW, output, logs)

    def iter_layers(self) -> Iterable[IDefenseLayer | ILayer]:
        return iter(self._layers)

