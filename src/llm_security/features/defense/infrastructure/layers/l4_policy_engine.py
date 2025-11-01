from __future__ import annotations

import re
from typing import Iterable

from ...domain.entities import Decision, DefenseResult, PromptBundle
from ...domain.policy import PolicyRules
from .base import BaseDefenseLayer


ROLE_CHANGE_RE = re.compile(r"\byou (are|now) (?:an?|the)\b", re.IGNORECASE)
SYSTEM_PROMPT_RE = re.compile(r"\bsystem prompt\b", re.IGNORECASE)


class PolicyEngineLayer(BaseDefenseLayer):
    id = "L4"

    def __init__(self, rules: PolicyRules):
        self.rules = rules

    def before_send(self, prompt_bundle: PromptBundle) -> DefenseResult:
        user_text = prompt_bundle.user_prompt.lower()
        reasons: list[str] = []

        if self.rules.forbid_role_change and (ROLE_CHANGE_RE.search(user_text) or self._matches_forbidden_role(user_text)):
            reasons.append("role_change")
        if self.rules.forbid_system_prompt_leak and SYSTEM_PROMPT_RE.search(user_text):
            reasons.append("system_prompt_leak")
        if self._contains_any(user_text, self.rules.forbid_direct_harm):
            reasons.append("direct_harm")
        if self._contains_any(user_text, self.rules.escalation_keywords):
            return DefenseResult.escalate(self.id, reason="escalation_keyword")

        if reasons:
            return DefenseResult.block(self.id, reason=",".join(reasons))
        return DefenseResult.allow(self.id)

    def _matches_forbidden_role(self, text: str) -> bool:
        return any(role.lower() in text for role in self.rules.forbidden_roles)

    @staticmethod
    def _contains_any(text: str, keywords: Iterable[str]) -> bool:
        lowered = text.lower()
        return any(keyword.lower() in lowered for keyword in keywords)
