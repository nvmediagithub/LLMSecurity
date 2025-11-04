from __future__ import annotations

import re
from typing import Any

from ..domain.entities import AttackExecutionContext, AttackResult, AttackCategory
from ..domain.interfaces import IAttackEmulator


class HTMLInjectionEmulator(IAttackEmulator):
    """Эмулятор HTML injection атак."""

    def __init__(self, config: dict[str, Any] | None = None):
        self._config = config or {}
        self._dangerous_tags = self._config.get("dangerous_tags", [
            "script", "iframe", "object", "embed", "form", "input", "button"
        ])
        self._dangerous_attrs = self._config.get("dangerous_attrs", [
            "onload", "onerror", "onclick", "onmouseover", "javascript:"
        ])

    def emulate_attack(self, context: AttackExecutionContext) -> AttackResult:
        """Эмулировать HTML injection атаку."""
        user_prompt = context.prompt_bundle.user_prompt
        attack_payload = context.attack.payload

        # Комбинируем текст с payload
        combined_text = user_prompt + attack_payload

        # Проверяем на наличие опасных HTML элементов
        has_dangerous_html = self._contains_dangerous_html(combined_text)

        # Имитируем ответ L3 слоя (Context Firewall)
        success = has_dangerous_html  # Атака успешна если опасный HTML прошел

        layer_response = {
            "decision": "block" if not success else "allow",
            "reason": "HTML injection detected and blocked" if not success else "HTML injection allowed",
            "layer_id": context.attack.target_layer,
            "detected_tags": self._find_dangerous_tags(combined_text),
            "detected_attrs": self._find_dangerous_attrs(combined_text),
        }

        return AttackResult(
            attack=context.attack,
            success=success,
            layer_response=layer_response,
            metrics={
                "text_length": len(combined_text),
                "has_script_tags": "<script" in combined_text.lower(),
                "has_iframe_tags": "<iframe" in combined_text.lower(),
                "has_javascript_attrs": "javascript:" in combined_text.lower(),
            },
        )

    def _contains_dangerous_html(self, text: str) -> bool:
        """Проверить наличие опасных HTML элементов."""
        text_lower = text.lower()

        # Проверяем опасные теги
        for tag in self._dangerous_tags:
            if f"<{tag}" in text_lower or f"</{tag}" in text_lower:
                return True

        # Проверяем опасные атрибуты
        for attr in self._dangerous_attrs:
            if attr in text_lower:
                return True

        # Проверяем JavaScript в атрибутах
        if "javascript:" in text_lower:
            return True

        # Проверяем встроенный JavaScript
        if "<script" in text_lower and "</script>" in text_lower:
            return True

        return False

    def _find_dangerous_tags(self, text: str) -> list[str]:
        """Найти опасные теги в тексте."""
        found = []
        text_lower = text.lower()

        for tag in self._dangerous_tags:
            if f"<{tag}" in text_lower:
                found.append(tag)

        return found

    def _find_dangerous_attrs(self, text: str) -> list[str]:
        """Найти опасные атрибуты в тексте."""
        found = []
        text_lower = text.lower()

        for attr in self._dangerous_attrs:
            if attr in text_lower:
                found.append(attr)

        return found


class AdvancedHTMLInjectionEmulator(IAttackEmulator):
    """Продвинутый эмулятор HTML injection с поддержкой различных техник."""

    def __init__(self, config: dict[str, Any] | None = None):
        self._config = config or {}
        self._check_nested = self._config.get("check_nested", True)
        self._check_encoded = self._config.get("check_encoded", True)

    def emulate_attack(self, context: AttackExecutionContext) -> AttackResult:
        """Эмулировать продвинутую HTML injection атаку."""
        user_prompt = context.prompt_bundle.user_prompt
        attack_payload = context.attack.payload

        combined_text = user_prompt + attack_payload

        # Расширенная проверка
        threats = self._analyze_threats(combined_text)

        success = len(threats) > 0  # Атака успешна если есть угрозы

        layer_response = {
            "decision": "block" if not success else "allow",
            "reason": f"Advanced HTML analysis: {len(threats)} threats detected",
            "layer_id": context.attack.target_layer,
            "threats": threats,
            "severity": self._calculate_severity(threats),
        }

        return AttackResult(
            attack=context.attack,
            success=success,
            layer_response=layer_response,
            metrics={
                "threat_count": len(threats),
                "severity_score": self._calculate_severity(threats),
                "has_encoded_payload": self._has_encoded_content(combined_text),
            },
        )

    def _analyze_threats(self, text: str) -> list[dict[str, Any]]:
        """Проанализировать текст на наличие угроз."""
        threats = []

        # XSS через теги
        xss_patterns = [
            r'<script[^>]*>.*?</script>',
            r'<iframe[^>]*src\s*=\s*["\'][^"\']*["\']',
            r'<object[^>]*>.*?</object>',
            r'<embed[^>]*>.*?</embed>',
        ]

        for pattern in xss_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            for match in matches:
                threats.append({
                    "type": "xss_tag_injection",
                    "pattern": pattern,
                    "content": match[:100],  # Ограничиваем длину
                    "severity": "high",
                })

        # XSS через атрибуты
        attr_patterns = [
            r'on\w+\s*=\s*["\'][^"\']*["\']',
            r'href\s*=\s*["\']javascript:[^"\']*["\']',
            r'src\s*=\s*["\']javascript:[^"\']*["\']',
        ]

        for pattern in attr_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                threats.append({
                    "type": "xss_attribute_injection",
                    "pattern": pattern,
                    "content": match,
                    "severity": "high",
                })

        # CSS injection
        css_pattern = r'<style[^>]*>.*?</style>'
        css_matches = re.findall(css_pattern, text, re.IGNORECASE | re.DOTALL)
        for match in css_matches:
            threats.append({
                "type": "css_injection",
                "pattern": css_pattern,
                "content": match[:100],
                "severity": "medium",
            })

        return threats

    def _calculate_severity(self, threats: list[dict[str, Any]]) -> str:
        """Рассчитать общий уровень угрозы."""
        if any(t["severity"] == "high" for t in threats):
            return "high"
        elif any(t["severity"] == "medium" for t in threats):
            return "medium"
        elif threats:
            return "low"
        return "none"

    def _has_encoded_content(self, text: str) -> bool:
        """Проверить наличие закодированного контента."""
        # Проверяем на HTML entities
        if "&#" in text or "<" in text or ">" in text:
            return True

        # Проверяем на hex encoding
        if "%3C" in text or "%3E" in text:  # < >
            return True

        return False