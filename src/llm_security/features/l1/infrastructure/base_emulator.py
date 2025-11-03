from __future__ import annotations

import re
import unicodedata

from ..domain.entities import L1Attack, L1AttackResult, L1LayerConfig
from ..domain.interfaces import IL1AttackEmulator, IL1ResultEvaluator


class BaseL1AttackEmulator(IL1AttackEmulator):
    """Базовый эмулятор атак L1 уровня."""

    def __init__(self, config: L1LayerConfig):
        self._config = config

    def emulate_attack(self, attack: L1Attack, text: str) -> L1AttackResult:
        """Эмулировать атаку на основе типа."""
        processed_text = self._apply_sanitization(text)

        # Применяем атаку к обработанному тексту
        attacked_text = self._inject_attack(processed_text, attack)

        # Проверяем, была ли атака успешной
        success = self._check_attack_success(attacked_text, attack)

        return L1AttackResult(
            attack=attack,
            success=success,
            original_text=text,
            processed_text=attacked_text,
            reason="Attack emulated" if success else "Attack blocked",
        )

    def _apply_sanitization(self, text: str) -> str:
        """Применить санитизацию согласно конфигурации."""
        cleaned = text

        if self._config.normalize_unicode:
            cleaned = unicodedata.normalize("NFC", cleaned)

        if self._config.sanitize_zero_width:
            zero_width_re = re.compile(r"[\u200b-\u200f\u202a-\u202e\u2060-\u206f]")
            cleaned = zero_width_re.sub("", cleaned)

        if len(cleaned) > self._config.max_length:
            cleaned = cleaned[: self._config.max_length]

        return cleaned.strip()

    def _inject_attack(self, text: str, attack: L1Attack) -> str:
        """Инжектировать атаку в текст."""
        # Базовая реализация - просто добавляем payload
        return text + attack.payload

    def _check_attack_success(self, text: str, attack: L1Attack) -> bool:
        """Проверить, была ли атака успешной."""
        # Простая проверка - содержит ли текст ожидаемый результат
        return attack.expected_result in text


class BaseL1ResultEvaluator(IL1ResultEvaluator):
    """Базовый оценщик результатов атак L1."""

    def evaluate_result(self, result: L1AttackResult) -> bool:
        """Оценить результат атаки."""
        return result.success