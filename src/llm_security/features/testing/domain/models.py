from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class TestSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(slots=True)
class PassCriteria:
    must_contain_any: List[str] = field(default_factory=list)
    must_not_contain_any: List[str] = field(default_factory=list)

    def evaluate(self, text: str) -> bool:
        content = text.lower()
        if self.must_contain_any:
            if not any(token.lower() in content for token in self.must_contain_any):
                return False
        if self.must_not_contain_any:
            if any(token.lower() in content for token in self.must_not_contain_any):
                return False
        return True


@dataclass(slots=True)
class PromptTest:
    id: str
    category: str
    name: str
    system_prompt: str
    user_prompt: str
    pass_criteria: PassCriteria = field(default_factory=PassCriteria)
    severity: TestSeverity = TestSeverity.MEDIUM
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class TestCategory:
    id: str
    title: str
    description: str

