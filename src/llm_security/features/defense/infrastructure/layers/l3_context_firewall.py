from __future__ import annotations

import re
from html import unescape

from ...domain.entities import DefenseResult, PromptBundle
from .base import BaseDefenseLayer


SCRIPT_RE = re.compile(r"<script.*?>.*?</script>", re.IGNORECASE | re.DOTALL)
HIDDEN_STYLE_RE = re.compile(r"<([^>]+)style=['\"]?[^>]*?(display\s*:\s*none|visibility\s*:\s*hidden)[^>]*>(.*?)</\1>", re.IGNORECASE | re.DOTALL)


class ContextFirewallLayer(BaseDefenseLayer):
    id = "L3"

    def __init__(self, *, strip_html: bool = True, remove_hidden_css: bool = True, allow_domains: list[str] | None = None):
        self.strip_html = strip_html
        self.remove_hidden_css = remove_hidden_css
        self.allow_domains = allow_domains or []

    def before_send(self, prompt_bundle: PromptBundle) -> DefenseResult:
        text = prompt_bundle.user_prompt
        cleaned = SCRIPT_RE.sub("", text)
        if self.remove_hidden_css and re.search(r"display\s*:\s*none|aria-hidden\s*=\s*['\"]?true", cleaned, re.IGNORECASE):
            return DefenseResult.block(self.id, reason="hidden_instruction")
        if self.strip_html:
            cleaned = self._strip_tags(cleaned)
        if cleaned != text:
            return DefenseResult.rewrite(self.id, rewritten_text=cleaned, reason="context_firewall")
        return DefenseResult.allow(self.id)

    @staticmethod
    def _strip_tags(value: str) -> str:
        no_tags = re.sub(r"<[^>]+>", " ", value)
        return unescape(re.sub(r"\s+", " ", no_tags)).strip()
