from __future__ import annotations

import unicodedata

from ..domain.entities import L1Attack, L1AttackResult, L1LayerConfig
from ..domain.interfaces import IL1AttackEmulator


class LengthLimitAttackEmulator(IL1AttackEmulator):
    """Эмулятор атак на превышение лимита длины."""

    def __init__(self, config: L1LayerConfig):
        self._config = config

    def emulate_attack(self, attack: L1Attack, text: str) -> L1AttackResult:
        """Эмулировать атаку на превышение лимита длины."""
        if not self._validate_attack(attack):
            return L1AttackResult(
                attack=attack,
                success=False,
                original_text=text,
                processed_text=text,
                reason="Invalid attack configuration",
                metadata={"error": "Attack must be length_attack category with oversized payload"}
            )

        # Применяем санитизацию если включена
        processed_text = self._apply_sanitization(text)

        # Инжектируем атаку
        attacked_text = self._inject_length_attack(processed_text, attack)

        # Проверяем успех атаки
        success = self._check_length_attack_success(attacked_text, attack)

        return L1AttackResult(
            attack=attack,
            success=success,
            original_text=text,
            processed_text=attacked_text,
            reason="Length limit attack succeeded" if success else "Length limit attack blocked",
            metadata={
                "max_length": self._config.max_length,
                "original_length": len(text),
                "processed_length": len(processed_text),
                "attacked_length": len(attacked_text),
                "payload_length": len(attack.payload),
                "truncated": len(attacked_text) > self._config.max_length
            }
        )

    def _validate_attack(self, attack: L1Attack) -> bool:
        """Валидировать атаку на корректность."""
        if not attack.payload:
            return False
        if attack.category.value != "length_attack":
            return False
        # Проверяем, что payload превышает лимит длины
        return len(attack.payload) > self._config.max_length or len(attack.payload + "test") > self._config.max_length

    def _apply_sanitization(self, text: str) -> str:
        """Применить санитизацию согласно конфигурации."""
        import re

        cleaned = text

        if self._config.normalize_unicode:
            cleaned = unicodedata.normalize("NFC", cleaned)

        if self._config.sanitize_zero_width:
            zero_width_re = re.compile(r"[\u200b-\u200f\u202a-\u202e\u2060-\u206f]")
            cleaned = zero_width_re.sub("", cleaned)

        if len(cleaned) > self._config.max_length:
            cleaned = cleaned[: self._config.max_length]

        return cleaned.strip()

    def _inject_length_attack(self, text: str, attack: L1Attack) -> str:
        """Инжектировать length атаку в текст."""
        # Добавляем payload, который может превысить лимит
        result = text + attack.payload

        # Если результат превышает лимит, он будет урезан санитизацией
        if len(result) > self._config.max_length:
            result = result[: self._config.max_length]

        return result

    def _check_length_attack_success(self, text: str, attack: L1Attack) -> bool:
        """Проверить, была ли length атака успешной."""
        # Атака успешна, если ожидаемый результат присутствует в тексте
        # несмотря на возможное усечение
        if attack.expected_result not in text:
            return False

        # Проверяем, был ли текст усечен из-за превышения лимита
        full_text = attack.payload
        if len(full_text) <= self._config.max_length:
            return True  # Payload не превышает лимит, атака прошла

        # Если payload превышает лимит, атака успешна только если часть payload прошла
        return attack.expected_result in text