from __future__ import annotations

from .entities import L1AttackCategory, L1LayerConfig


class L1Policy:
    """Политики для L1 слоя защиты."""

    @staticmethod
    def is_attack_allowed(config: L1LayerConfig, category: L1AttackCategory) -> bool:
        """Проверить, разрешена ли категория атаки в конфигурации."""
        return category in config.enabled_categories or not config.enabled_categories

    @staticmethod
    def validate_config(config: L1LayerConfig) -> list[str]:
        """Валидировать конфигурацию L1 слоя."""
        errors = []
        if config.max_length <= 0:
            errors.append("max_length must be positive")
        if config.max_length > 100000:
            errors.append("max_length must be less than 100000")
        return errors

    @staticmethod
    def get_default_config() -> L1LayerConfig:
        """Получить конфигурацию по умолчанию."""
        return L1LayerConfig(
            max_length=5000,
            enabled_categories=set(L1AttackCategory),
            sanitize_zero_width=True,
            normalize_unicode=True,
        )