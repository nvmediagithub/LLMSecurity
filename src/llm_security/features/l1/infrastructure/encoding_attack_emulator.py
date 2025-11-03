from __future__ import annotations

import base64
import binascii
import html
import unicodedata
from typing import Optional

from ..domain.entities import L1Attack, L1AttackResult, L1LayerConfig
from ..domain.interfaces import IL1AttackEmulator


class EncodingAttackEmulator(IL1AttackEmulator):
    """Эмулятор атак с использованием различных кодировок."""

    def __init__(self, config: L1LayerConfig):
        self._config = config

    def emulate_attack(self, attack: L1Attack, text: str) -> L1AttackResult:
        """Эмулировать атаку с различными кодировками на тексте."""
        if not self._validate_attack(attack):
            return L1AttackResult(
                attack=attack,
                success=False,
                original_text=text,
                processed_text=text,
                reason="Invalid attack configuration",
                metadata={"error": "Attack must be encoding_attack category with valid encoded payload"}
            )

        # Применяем санитизацию если включена
        processed_text = self._apply_sanitization(text)

        # Инжектируем атаку
        attacked_text = self._inject_encoding_attack(processed_text, attack)

        # Проверяем успех атаки
        success = self._check_encoding_attack_success(attacked_text, attack)

        return L1AttackResult(
            attack=attack,
            success=success,
            original_text=text,
            processed_text=attacked_text,
            reason="Encoding attack succeeded" if success else "Encoding attack blocked",
            metadata={
                "encoding_type": self._detect_encoding_type(attack.payload),
                "decoded_payload": self._try_decode_payload(attack.payload),
                "sanitization_applied": True
            }
        )

    def _validate_attack(self, attack: L1Attack) -> bool:
        """Валидировать атаку на корректность."""
        if not attack.payload:
            return False
        if attack.category.value != "encoding_attack":
            return False
        # Проверяем, что payload содержит закодированный контент
        return self._detect_encoding_type(attack.payload) is not None

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

    def _inject_encoding_attack(self, text: str, attack: L1Attack) -> str:
        """Инжектировать encoding атаку в текст."""
        # Добавляем закодированный payload
        return text + attack.payload

    def _check_encoding_attack_success(self, text: str, attack: L1Attack) -> bool:
        """Проверить, была ли encoding атака успешной."""
        # Атака успешна, если ожидаемый результат присутствует в тексте
        # или если декодированный контент прошел через фильтры
        if attack.expected_result in text:
            return True

        # Проверяем, удалось ли декодировать и выполнить атаку
        decoded = self._try_decode_payload(attack.payload)
        if decoded and decoded in text:
            return True

        return False

    def _detect_encoding_type(self, payload: str) -> Optional[str]:
        """Определить тип кодировки в payload."""
        # Проверяем base64
        try:
            base64.b64decode(payload, validate=True)
            return "base64"
        except (binascii.Error, ValueError):
            pass

        # Проверяем HTML entities
        if "&" in payload and ";" in payload:
            try:
                decoded = html.unescape(payload)
                if decoded != payload:
                    return "html_entities"
            except:
                pass

        # Проверяем URL encoding
        if "%" in payload:
            try:
                from urllib.parse import unquote
                decoded = unquote(payload)
                if decoded != payload:
                    return "url_encoding"
            except:
                pass

        # Проверяем Unicode escapes
        if "\\u" in payload or "\\U" in payload:
            return "unicode_escape"

        return None

    def _try_decode_payload(self, payload: str) -> Optional[str]:
        """Попытаться декодировать payload."""
        encoding_type = self._detect_encoding_type(payload)
        if not encoding_type:
            return None

        try:
            if encoding_type == "base64":
                decoded_bytes = base64.b64decode(payload)
                return decoded_bytes.decode('utf-8', errors='ignore')
            elif encoding_type == "html_entities":
                return html.unescape(payload)
            elif encoding_type == "url_encoding":
                from urllib.parse import unquote
                return unquote(payload)
            elif encoding_type == "unicode_escape":
                return payload.encode().decode('unicode_escape')
        except:
            return None

        return None