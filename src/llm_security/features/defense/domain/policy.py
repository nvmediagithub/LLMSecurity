from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List


@dataclass(slots=True)
class PolicyRules:
    forbid_role_change: bool = True
    forbidden_roles: List[str] = field(default_factory=list)
    forbid_system_prompt_leak: bool = True
    forbid_direct_harm: List[str] = field(default_factory=list)
    allow_domains: List[str] = field(default_factory=list)
    data_marking: str = "DATA_ONLY"
    escalation_keywords: List[str] = field(default_factory=list)

    @classmethod
    def from_mapping(cls, data: dict) -> "PolicyRules":
        policy = data.get("policy", data)
        return cls(
            forbid_role_change=bool(policy.get("forbid_role_change", True)),
            forbidden_roles=list(policy.get("forbidden_roles", [])),
            forbid_system_prompt_leak=bool(policy.get("forbid_system_prompt_leak", True)),
            forbid_direct_harm=list(policy.get("forbid_direct_harm", [])),
            allow_domains=list(policy.get("allow_domains", [])),
            data_marking=str(policy.get("data_marking", "DATA_ONLY")),
            escalation_keywords=list(policy.get("escalation_keywords", [])),
        )

