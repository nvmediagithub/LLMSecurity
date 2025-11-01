from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass(slots=True)
class DefenseProfile:
    id: str
    title: str
    description: str
    enabled_layers: List[str] = field(default_factory=list)
    params: Dict[str, Any] = field(default_factory=dict)

