from __future__ import annotations

from typing import Callable, Dict, List

from ....core.config.loader import ConfigLoader
from ..application.pipeline import DefensePipeline
from ..domain.profile import DefenseProfile
from ..domain.policy import PolicyRules
from .layers.l1_input_sanitizer import InputSanitizerLayer
from .layers.l2_prompt_classifier import PromptClassifierLayer
from .layers.l3_context_firewall import ContextFirewallLayer
from .layers.l4_policy_engine import PolicyEngineLayer
from .layers.l5_tool_gatekeeper import ToolGatekeeperLayer
from .layers.l6_suffix_detector import AdversarialSuffixLayer
from .layers.l7_output_guard import OutputGuardLayer
from .layers.l8_memory_guard import MemoryGuardLayer
from .layers.l9_rate_scope_guard import RateScopeGuardLayer


class DefensePipelineBuilder:
    """Создаёт экземпляры защитных слоёв на основе профилей и конфигов."""

    def __init__(self, loader: ConfigLoader | None = None):
        self._loader = loader or ConfigLoader()
        self._policy_rules = PolicyRules.from_mapping(self._loader.load_policy())

    def build(self, profile: DefenseProfile) -> DefensePipeline:
        factories: Dict[str, Callable[[], object]] = {
            "L1": lambda: InputSanitizerLayer(**profile.params.get("L1", {})),
            "L2": lambda: PromptClassifierLayer(**profile.params.get("L2", {})),
            "L3": lambda: ContextFirewallLayer(**profile.params.get("L3", {})),
            "L4": lambda: PolicyEngineLayer(self._policy_rules),
            "L5": lambda: ToolGatekeeperLayer(**profile.params.get("L5", {})),
            "L6": lambda: AdversarialSuffixLayer(**profile.params.get("L6", {})),
            "L7": lambda: OutputGuardLayer(blocked_keywords=profile.params.get("L7", {}).get("categories_block", [])),
            "L8": lambda: MemoryGuardLayer(),
            "L9": lambda: RateScopeGuardLayer(**profile.params.get("L9", {})),
        }
        layers = []
        for layer_id in profile.enabled_layers:
            factory = factories.get(layer_id)
            if not factory:
                continue
            layer = factory()
            layer.enabled = True  # type: ignore[attr-defined]
            layers.append(layer)
        return DefensePipeline(layers)

