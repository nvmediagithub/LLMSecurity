from __future__ import annotations

import unicodedata

from ..domain.entities import L1Attack, L1AttackResult, L1LayerConfig
from ..domain.interfaces import IL1AttackEmulator


class UnicodeNormalizationAttackEmulator(IL1AttackEmulator):
    """Эмулятор атак с использованием Unicode-омографов и нормализации."""

    def __init__(self, config: L1LayerConfig):
        self._config = config

    def emulate_attack(self, attack: L1Attack, text: str) -> L1AttackResult:
        """Эмулировать атаку с Unicode нормализацией на тексте."""
        if not self._validate_attack(attack):
            return L1AttackResult(
                attack=attack,
                success=False,
                original_text=text,
                processed_text=text,
                reason="Invalid attack configuration",
                metadata={"error": "Attack must be normalization category with valid payload"}
            )

        # Применяем санитизацию если включена
        processed_text = self._apply_sanitization(text)

        # Инжектируем атаку
        attacked_text = self._inject_normalization_attack(processed_text, attack)

        # Проверяем успех атаки
        success = self._check_normalization_attack_success(attacked_text, attack)

        return L1AttackResult(
            attack=attack,
            success=success,
            original_text=text,
            processed_text=attacked_text,
            reason="Unicode normalization attack succeeded" if success else "Unicode normalization attack blocked",
            metadata={
                "normalization_applied": self._config.normalize_unicode,
                "original_chars": len(text),
                "normalized_chars": len(unicodedata.normalize("NFC", text)),
                "attack_normalized": unicodedata.normalize("NFC", attack.payload)
            }
        )

    def _validate_attack(self, attack: L1Attack) -> bool:
        """Валидировать атаку на корректность."""
        if not attack.payload:
            return False
        if attack.category.value != "normalization":
            return False
        # Проверяем, что payload содержит символы, которые меняются при нормализации
        return unicodedata.normalize("NFC", attack.payload) != unicodedata.normalize("NFD", attack.payload)

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

    def _inject_normalization_attack(self, text: str, attack: L1Attack) -> str:
        """Инжектировать normalization атаку в текст."""
        # Добавляем payload, который может быть омографом или составным символом
        return text + attack.payload

    def _check_normalization_attack_success(self, text: str, attack: L1Attack) -> bool:
        """Проверить, была ли normalization атака успешной."""
        # Атака успешна, если ожидаемый результат присутствует в тексте
        if attack.expected_result not in text:
            return False

        # Если нормализация включена, атака может быть заблокирована
        if self._config.normalize_unicode:
            # Проверяем, была ли атака нормализована (что могло изменить ее)
            original_payload_normalized = unicodedata.normalize("NFC", attack.payload)
            if original_payload_normalized in text:
                return True  # Атака прошла через нормализацию
            return False  # Атака была изменена нормализацией

        # Если нормализация отключена, атака успешна если payload присутствует
        return attack.payload in text