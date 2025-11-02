from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass(slots=True)
class ConnectionConfig:
    id: str
    provider: str
    description: str = ""
    model_id: Optional[str] = None
    base_url: Optional[str] = None
    timeout: Optional[int] = None
    headers: Dict[str, str] = field(default_factory=dict)
    auth: Dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class ConnectionInfo:
    id: str
    provider: str
    description: str
