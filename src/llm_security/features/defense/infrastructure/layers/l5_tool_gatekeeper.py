from __future__ import annotations

from typing import Iterable, Optional

from ...domain.entities import DefenseResult, PromptBundle
from .base import BaseDefenseLayer


class ToolGatekeeperLayer(BaseDefenseLayer):
    id = "L5"

    def __init__(self, *, allowed_tools: Optional[Iterable[str]] = None):
        self.allowed_tools = {tool.lower() for tool in (allowed_tools or [])}

    def before_send(self, prompt_bundle: PromptBundle) -> DefenseResult:
        requested_tool = prompt_bundle.context.get("tool")
        if requested_tool and requested_tool.lower() not in self.allowed_tools:
            return DefenseResult.escalate(self.id, reason=f"tool_not_allowed:{requested_tool}")
        return DefenseResult.allow(self.id)

    def after_recv(self, prompt_bundle: PromptBundle, response_text: str) -> DefenseResult:
        if "execute_tool" in response_text.lower():
            return DefenseResult.escalate(self.id, reason="response_requests_tool")
        return DefenseResult.allow(self.id)

