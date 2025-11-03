from __future__ import annotations

import re
import unicodedata

from ..domain.entities import L1Attack, L1AttackResult, L1LayerConfig
from ..domain.interfaces import IL1AttackEmulator


class ZeroWidthAttackEmulator(IL1AttackEmulator):
    """Эмулятор атак с нулевыми символами (zero-width characters)."""

    def __init__(self, config: L1LayerConfig):
        self._config = config
        self._zero_width_chars = re.compile(r"[\u200b-\u200f\u202a-\u202e\u2060-\u206f]")

    def emulate_attack(self, attack: L1Attack, text: str) -> L1AttackResult:
        """Эмулировать атаку с нулевыми символами на тексте."""
        if not self._validate_attack(attack):
            return L1AttackResult(
                attack=attack,
                success=False,
                original_text=text,
                processed_text=text,
                reason="Invalid attack configuration",
                metadata={"error": "Attack payload must contain zero-width characters"}
            )

        # Применяем санитизацию если включена
        processed_text = self._apply_sanitization(text)

        # Инжектируем атаку
        attacked_text = self._inject_zero_width_attack(processed_text, attack)

        # Проверяем успех атаки
        success = self._check_zero_width_attack_success(attacked_text, attack)

        return L1AttackResult(
            attack=attack,
            success=success,
            original_text=text,
            processed_text=attacked_text,
            reason="Zero-width attack succeeded" if success else "Zero-width attack blocked",
            metadata={
                "zero_width_chars_detected": bool(self._zero_width_chars.search(attack.payload)),
                "sanitization_applied": self._config.sanitize_zero_width,
                "chars_removed": len(self._zero_width_chars.findall(attacked_text)) if not success else 0
            }
        )

    def _validate_attack(self, attack: L1Attack) -> bool:
        """Валидировать атаку на корректность."""
        if not attack.payload:
            return False
        if attack.category.value != "encoding_attack":
            return False
        # Проверяем, что payload содержит zero-width символы
        return bool(self._zero_width_chars.search(attack.payload))

    def _apply_sanitization(self, text: str) -> str:
        """Применить санитизацию согласно конфигурации."""
        cleaned = text

        if self._config.normalize_unicode:
            cleaned = unicodedata.normalize("NFC", cleaned)

        if self._config.sanitize_zero_width:
            cleaned = self._zero_width_chars.sub("", cleaned)

        if len(cleaned) > self._config.max_length:
            cleaned = cleaned[: self._config.max_length]

        return cleaned.strip()

    def _inject_zero_width_attack(self, text: str, attack: L1Attack) -> str:
        """Инжектировать zero-width символы в текст."""
        # Вставляем zero-width символы в случайные места или в конец
        # Для простоты добавляем в конец, но можно сделать более сложной
        return text + attack.payload

    def _check_zero_width_attack_success(self, text: str, attack: L1Attack) -> bool:
        """Проверить, была ли zero-width атака успешной."""
        # Атака успешна, если ожидаемый результат присутствует в тексте
        # и zero-width символы все еще там (если санитизация отключена)
        if attack.expected_result not in text:
            return False

        has_zero_width = bool(self._zero_width_chars.search(text))
        return not self._config.sanitize_zero_width or has_zero_width